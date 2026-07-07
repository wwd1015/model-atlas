# Runbook: my-runbook-skill

prompt_version: 1

> Rendered by the prepare phase into `artifacts/..._runbook.md`.
> Claude Code executes this file; it is the authoritative instruction set.

## Worklist

- Worklist: `{worklist_path}`
- Output schema: `{schema_path}`

## Instructions

For each entry in the worklist:

1. If `output_path` already contains valid output, skip it (resumability).
2. (The LLM work — describe exactly what to read, what to produce, and the
   output format. Bump `prompt_version` above on every prompt change and
   carry it into the outputs.)
3. Validate before writing; on failure retry once with a correction, then
   write a stub flagged for human QA rather than failing silently.
4. Every N entries, append a progress line to the progress log.

## On completion

Report processed / skipped / low-confidence / error counts and direct the
user to the next step in the pipeline.
