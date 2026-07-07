"""Prepare phase for the my-runbook-skill step — deterministic only.

Contract
--------
Input:   (source files / manifests this reads)
Output:  artifacts/..._worklist.json  — one entry per unit of work, each with
         everything the execute phase needs (paths, context, output_path)
         artifacts/..._runbook.md     — rendered from runbook_template.md
Invoked: by Claude Code during the prepare phase.

No LLM work here: this script must not look at images, transcribe, or reason.
It only enumerates work and renders the runbook.
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    # parser.add_argument(...)
    parser.parse_args()
    raise NotImplementedError("flesh out per the contract above")


if __name__ == "__main__":
    main()
