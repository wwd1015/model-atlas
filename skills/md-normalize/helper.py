"""md-normalize helper.

Deterministic scaffold. The real implementation should:

1. For each target doc_id, load:
       artifacts/extracted/{doc_id}.md         (skeleton)
       artifacts/manifests/{doc_id}.json       (equation manifest)
       artifacts/formulas/{doc_id}/*.json      (OCR outputs)
2. Replace every {{EQUATION_<id>}} token with either:
       $$\n<latex>\n$$\n<!-- formula_id: <id> | desc: <desc> -->    (display)
       $<latex>$                                                    (inline)
   Use manifest.latex_converted for OMML equations and formula JSON for image
   equations. Halt if any token lacks a replacement.
3. Normalize headings: every heading gets an explicit `{#slug}` anchor.
   Slug logic must match docx-extract so section_anchor fields stay aligned.
4. Build YAML frontmatter: doc_id, title, version, effective_date,
   model_family, source_file, section_count, formula_count, last_processed,
   knowledge_pack_version.
5. Append variable definitions under each formula when formula.variables is
   non-empty.
6. Write knowledge/docs/{doc_id}.md.

Never silently paper over missing formulas — fail loudly instead.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def normalize(doc_id: str, artifacts_dir: Path, knowledge_dir: Path) -> None:
    raise NotImplementedError("md-normalize helper not yet implemented — see SKILL.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stitch LaTeX + frontmatter into the final Markdown")
    parser.add_argument("doc_id")
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--knowledge-dir", type=Path, default=Path("knowledge"))
    args = parser.parse_args()
    normalize(args.doc_id, args.artifacts_dir, args.knowledge_dir)


if __name__ == "__main__":
    main()
