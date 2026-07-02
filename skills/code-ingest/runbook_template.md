# Code ingest runbook

prompt_version: 1.0
Work list: `{{worklist_path}}` ({{total_count}} repos, target channel: `{{channel}}`)

You (Claude Code) are the executor. Process each worklist entry as follows.

## Per-entry procedure

1. **Resumability check.** If `output_path` already exists and starts with `---` frontmatter containing a `type:` field, skip and log as skipped.
2. **Read the inventory** at `inventory_path`, then read the shortlisted `key_files` in this order: READMEs → dependency manifests → entry points → largest source files. Stop reading once you can answer the template's questions confidently.
3. **Secrets/NPI gate.** If you encounter credentials, tokens, or customer data fixtures, STOP for that entry and flag it to the user — that's a finding for the repo owner, not hub content.
4. **Write the OKF concept** to `output_path`:

```markdown
---
type: Tool
title: <display name>
description: <one sentence — what the tool does and who uses it>
tags: [tooling, <language>, <2-3 topical tags>]
timestamp: <today, YYYY-MM-DD>
resource: <source_path or repo URL if known>
owner: <from README/manifest if stated, else omit>
prompt_version: "1.0"
---

# <title>

## What it does

<2-4 sentences, plain language, for someone deciding whether this tool solves their problem.>

## How to run it

<install + invoke, as fenced commands. If reconstructed from code rather than
documented, say so explicitly: "inferred from argparse — verify".>

## Architecture

<one short paragraph or bullet list: main modules and how data flows. Name
actual files (e.g. `hub/engine/search.py`) so readers can jump in.>

## Key entry points

<bulleted file list with one-line purpose each>

## Gotchas

<sharp edges found while reading: env assumptions, hardcoded paths, version
pins, surprising defaults. Omit if none.>
```

5. **Ground everything in the code you read.** No aspirational features; if the README claims something the code contradicts, note the discrepancy.
6. **Cross-link** related hub concepts with `[[wiki-link]]` syntax.

## After the batch

- Report: processed / skipped / flagged, plus anything unverifiable.
- Remind the user to restart the hub and commit `content/` changes.
