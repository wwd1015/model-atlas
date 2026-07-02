"""code-ingest prepare-phase helper.

Deterministic. Walks a repository, builds a language/LOC inventory, and
shortlists the files Claude Code should actually read during the execute
phase. No LLM work happens here.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    "env", ".tox", "dist", "build", ".next", ".cache", "target", ".idea",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "artifacts",
}
LANG_BY_EXT = {
    ".py": "Python", ".r": "R", ".sql": "SQL", ".js": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".jsx": "JavaScript",
    ".sh": "Shell", ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
    ".md": "Markdown", ".ipynb": "Notebook", ".sas": "SAS", ".jl": "Julia",
    ".scala": "Scala", ".java": "Java", ".css": "CSS", ".html": "HTML",
}
MANIFESTS = {
    "pyproject.toml", "requirements.txt", "setup.py", "package.json",
    "renv.lock", "DESCRIPTION", "environment.yml", "Makefile", "Dockerfile",
}
ENTRY_HINTS = re.compile(r"(^|/)(app|main|cli|run|server|index)\.(py|js|ts|r)$", re.IGNORECASE)


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower())
    return text.strip("-")


def inventory(repo: Path) -> dict:
    loc: dict[str, int] = {}
    files: list[tuple[str, int]] = []
    readmes, manifests, entries = [], [], []
    for path in repo.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        rel = str(path.relative_to(repo))
        lang = LANG_BY_EXT.get(path.suffix.lower())
        try:
            n_lines = sum(1 for _ in path.open("rb"))
        except OSError:
            continue
        if lang:
            loc[lang] = loc.get(lang, 0) + n_lines
            files.append((rel, n_lines))
        if path.name.lower().startswith("readme"):
            readmes.append(rel)
        if path.name in MANIFESTS:
            manifests.append(rel)
        if ENTRY_HINTS.search(rel):
            entries.append(rel)

    code_files = [
        (f, n) for f, n in files
        if LANG_BY_EXT.get(Path(f).suffix.lower()) not in ("Markdown", "YAML", "TOML", None)
    ]
    largest = [f for f, _ in sorted(code_files, key=lambda x: -x[1])[:8]]
    key_files = list(dict.fromkeys(readmes + manifests + entries + largest))
    return {
        "root": str(repo),
        "languages": sorted(loc, key=loc.get, reverse=True),
        "loc_by_language": dict(sorted(loc.items(), key=lambda x: -x[1])),
        "file_count": len(files),
        "readmes": readmes,
        "dependency_manifests": manifests,
        "entry_points": entries,
        "key_files": key_files[:20],
    }


def prepare(repo: Path, name: str, artifacts_dir: Path, content_dir: Path,
            template_path: Path, channel: str) -> None:
    artifacts_code = artifacts_dir / "code"
    artifacts_code.mkdir(parents=True, exist_ok=True)

    slug = slugify(name)
    inv = {"name": name, **inventory(repo)}
    inv_path = artifacts_code / f"{slug}_inventory.json"
    inv_path.write_text(json.dumps(inv, indent=2), encoding="utf-8")

    entries = [
        {
            "slug": slug,
            "title": name,
            "inventory_path": str(inv_path),
            "source_path": str(repo),
            "channel": channel,
            "output_path": str(content_dir / channel / f"{slug}.md"),
        }
    ]
    worklist_path = artifacts_dir / "code_worklist.json"
    worklist_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    runbook = template_path.read_text(encoding="utf-8")
    runbook = (
        runbook.replace("{{worklist_path}}", str(worklist_path))
        .replace("{{total_count}}", str(len(entries)))
        .replace("{{channel}}", channel)
    )
    runbook_path = artifacts_dir / "code_runbook.md"
    runbook_path.write_text(runbook, encoding="utf-8")

    top = ", ".join(f"{k} ({v} loc)" for k, v in list(inv["loc_by_language"].items())[:3])
    print(f"Inventory: {inv['file_count']} files — {top}")
    print(f"Key files shortlisted: {len(inv['key_files'])}")
    print(f"Runbook: {runbook_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare the code ingest runbook")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--name", default=None, help="Display name (default: repo dir name)")
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--content-dir", type=Path, default=Path("content"))
    parser.add_argument("--channel", default="tooling")
    parser.add_argument(
        "--template", type=Path,
        default=Path("skills/code-ingest/runbook_template.md"),
    )
    args = parser.parse_args()
    repo = args.repo.resolve()
    if not repo.is_dir():
        raise SystemExit(f"Not a directory: {repo}")
    prepare(repo, args.name or repo.name, args.artifacts_dir, args.content_dir,
            args.template, args.channel)


if __name__ == "__main__":
    main()
