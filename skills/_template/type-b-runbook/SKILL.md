---
name: my-runbook-skill
description: >
  One or two sentences on WHAT this skill produces "via the prepare/execute
  runbook pattern", then WHEN to use it — trigger phrases for both phases
  ("prepare the X runbook", "execute the X runbook"), prerequisites, and what
  it is NOT for. This field is what triggers the skill; spend more effort here
  than anywhere else. Max 1024 chars, no angle brackets.
type: llm-runbook
---

# my-runbook-skill

One-paragraph summary. Runbook pattern: the prepare phase is deterministic
Python that writes a worklist + runbook; the execute phase is Claude Code
reading the runbook and using its own vision/reasoning, with resumability.
No external API calls — Claude Code is the executor.

## When to use

Use this skill when the user wants to:
- "Prepare the ... runbook" (prepare phase)
- "Execute the ... runbook" (execute phase)

Do NOT use this skill when:
- Prerequisite outputs don't exist yet — name the upstream skill.

## Inputs

- **Prepare phase:** source files / doc_ids.
- **Execute phase:** the runbook written by the prepare phase.

## Outputs

**Prepare phase produces:**
- `artifacts/..._worklist.json` — one entry per unit of work.
- `artifacts/..._runbook.md` — instructions Claude Code executes next.

**Execute phase produces:**
- one output file per worklist entry (validate against `schemas/` if any).
- progress + error logs under `artifacts/`.

## Procedure

### Prepare phase

1. **Validate prerequisites.**
2. **Call `prepare_worklist.py`** to emit the worklist.
3. **Render `runbook_template.md`** and write the runbook.
4. **Report** counts and the runbook path; let the user spot-check first.

### Execute phase

1. **Read the runbook** — it is authoritative.
2. **For each worklist entry:** skip if valid output already exists
   (resumability); do the LLM work; validate; write; log progress.
3. **Report** processed / skipped / error counts and the next skill to run.

## Example invocations

- "..."

## Common gotchas

- **Don't do LLM work during the prepare phase** — it is deterministic only.
- **Don't call an external API** — Claude Code's own reasoning is the executor.
- **Respect resumability** — restarts must skip completed entries.
