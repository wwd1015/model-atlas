"""structured-extract prepare-phase helper.

Deterministic. Does NOT read doc bodies or call an LLM — that is Claude Code's
job during the execute phase.

This script should:

1. Validate --type against {metrics, assumptions, data, governance, dependencies}.
2. List target docs (knowledge/docs/*.md, optionally filtered).
3. Emit artifacts/structured_worklist.{type}.json with entries:
       doc_id, doc_path, schema_path, prompt_path, output_path
4. Render skills/structured-extract/runbook_template.md into
   artifacts/structured_runbook.{type}.md, substituting {{index_type}},
   {{worklist_path}}, {{prompt_path}}, {{schema_path}}, {{total_count}}.

Do NOT wipe outputs for other index_types. This is additive per type.
"""

from __future__ import annotations

import argparse
from pathlib import Path

INDEX_TYPES = {"metrics", "assumptions", "data", "governance", "dependencies"}


def prepare(index_type: str, knowledge_dir: Path, artifacts_dir: Path, skills_dir: Path, schemas_dir: Path) -> None:
    if index_type not in INDEX_TYPES:
        raise ValueError(f"unknown index_type={index_type}; must be one of {sorted(INDEX_TYPES)}")
    raise NotImplementedError("structured-extract prepare_worklist not yet implemented — see SKILL.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a structured-extract runbook for a given index type")
    parser.add_argument("--type", dest="index_type", required=True, choices=sorted(INDEX_TYPES))
    parser.add_argument("--knowledge-dir", type=Path, default=Path("knowledge"))
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--skills-dir", type=Path, default=Path("skills"))
    parser.add_argument("--schemas-dir", type=Path, default=Path("schemas"))
    args = parser.parse_args()
    prepare(args.index_type, args.knowledge_dir, args.artifacts_dir, args.skills_dir, args.schemas_dir)


if __name__ == "__main__":
    main()
