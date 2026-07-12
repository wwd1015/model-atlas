"""Atlas Copilot — the sidebar assistant.

Default mode is **fully offline and extractive**: retrieve the best
sections via the search engine, lift the most relevant sentences, and
compose a grounded answer where every claim links to its source anchor
(`/doc/<id>#<anchor>`). That keeps the assistant honest in a regulated
setting — it navigates you to the source rather than paraphrasing it.

Synthesis is pluggable — any backend works, but citations always come from
retrieval. Two adapters ship in-repo: the **Claude Code CLI** (headless
``claude -p``, the default whenever the CLI is installed — ideal for local
testing, no keys) and a **generic OpenAI-compatible HTTP adapter**
(`http_adapter.py`, stdlib-only, activated by ``ATLAS_LLM_BASE_URL``) so any
hosted LLM or enterprise gateway works via env config. Anything else can be
plugged in via ``ATLAS_COPILOT_ADAPTER="package.module:factory"``. Keys are
deploy-time env vars only — never repo code.
"""

from __future__ import annotations

import importlib
import os
import re
from dataclasses import dataclass, field
from typing import Protocol

from hub import config
from hub.engine.loader import Corpus
from hub.engine.recommend import Recommender
from hub.engine.search import _QUERY_STOP, Hit, SearchEngine

_WORD_RE = re.compile(r"[A-Za-z0-9_]+")


class LLMAdapter(Protocol):
    """Synthesis backend. Ships with a Claude Code CLI implementation
    (`claude_adapter.ClaudeCodeAdapter`) and a generic OpenAI-compatible one
    (`http_adapter.OpenAICompatAdapter`); anything else can be plugged in via
    ATLAS_COPILOT_ADAPTER."""

    def generate(self, question: str, passages: list[dict],
                 history: list[tuple[str, str]] | None = None) -> str: ...


@dataclass
class Citation:
    doc_id: str
    title: str
    heading: str
    anchor: str

    @property
    def url(self) -> str:
        return f"/doc/{self.doc_id}#{self.anchor}" if self.anchor else f"/doc/{self.doc_id}"

    @property
    def label(self) -> str:
        return f"{self.title} › {self.heading}" if self.heading else self.title


@dataclass
class Answer:
    text: str                                   # markdown
    citations: list[Citation] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


def load_adapter() -> LLMAdapter | None:
    """Pick the synthesis backend.

    Precedence: ATLAS_COPILOT_ADAPTER (custom "module:factory") →
    ATLAS_COPILOT env ("claude"/"api" force / "extractive"|"off" force-off) →
    auto: OpenAI-compatible API when ATLAS_LLM_BASE_URL is configured, else
    the local Claude Code CLI when installed (the testing default), else
    extractive.
    """
    spec = config.COPILOT_ADAPTER.strip()
    if spec and ":" in spec:
        mod_name, factory = spec.split(":", 1)
        try:
            module = importlib.import_module(mod_name)
            return getattr(module, factory)()
        except Exception:
            return None  # misconfigured adapter must never take the hub down

    from hub.engine import http_adapter
    from hub.engine.claude_adapter import ClaudeCodeAdapter, cli_available

    mode = os.environ.get("ATLAS_COPILOT", "auto").strip().lower()
    if mode in ("extractive", "off", "none"):
        return None
    if mode == "api":
        return http_adapter.OpenAICompatAdapter() if http_adapter.configured() else None
    if mode == "auto" and http_adapter.configured():
        return http_adapter.OpenAICompatAdapter()
    if mode in ("claude", "auto") and cli_available():
        return ClaudeCodeAdapter(cwd=str(config.ROOT))
    return None


class Copilot:
    def __init__(
        self,
        corpus: Corpus,
        search: SearchEngine,
        recommender: Recommender,
        adapter: LLMAdapter | None = None,
    ):
        self.corpus = corpus
        self.search = search
        self.recommender = recommender
        self.adapter = adapter

    # -- entry point --------------------------------------------------------

    @property
    def mode(self) -> str:
        return getattr(self.adapter, "name", "custom") if self.adapter else "offline extractive"

    def ask(self, question: str, current_doc: str | None = None,
            history: list[tuple[str, str]] | None = None) -> Answer:
        q = question.strip()
        if not q:
            return self._help()
        if re.fullmatch(r"(hi|hello|hey|help|\?)[!. ]*", q.lower()):
            return self._help()

        special = self._glossary_answer(q) or self._owner_answer(q)
        if special:
            return special

        hits = self._retrieve(q, current_doc)
        if not hits:
            return self._no_hits(q)
        return self._compose(q, hits, history or [])

    # -- intents ------------------------------------------------------------

    def _help(self) -> Answer:
        channels = ", ".join(
            f"[{config.CHANNELS[c]['label']}](/channel/{c})"
            for c in self.corpus.channels()
            if c in config.CHANNELS
        )
        models = ", ".join(f"[{m.name}]({m.url})" for m in self.corpus.models.values())
        backend = (
            f"_Answers are written by **{self.mode}**, grounded in hub "
            "content — each claim links to its source._"
            if self.adapter is not None
            else "_Running in offline extractive mode — answers quote hub content directly, "
                 "with links to the source. Install the Claude Code CLI for synthesized answers._"
        )
        text = (
            "I'm the **Atlas copilot**. Ask me anything in the knowledge base and "
            "I'll point you at the exact section.\n\n"
            f"Channels: {channels}.\n\n"
            + (f"Model spaces: {models}.\n\n" if models else "")
            + backend
        )
        return Answer(
            text=text,
            suggestions=[
                "What should I do in my first week?",
                "How do we handle NPI data?",
                "Which lessons learned involve data issues?",
            ],
        )

    def _glossary_answer(self, q: str) -> Answer | None:
        m = re.match(r"(?:what\s+is|what's|define|definition\s+of|meaning\s+of)\s+(?:an?\s+|the\s+)?(.+?)\??$",
                     q.lower())
        if not m:
            return None
        term = m.group(1).strip()
        gloss = self.corpus.glossary()
        entry = gloss.get(term)
        if not entry:  # try acronym-style exact uppercase token
            entry = next((v for k, v in gloss.items() if k == term.upper().lower()), None)
        if not entry:
            return None
        name, definition, locator = entry
        doc_id, _, anchor = locator.partition("#")
        doc = self.corpus.docs.get(doc_id)
        cite = Citation(doc_id, doc.title if doc else "Glossary", name, anchor)
        return Answer(
            text=f"**{name}** — {definition}\n\n[Open in the glossary →]({cite.url})",
            citations=[cite],
            suggestions=[f"Where is {name} used?"],
        )

    @staticmethod
    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[-_./]", " ", s.lower())).strip()

    def _model_aliases(self, model) -> set[str]:
        aliases = {self._norm(model.id), self._norm(model.name),
                   self._norm(str(model.meta.get("model_id", "")))}
        # Version-free variants: "cre pd model v2 0" → "cre pd model", "cre pd v2" → "cre pd"
        aliases |= {re.sub(r"\s+v?\d[\d ]*$", "", a).strip() for a in set(aliases)}
        # "…model"-free variants: "va hedging model" → "va hedging"
        aliases |= {a.replace(" model", "").strip() for a in set(aliases)}
        return {a for a in aliases if len(a) > 3}

    def _owner_answer(self, q: str) -> Answer | None:
        if not re.search(r"\b(who\s+owns?|owner|who\s+maintains?|whom?\s+.*contact\s+(about|for))\b", q.lower()):
            return None
        qn = self._norm(q)
        for model in self.corpus.models.values():
            if any(a in qn for a in self._model_aliases(model)):
                owner = model.meta.get("owner", "the model owner listed on the model card")
                status = model.meta.get("status", "")
                doc = self.corpus.docs.get(model.overview)
                cite = Citation(model.overview, doc.title if doc else model.name, "", "")
                text = (
                    f"**{model.name}** is owned by **{owner}**"
                    + (f" (status: {status})" if status else "")
                    + f".\n\n[Open the model card →]({model.url})"
                )
                return Answer(text=text, citations=[cite],
                              suggestions=[f"Show the monitoring plan for {model.name}"])
        return None

    def _no_hits(self, q: str) -> Answer:
        return Answer(
            text=(
                f"I couldn't find anything in Atlas for “{q}”. "
                "Try different terms, or browse by channel — "
                + ", ".join(f"[{meta['label']}](/channel/{c})" for c, meta in config.CHANNELS.items())
                + "."
            ),
            suggestions=["What channels exist?", "What's in the tooling catalog?"],
        )

    # -- retrieval & composition --------------------------------------------

    def _retrieve(self, q: str, current_doc: str | None) -> list[Hit]:
        hits = self.search.search(q, limit=10)
        # Confidence gate: a grounded answer must actually cover the question.
        # Weak OR-fallback matches are fine on the search page, but the copilot
        # composing prose from them would be confidently wrong — degrade to
        # "no answer" instead.
        content_toks = [t for t in _WORD_RE.findall(q.lower()) if t not in _QUERY_STOP]
        if content_toks:
            hits = [h for h in hits if self._coverage(h, content_toks) >= 0.5]
        if current_doc:
            # Gentle boost for the page the user is reading — enough to break
            # ties, not enough to displace a clearly better source elsewhere.
            hits.sort(key=lambda h: -(h.score * (1.15 if h.doc_id == current_doc else 1.0)))
        return hits

    def _coverage(self, hit: Hit, toks: list[str]) -> float:
        hay = f"{hit.title} {hit.heading} {self._section_text(hit)}".lower()
        # Prefix match approximates stemming: "handle" hits "handling".
        matched = sum(1 for t in toks if (t[:4] if len(t) > 4 else t) in hay)
        return matched / len(toks)

    def _compose(self, q: str, hits: list[Hit], history: list[tuple[str, str]]) -> Answer:
        # Best section per doc, max three docs.
        picked: list[Hit] = []
        seen_docs: set[str] = set()
        for h in hits:
            if h.doc_id not in seen_docs:
                picked.append(h)
                seen_docs.add(h.doc_id)
            if len(picked) == 3:
                break

        citations = [Citation(h.doc_id, h.title, h.heading, h.anchor) for h in picked]

        if self.adapter is not None:
            # Give the LLM more context than the extractive path uses: up to
            # five sections (the three picked docs may contribute several).
            passages = [
                {"doc_id": h.doc_id, "title": h.title, "heading": h.heading,
                 "url": h.url, "text": self._section_text(h)}
                for h in hits[:5]
            ]
            try:
                text = self.adapter.generate(q, passages, history)
                return Answer(text=text, citations=citations,
                              suggestions=self._suggestions(picked))
            except Exception:
                pass  # fall back to extractive composition

        bullets = []
        for h, cite in zip(picked, citations):
            excerpt = self._best_sentences(self._section_text(h), q)
            bullets.append(f"- **[{cite.label}]({cite.url})** — {excerpt}")
        lead = "Here's what Atlas has on that:"
        tail = "\n\n_Answers are extracted from hub content — follow the links for full context._"
        return Answer(text=lead + "\n\n" + "\n".join(bullets) + tail,
                      citations=citations, suggestions=self._suggestions(picked))

    def _section_text(self, hit: Hit) -> str:
        doc = self.corpus.docs.get(hit.doc_id)
        if doc:
            for sec in doc.sections:
                if sec.anchor == hit.anchor:
                    return sec.text
        return hit.snippet

    @staticmethod
    def _best_sentences(text: str, q: str, max_chars: int = 320) -> str:
        toks = {t.lower() for t in _WORD_RE.findall(q)}
        # Drop table rows — they don't read as prose in an excerpt.
        text = "\n".join(ln for ln in text.splitlines() if "|" not in ln)
        # Strip markdown block furniture so the excerpt reads inline.
        flat = re.sub(r"^[>#\-\*\d\.\s]+", "", text, flags=re.MULTILINE)
        flat = flat.replace("*", "").replace("`", "")
        flat = re.sub(r"\s+", " ", flat).strip()
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", flat) if s]
        ranked = sorted(
            range(len(sentences)),
            key=lambda i: -len(toks & {t.lower() for t in _WORD_RE.findall(sentences[i])}),
        )
        chosen: list[int] = []
        total = 0
        for i in ranked[:3]:
            if total + len(sentences[i]) > max_chars:
                break
            chosen.append(i)
            total += len(sentences[i])
        # Present selected sentences in their original order — reads naturally.
        out = " ".join(sentences[i] for i in sorted(chosen))
        return out or flat[:max_chars]

    def _suggestions(self, picked: list[Hit]) -> list[str]:
        sugg: list[str] = []
        for h in picked[:1]:
            for rel_id, _ in self.recommender.related(h.doc_id, k=2):
                rel = self.corpus.docs.get(rel_id)
                if rel:
                    sugg.append(f"Tell me about {rel.title}")
        model = self.corpus.model_for_doc(picked[0].doc_id) if picked else None
        if model:
            sugg.append(f"Who owns {model.name}?")
        return sugg[:3]
