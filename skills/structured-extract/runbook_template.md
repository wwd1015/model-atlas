# Structured extraction runbook — {{index_type}}

**Status:** ready for execution
**Work list:** `{{worklist_path}}`
**Prompt template:** `{{prompt_path}}`
**Output schema:** `{{schema_path}}`
**Total entries:** {{total_count}}

## Your task

For each entry in the work list, read a normalized whitepaper and extract structured records of type `{{index_type}}` using the prompt template. Validate the output against the schema, verify that every `verbatim_quote` appears literally in the source, then write the JSON file.

## Execution loop

For each entry in `{{worklist_path}}`:

1. **Check if already done.** If `entry.output_path` exists and contains valid JSON matching the schema, skip. Log to `artifacts/structured_progress.{{index_type}}.log`.

2. **Read the prompt template** at `entry.prompt_path`.

3. **Read the doc** at `entry.doc_path`. Extract `{doc_id}` and `{title}` from the YAML frontmatter.

4. **Handle length.** If the doc body exceeds ~50 pages (rough heuristic: >80,000 characters), process section-by-section: split at `## ` boundaries, run the prompt per section, then merge the `records` arrays. Do not truncate.

5. **Apply the prompt.** Substitute `{doc_id}`, `{title}`, `{full_markdown}`, and `{today}` (current date in YYYY-MM-DD). Produce JSON.

6. **Validate.**
   - Schema validation against `entry.schema_path`.
   - Verbatim-quote check: for each record, search the doc text for `record.verbatim_quote` as a substring. If not found (after whitespace normalization), flag the record with `confidence: "low"` and append `_quote_mismatch: true`.
   - If schema validation fails, retry once with a correction prompt: "Your previous output failed validation with errors: {errors}. Return corrected JSON only."

7. **Write JSON** to `entry.output_path`. Ensure parent dirs exist.

8. **Every 10 entries**, append a progress line to `artifacts/structured_progress.{{index_type}}.log`:
   `{timestamp} | processed={N} | skipped={M} | records_total={R} | quote_mismatches={Q}`

## Error handling

- **Missing doc file:** write a stub with `records: []` and `error: "doc_not_found"`. Log and continue.
- **Schema fails twice:** write the best-effort JSON plus `error: "schema_validation_failed_twice"`. Log and continue.
- **All records flagged quote_mismatch:** warn the user prominently — the prompt may be hallucinating quotes.
- **Do not halt** on individual entry failures. Log and continue; QA will catch them.

## Completion

When exhausted:

1. Append final summary to progress log.
2. Report to user:
   - docs processed
   - total records extracted
   - records per confidence tier (high/medium/low)
   - quote-mismatch count (this is the most important number — it's how you know extraction is grounded)
   - error count
3. Recommend next steps:
   - If quote-mismatch rate > 5%, the user should review the prompt or the affected docs before running `structured-index`.
   - Otherwise, proceed to `structured-index` to build the rollup.

## A note for reviewers

The `verbatim_quote` field is the audit artifact. It lets model validators confirm any extracted value against the source without re-reading the whitepaper. Preserve it faithfully, and never modify a quote post-extraction.
