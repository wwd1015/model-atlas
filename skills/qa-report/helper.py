"""qa-report helper.

Deterministic scaffold. The real implementation should:

1. Accept --qa-type in {formula, structured}. For structured, also accept
   --index-type.
2. For formula QA: walk artifacts/formulas/**/*.json, locate the source image
   via the manifest, render a side-by-side HTML (original image on the left,
   MathJax-rendered LaTeX on the right). Sort low confidence first, then
   medium, then high. Use Jinja2 templates.
3. For structured QA: walk artifacts/structured/*.{type}.json, confirm each
   verbatim_quote still appears in the source doc (knowledge/docs/{doc_id}.md),
   and render extracted value alongside the quote. Sort quote_mismatch=true
   first, then low, medium, high confidence.
4. Include review-budget guidance in the report header so reviewers pace
   themselves.
5. Write:
       artifacts/qa/formula_review.html
       artifacts/qa/structured_review.{index_type}.html
"""

from __future__ import annotations

import argparse
from pathlib import Path


def build(qa_type: str, index_type: str | None, artifacts_dir: Path, knowledge_dir: Path) -> None:
    raise NotImplementedError("qa-report helper not yet implemented — see SKILL.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Produce a side-by-side HTML QA report")
    parser.add_argument("--qa-type", required=True, choices=["formula", "structured"])
    parser.add_argument("--index-type", default=None, help="Required when qa-type=structured")
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--knowledge-dir", type=Path, default=Path("knowledge"))
    args = parser.parse_args()
    build(args.qa_type, args.index_type, args.artifacts_dir, args.knowledge_dir)


if __name__ == "__main__":
    main()
