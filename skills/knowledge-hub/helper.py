"""knowledge-hub helper — validate the OKF bundle / serve the hub app."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def validate() -> int:
    from hub.engine.loader import load_corpus, validate_bundle

    problems = validate_bundle()
    corpus = load_corpus()
    print(f"Corpus: {len(corpus.docs)} concepts, {len(corpus.models)} model spaces, "
          f"channels: {', '.join(corpus.channels())}")
    for issue in corpus.issues:
        print(f"  loader warning: {issue}")
    if problems:
        print(f"\nOKF conformance problems ({len(problems)}):")
        for p in problems:
            print(f"  ✗ {p}")
        return 1
    print("OKF bundle: conformant ✓")
    return 0


def serve(port: int | None = None) -> int:
    from hub.app import app  # noqa: PLC0415

    import os
    app.run(
        debug=os.environ.get("ATLAS_DEBUG", "0") == "1",
        host=os.environ.get("ATLAS_HOST", "127.0.0.1"),
        port=port or int(os.environ.get("ATLAS_PORT", "8050")),
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Atlas hub operations")
    parser.add_argument("command", choices=["validate", "serve"])
    parser.add_argument("--port", type=int, default=None, help="port for serve (default 8050)")
    args = parser.parse_args()
    raise SystemExit(validate() if args.command == "validate" else serve(args.port))


if __name__ == "__main__":
    main()
