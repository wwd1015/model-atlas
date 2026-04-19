"""docx-extract helper.

Scaffold placeholder. The real implementation should:

1. Unzip the .docx and parse word/document.xml with lxml.
2. Find <m:oMath> elements (native OMML equations). Convert to LaTeX via
   pandoc if available; otherwise keep the raw OMML and leave
   latex_converted=null.
3. Find <w:drawing> and <w:pict> elements (image equations). Extract each
   image from word/media/ and assign a stable equation_id / image_id based
   on paragraph order.
4. Capture paragraph_index, nearest heading, and ~3 sentences of surrounding
   context for each equation. Vision OCR accuracy depends on this context.
5. Run mammoth on the body to produce HTML, then convert to Markdown,
   replacing equation elements with {{EQUATION_<id>}} tokens.
6. Emit:
       artifacts/extracted/{doc_id}.md
       artifacts/extracted/{doc_id}/images/{image_id}.{ext}
       artifacts/manifests/{doc_id}.json

The skill's SKILL.md is the authoritative spec.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def extract(docx_path: Path, artifacts_dir: Path) -> None:
    raise NotImplementedError("docx-extract helper not yet implemented — see SKILL.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a .docx whitepaper into the artifacts tree")
    parser.add_argument("docx_path", type=Path)
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    extract(args.docx_path, args.artifacts_dir)


if __name__ == "__main__":
    main()
