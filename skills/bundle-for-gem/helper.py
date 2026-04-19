"""bundle-for-gem helper.

Deterministic scaffold. The real implementation should:

1. Load skills/bundle-for-gem/grouping.yaml.
2. List knowledge/docs/*.md and assign each doc to the first bundle whose
   `match` regex matches doc_id. Flag any doc that hits the catch-all.
3. For each entry in always_include_indexes, copy the file into
   knowledge/gem_bundle/ with a numeric prefix (00_, 01_, ...).
4. For each content bundle, concatenate the member docs with:
       ---
       # DOC: <title>
       <full markdown including frontmatter>
   Prepend a bundle header and a TOC listing member docs.
5. Check per-file size (warn > 400KB, hard-limit 1MB) and total file count
   against gem_file_limit (default 10).
6. Write knowledge/gem_bundle/BUNDLE_MANIFEST.json recording what is in each
   output file.
7. Report sizes, file count, and whether within Gem limits.

Never bundle for Vertex or NotebookLM — those consume knowledge/docs/ and
knowledge/indexes/ directly.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def bundle(grouping_path: Path, knowledge_dir: Path, gem_file_limit: int = 10) -> None:
    raise NotImplementedError("bundle-for-gem helper not yet implemented — see SKILL.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Produce Gem-ready bundled files")
    parser.add_argument(
        "--grouping",
        type=Path,
        default=Path("skills/bundle-for-gem/grouping.yaml"),
    )
    parser.add_argument("--knowledge-dir", type=Path, default=Path("knowledge"))
    parser.add_argument("--gem-file-limit", type=int, default=10)
    args = parser.parse_args()
    bundle(args.grouping, args.knowledge_dir, args.gem_file_limit)


if __name__ == "__main__":
    main()
