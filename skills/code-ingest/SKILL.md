---
name: code-ingest
type: llm-runbook
---

# code-ingest

Turns an existing code repository or tool (a script folder, a dashboard, a package) into an OKF **Tool** concept for the Atlas tooling channel — what it does, how to run it, architecture, gotchas. Runbook pattern: the prepare phase walks the repo deterministically and builds an inventory; Claude Code executes the runbook by actually reading the key files.

## When to use

Use this skill when the user wants to:
- "Ingest this repo/tool into the hub" / "document this codebase in Atlas"
- "Prepare the code ingest runbook for ~/projects/foo" (prepare phase)
- "Execute the code runbook" (execute phase)

Do NOT use this skill when:
- The user wants full API documentation — this produces a *catalog entry* (a page, not a manual).
- The target is a document, deck, or video — use the matching ingest skill.

## Inputs

- **Prepare phase:** `--repo <path>` — the codebase to inventory (defaults to the current repo). `--name` optional display name.
- **Optional:** `--channel` (default `tooling`).

## Outputs

**Prepare phase produces:**
- `artifacts/code/{slug}_inventory.json` — `{name, root, languages, loc_by_language, key_files, entry_points, readmes, dependency_manifests, tree}`.
- `artifacts/code_worklist.json` + `artifacts/code_runbook.md`.

**Execute phase produces:**
- `content/{channel}/{slug}.md` — an OKF concept, `type: Tool`, with What it does / How to run it / Architecture / Key entry points / Gotchas, `resource:` pointing at the repo.

## Procedure

### Prepare phase

1. Run `python skills/code-ingest/prepare_worklist.py --repo <path> [--name "Display Name"]`.
2. It walks the tree (skipping `.git`, virtualenvs, `node_modules`, build dirs), counts lines by language, and shortlists the files worth reading: READMEs, dependency manifests, likely entry points, and the largest source files.
3. Report the inventory summary.

### Execute phase

1. Read `artifacts/code_runbook.md` — it is authoritative.
2. For each worklist entry: skip if `output_path` has valid frontmatter (resumability). Read the shortlisted files (READMEs and manifests first, then entry points). Write the OKF Tool concept per the runbook.
3. Report processed / skipped, and anything the code couldn't answer (e.g. "no README, run instructions inferred from argparse — verify").

## Example invocations

- "Document the bank risk dashboard repo in the hub."
- "Prepare a code ingest for ~/projects/pricing-toolkit."
- "Execute the code runbook."

## Common gotchas

- **Read the code, not just the README.** READMEs drift; `--help` strings and entry points don't.
- **State what you inferred.** If run instructions were reconstructed rather than documented, the output must say so.
- **Secrets check.** If the repo contains credentials or NPI fixtures, stop and flag — that's a finding for the repo owner, not content for the hub.
