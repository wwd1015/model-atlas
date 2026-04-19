---
name: structured-extract
type: llm-runbook
---

# structured-extract

Extracts structured records (metrics, assumptions, data coverage, governance, dependencies) from normalized per-doc Markdown using the runbook pattern. One skill handles all five index types via type-specific prompt files. No external API — Claude Code does the reasoning work.

## When to use

Use this skill when the user wants to:
- "Prepare metrics extraction for the pilot"
- "Extract assumptions across all docs"
- "Run structured extraction for governance"
- "Re-extract metrics — I updated the prompt"

Do NOT use this skill when:
- Final Markdown doesn't exist yet — this skill reads from `knowledge/docs/`, not `artifacts/extracted/`. Run `md-normalize` first.
- The user wants the cross-doc rollup table — that's `structured-index`, which runs after this.
- The user is asking a question about a single doc — don't extract, just answer from the doc directly.

## Inputs

- **Required argument:** `index_type` ∈ {`metrics`, `assumptions`, `data`, `governance`, `dependencies`}. If not provided, ask which one.
- **Targeted docs:** one or more `doc_id`s, or "all".
- `knowledge/docs/{doc_id}.md` — final normalized docs.
- `schemas/{index_type}.schema.json` — output schema.
- `skills/structured-extract/prompts/{index_type}.md` — type-specific extraction prompt.

## Outputs

**Prepare phase:**
- `artifacts/structured_worklist.{index_type}.json` — one entry per target doc.
- `artifacts/structured_runbook.{index_type}.md` — runbook for this extraction.

**Execute phase:**
- `artifacts/structured/{doc_id}.{index_type}.json` — one file per (doc, type) pair.
- `artifacts/structured_progress.{index_type}.log`
- `artifacts/structured_errors.{index_type}.log`

### Output schema example (`schemas/metrics.schema.json`)

```json
{
  "doc_id": "model_a_pd_v3",
  "index_type": "metrics",
  "records": [
    {
      "metric": "AUC",
      "value": 0.82,
      "unit": "ratio",
      "dataset": "OOT 2024",
      "segment": "Overall",
      "period": "2020-2023",
      "sample_size": 125430,
      "anchor": "model_a_pd_v3#performance",
      "verbatim_quote": "The out-of-time AUC for the overall portfolio is 0.82 over the 2020-2023 period (N=125,430).",
      "confidence": "high"
    }
  ],
  "extracted_at": "2026-04-17",
  "prompt_version": "metrics@v3"
}
```

## Procedure

### Prepare phase

1. **Validate the index_type.** Must be one of the five known types. Confirm the corresponding schema and prompt file exist.
2. **Validate inputs.** Each target doc must have a normalized `.md` in `knowledge/docs/`.
3. **Build the work list.** Call `prepare_worklist.py --type {index_type}`. It emits `artifacts/structured_worklist.{index_type}.json` with entries `{doc_id, doc_path, schema_path, prompt_path, output_path}`.
4. **Render the runbook.** Use `runbook_template.md` with `{index_type}` and paths substituted. Write to `artifacts/structured_runbook.{index_type}.md`.
5. **Report** count of docs to process and runbook path. Ask the user to confirm before execution.

### Execute phase

1. **Read the runbook.** Follow its instructions.
2. **For each worklist entry:**
   - Check for existing valid output. Skip if present (resumability).
   - Read the doc at `doc_path`.
   - Read the prompt template at `prompt_path` and substitute `{doc_id}`, `{title}` (from frontmatter), and the full body.
   - Produce JSON matching the schema. Critically: every record must have a `verbatim_quote` that appears literally in the doc. This is checked — quotes that don't appear verbatim are flagged.
   - Validate locally. Retry once with a correction prompt if invalid.
   - Write to `output_path`.
3. **Long docs:** if a doc exceeds a conservative context budget (say 50 pages), split by top-level sections and merge records post-hoc. The runbook handles this explicitly.
4. **Report** on completion: docs processed, records extracted total, low-confidence record count, verbatim-quote mismatches (these need manual review).

## Example invocations

- "Prepare metrics extraction for the pilot."
- "Extract metrics across all docs."
- "Run structured extraction for assumptions on Model A and Model B."
- "Re-run governance extraction — I updated the prompt."

## Common gotchas

- **Verbatim quotes must actually be verbatim.** If the LLM paraphrases, the audit trail breaks. The runbook includes a post-check that searches for the quote string in the doc; flag mismatches.
- **Percentage normalization is a common failure.** "AUC = 82%" in the doc should extract as `value: 0.82, unit: "ratio"` or `value: 82, unit: "%"` — pick one convention per schema and enforce it. Mixing causes silent comparison errors.
- **Metric name standardization.** Sources use "AUC", "AUROC", "c-statistic", "area under ROC" interchangeably. The prompt must enforce a canonical name per metric. Maintain a glossary in the prompt file.
- **Don't extract from sections you didn't touch.** If re-extracting only "governance" for a doc, leave the other types' JSONs alone. `prepare_worklist.py` filters by type — don't wipe other outputs.
- **Prompt version in the output.** Include `prompt_version` in each output JSON. When you iterate prompts, you want to know which records were extracted with which version for reproducibility.
