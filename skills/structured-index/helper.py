"""structured-index helper.

Deterministic scaffold. The real implementation should:

1. Accept --type in {metrics, assumptions, data, governance, dependencies, all}.
2. For each type, glob artifacts/structured/*.{type}.json, validate against
   schemas/{type}.schema.json, and drop (with warning) anything invalid.
3. Flatten per-doc records into rows, carrying doc_id + model_name.
4. Write:
       knowledge/indexes/{type}_index.csv   (canonical, machine-readable)
       knowledge/indexes/{type}_index.md    (Gem-facing, with caveats)
5. The Markdown should include a "How to use" section and a caveats section
   that is partly computed (dataset / period / segment heterogeneity) and
   partly static (metric-name standardization note).
6. Truncate verbatim_quote from the Markdown table if it blows up layout,
   but always keep it in the CSV. Point readers to the per-doc JSONs for
   the full quote.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def build(index_type: str, artifacts_dir: Path, knowledge_dir: Path, schemas_dir: Path) -> None:
    raise NotImplementedError("structured-index helper not yet implemented — see SKILL.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Roll up per-doc structured JSONs into cross-doc indexes")
    parser.add_argument("--type", dest="index_type", required=True)
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--knowledge-dir", type=Path, default=Path("knowledge"))
    parser.add_argument("--schemas-dir", type=Path, default=Path("schemas"))
    args = parser.parse_args()
    build(args.index_type, args.artifacts_dir, args.knowledge_dir, args.schemas_dir)


if __name__ == "__main__":
    main()
