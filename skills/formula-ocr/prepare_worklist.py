"""formula-ocr prepare-phase helper.

Deterministic. Does NOT look at images — that is Claude Code's job during the
execute phase via artifacts/ocr_runbook.md.

This script should:

1. Load every manifest under artifacts/manifests/ (or the subset requested).
2. For each equation with type=="image", emit a worklist entry with:
       equation_id, doc_id, image_path, section_anchor, surrounding_context,
       display_mode, output_path (artifacts/formulas/{doc_id}/{equation_id}.json)
3. Write artifacts/ocr_worklist.json.
4. Render skills/formula-ocr/runbook_template.md into artifacts/ocr_runbook.md
   substituting {{worklist_path}}, {{schema_path}}, {{total_count}}.

The SKILL.md is the authoritative spec.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def prepare(manifests_dir: Path, artifacts_dir: Path, schema_path: Path, template_path: Path) -> None:
    raise NotImplementedError("formula-ocr prepare_worklist not yet implemented — see SKILL.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare the formula OCR runbook")
    parser.add_argument("--manifests-dir", type=Path, default=Path("artifacts/manifests"))
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--schema", type=Path, default=Path("schemas/formula.schema.json"))
    parser.add_argument(
        "--template",
        type=Path,
        default=Path("skills/formula-ocr/runbook_template.md"),
    )
    args = parser.parse_args()
    prepare(args.manifests_dir, args.artifacts_dir, args.schema, args.template)


if __name__ == "__main__":
    main()
