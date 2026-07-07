"""Deterministic helper for the my-skill step.

Contract
--------
Input:   (document the exact files/paths this reads)
Output:  (document the exact files this writes, and their schema)
Invoked: by Claude Code when `SKILL.md` is triggered — keep a CLI entrypoint
         so it can also be run standalone for debugging.

All plumbing lives here; no LLM reasoning inside a Type A step.
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    # parser.add_argument(...)
    parser.parse_args()
    raise NotImplementedError("flesh out per the contract above")


if __name__ == "__main__":
    main()
