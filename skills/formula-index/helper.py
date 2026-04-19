"""formula-index helper.

Deterministic scaffold. The real implementation should:

1. Walk artifacts/formulas/**/*.json for OCR'd image formulas.
2. Walk artifacts/manifests/*.json for OMML equations with non-null
   latex_converted. Skip is_formula: false entries.
3. Sort by (doc_id, paragraph_index). Preserve prior IDs from
   artifacts/formula_id_map.json so F-NNN numbering is stable; only assign
   new IDs to new formulas.
4. Render each entry with source, anchor, confidence, description, LaTeX,
   and variables section (only if non-empty).
5. Write knowledge/formula_index.md and artifacts/formula_id_map.json.
6. Report added/removed formulas vs prior run.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def build(artifacts_dir: Path, knowledge_dir: Path) -> None:
    raise NotImplementedError("formula-index helper not yet implemented — see SKILL.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the cross-doc formula index")
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--knowledge-dir", type=Path, default=Path("knowledge"))
    args = parser.parse_args()
    build(args.artifacts_dir, args.knowledge_dir)


if __name__ == "__main__":
    main()
