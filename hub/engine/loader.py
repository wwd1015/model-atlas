"""Load the Atlas corpus from the OKF content bundle + pipeline knowledge docs.

Two roots feed the corpus:

- ``content/`` — the hand-authored OKF bundle. Every non-reserved ``.md``
  file is a *concept*: YAML frontmatter (``type`` required) + markdown body.
  Top-level directories are the hub's channels.
- ``knowledge/docs/`` — cleaned whitepapers produced by the pipeline.
  Read-only; they are surfaced in the *models* channel and attached to a
  model space when their ``doc_id`` matches.

The loader is deliberately dependency-light: PyYAML + stdlib only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from hub import config

RESERVED_FILES = {"index.md", "log.md"}

_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]")
_HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$", re.MULTILINE)
_MD_BUNDLE_LINK_RE = re.compile(r"\]\((/[^)#\s]+\.md)(#[^)\s]*)?\)")


def slugify(text: str) -> str:
    """Kebab-case slug — same convention as the docx pipeline anchors."""
    text = re.sub(r"[*_`~]", "", text)
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower())
    return text.strip("-")


@dataclass
class Section:
    anchor: str          # kebab-case slug of the heading ("" for preamble)
    heading: str         # heading text ("" for preamble)
    level: int           # 0 for preamble, else number of '#'
    text: str            # markdown body of the section (heading line excluded)


@dataclass
class Doc:
    id: str              # bundle-relative path without extension, e.g. "onboarding/welcome"
    path: Path
    channel: str
    dtype: str           # OKF `type`
    title: str
    description: str
    tags: list[str]
    timestamp: str
    owner: str
    meta: dict           # full frontmatter, unknown keys preserved (OKF round-trip rule)
    body: str            # markdown body with wiki-links rewritten to hub routes
    sections: list[Section]
    source: str          # "content" | "knowledge"
    links_out: set[str] = field(default_factory=set)
    backlinks: set[str] = field(default_factory=set)

    @property
    def url(self) -> str:
        return f"/doc/{self.id}"


@dataclass
class Model:
    """A model space — the folder under content/models/ grouping one model's artifacts."""

    id: str              # folder slug, e.g. "cre-pd-v2"
    meta: dict           # frontmatter of model.md
    overview: str        # doc id of model.md
    artifacts: dict = field(default_factory=dict)  # role -> doc id

    @property
    def name(self) -> str:
        return self.meta.get("title", self.id)

    @property
    def url(self) -> str:
        return f"/model/{self.id}"


# filename stem -> artifact role shown as a tab on the model page
_ARTIFACT_ROLES = {
    "whitepaper": "Whitepaper",
    "user-guide": "User Guide",
    "monitoring-plan": "Monitoring Plan",
}


@dataclass
class Corpus:
    docs: dict[str, Doc]
    models: dict[str, Model]
    bundle_meta: dict
    issues: list[str]                     # OKF conformance problems found while loading

    def by_channel(self, channel: str) -> list[Doc]:
        docs = [d for d in self.docs.values() if d.channel == channel]
        return sorted(docs, key=lambda d: (d.timestamp or ""), reverse=True)

    def channels(self) -> list[str]:
        seen = list(config.CHANNELS)
        extra = sorted({d.channel for d in self.docs.values()} - set(seen))
        return [c for c in seen + extra if any(d.channel == c for d in self.docs.values())]

    def model_for_doc(self, doc_id: str) -> Model | None:
        for m in self.models.values():
            if doc_id == m.overview or doc_id in m.artifacts.values():
                return m
        return None

    def glossary(self) -> dict[str, tuple[str, str, str]]:
        """term(lower) -> (term, definition-markdown, 'doc_id#anchor')."""
        out: dict[str, tuple[str, str, str]] = {}
        for doc in self.docs.values():
            if doc.dtype.lower() != "glossary":
                continue
            for sec in doc.sections:
                if sec.level >= 2 and sec.heading and sec.text.strip():
                    definition = sec.text.strip().split("\n\n")[0]
                    out[sec.heading.lower()] = (sec.heading, definition, f"{doc.id}#{sec.anchor}")
        return out


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Split a markdown file into (frontmatter dict, body). Tolerant: returns ({}, raw) if absent."""
    m = _FRONTMATTER_RE.match(raw)
    if not m:
        return {}, raw
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}, raw
    if not isinstance(meta, dict):
        return {}, raw
    return meta, raw[m.end():]


def split_sections(body: str) -> list[Section]:
    """Split markdown into sections at headings (levels 1–4)."""
    sections: list[Section] = []
    matches = list(_HEADING_RE.finditer(body))
    preamble = body[: matches[0].start()] if matches else body
    if preamble.strip():
        sections.append(Section(anchor="", heading="", level=0, text=preamble.strip()))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        heading = m.group(2).strip()
        sections.append(
            Section(
                anchor=slugify(heading),
                heading=heading,
                level=len(m.group(1)),
                text=body[m.end(): end].strip(),
            )
        )
    if not sections:
        sections.append(Section(anchor="", heading="", level=0, text=body.strip()))
    return sections


def _load_file(path: Path, doc_id: str, channel: str, source: str, issues: list[str]) -> Doc | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:  # unreadable file — report, keep loading
        issues.append(f"{path}: unreadable ({e})")
        return None
    meta, body = parse_frontmatter(raw)
    dtype = str(meta.get("type", "") or "").strip()
    if source == "content" and not dtype:
        issues.append(f"{doc_id}: missing OKF `type` in frontmatter")
        dtype = "Note"
    if source == "knowledge" and not dtype:
        dtype = "Whitepaper"
    title = str(meta.get("title") or "").strip()
    if not title:
        m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        title = m.group(1).strip() if m else path.stem.replace("-", " ").title()
    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    return Doc(
        id=doc_id,
        path=path,
        channel=channel,
        dtype=dtype,
        title=title,
        description=str(meta.get("description", "") or ""),
        tags=[str(t) for t in tags],
        timestamp=str(meta.get("timestamp", meta.get("updated", "")) or ""),
        owner=str(meta.get("owner", "") or ""),
        meta=meta,
        body=body,
        sections=[],
        source=source,
    )


def _resolve_links(docs: dict[str, Doc], issues: list[str]) -> None:
    """Rewrite [[wiki-links]] and bundle-absolute .md links to hub routes; build the link graph."""
    by_basename: dict[str, list[str]] = {}
    for doc_id in docs:
        by_basename.setdefault(doc_id.rsplit("/", 1)[-1], []).append(doc_id)

    def resolve(target: str) -> str | None:
        target = target.strip().strip("/")
        if target in docs:
            return target
        candidates = by_basename.get(target.rsplit("/", 1)[-1], [])
        if len(candidates) == 1:
            return candidates[0]
        return None

    for doc in docs.values():

        def wiki_sub(m: re.Match) -> str:
            target, anchor, label = m.group(1), m.group(2), m.group(3)
            resolved = resolve(target)
            text = (label or target.rsplit("/", 1)[-1].replace("-", " ")).strip()
            if resolved is None:
                # OKF: broken links are tolerated — knowledge not yet written.
                return text
            doc.links_out.add(resolved)
            frag = f"#{slugify(anchor)}" if anchor else ""
            if not label:
                text = docs[resolved].title
            return f"[{text}](/doc/{resolved}{frag})"

        def mdlink_sub(m: re.Match) -> str:
            target = m.group(1).strip("/").removesuffix(".md")
            resolved = resolve(target)
            if resolved is None:
                return m.group(0)
            doc.links_out.add(resolved)
            return f"](/doc/{resolved}{m.group(2) or ''})"

        doc.body = _WIKILINK_RE.sub(wiki_sub, doc.body)
        doc.body = _MD_BUNDLE_LINK_RE.sub(mdlink_sub, doc.body)
        doc.sections = split_sections(doc.body)

    for doc in docs.values():
        for target in doc.links_out:
            if target in docs:
                docs[target].backlinks.add(doc.id)


def _build_models(docs: dict[str, Doc], issues: list[str]) -> dict[str, Model]:
    models: dict[str, Model] = {}
    for doc in docs.values():
        if doc.source == "content" and doc.id.startswith("models/") and doc.id.count("/") == 2:
            folder = doc.id.split("/")[1]
            stem = doc.id.rsplit("/", 1)[-1]
            if stem == "model":
                models.setdefault(folder, Model(id=folder, meta={}, overview=doc.id))
                models[folder].meta = doc.meta
                models[folder].overview = doc.id
    for doc in docs.values():
        if doc.source == "content" and doc.id.startswith("models/") and doc.id.count("/") == 2:
            folder = doc.id.split("/")[1]
            stem = doc.id.rsplit("/", 1)[-1]
            if folder in models and stem != "model":
                role = _ARTIFACT_ROLES.get(stem, doc.dtype or stem.replace("-", " ").title())
                models[folder].artifacts[role] = doc.id
    # Attach pipeline whitepapers: knowledge doc_id (frontmatter or filename)
    # matching the model folder slug or its declared model_id wins the Whitepaper slot.
    for doc in docs.values():
        if doc.source != "knowledge":
            continue
        key = slugify(str(doc.meta.get("doc_id", "") or doc.path.stem))
        for model in models.values():
            declared = slugify(str(model.meta.get("model_id", "") or model.id))
            if key.startswith(declared) or declared.startswith(key):
                model.artifacts["Whitepaper"] = doc.id
    return models


def load_corpus(
    content_dir: Path | None = None,
    knowledge_docs_dir: Path | None = None,
) -> Corpus:
    content_dir = content_dir or config.CONTENT_DIR
    knowledge_docs_dir = knowledge_docs_dir or config.KNOWLEDGE_DOCS_DIR
    issues: list[str] = []
    docs: dict[str, Doc] = {}
    bundle_meta: dict = {}

    if content_dir.is_dir():
        root_index = content_dir / "index.md"
        if root_index.exists():
            bundle_meta, _ = parse_frontmatter(root_index.read_text(encoding="utf-8"))
        for path in sorted(content_dir.rglob("*.md")):
            if path.name in RESERVED_FILES:
                continue
            rel = path.relative_to(content_dir)
            doc_id = str(rel.with_suffix("")).replace("\\", "/")
            channel = rel.parts[0] if len(rel.parts) > 1 else "misc"
            doc = _load_file(path, doc_id, channel, "content", issues)
            if doc:
                docs[doc.id] = doc
    else:
        issues.append(f"content bundle not found at {content_dir}")

    if knowledge_docs_dir.is_dir():
        for path in sorted(knowledge_docs_dir.glob("*.md")):
            doc_id = f"knowledge/{path.stem}"
            doc = _load_file(path, doc_id, "models", "knowledge", issues)
            if doc:
                docs[doc.id] = doc

    _resolve_links(docs, issues)
    models = _build_models(docs, issues)
    return Corpus(docs=docs, models=models, bundle_meta=bundle_meta, issues=issues)


def validate_bundle(content_dir: Path | None = None) -> list[str]:
    """OKF conformance check: parseable frontmatter + non-empty `type` everywhere."""
    content_dir = content_dir or config.CONTENT_DIR
    problems: list[str] = []
    if not content_dir.is_dir():
        return [f"bundle directory missing: {content_dir}"]
    for path in sorted(content_dir.rglob("*.md")):
        rel = path.relative_to(content_dir)
        raw = path.read_text(encoding="utf-8")
        if path.name in RESERVED_FILES:
            if path.name == "log.md" and raw.startswith("---"):
                problems.append(f"{rel}: log.md must not carry frontmatter")
            continue
        meta, _ = parse_frontmatter(raw)
        if not meta:
            problems.append(f"{rel}: missing or unparseable YAML frontmatter")
        elif not str(meta.get("type", "") or "").strip():
            problems.append(f"{rel}: missing required OKF field `type`")
    return problems
