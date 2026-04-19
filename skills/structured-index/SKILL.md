---
name: structured-index
type: deterministic
---

# structured-index

Rolls up per-doc structured JSONs (from `structured-extract`) into cross-doc indexes — one Markdown file for the Gem and one CSV file for deterministic lookup. Produces the files that actually answer cross-doc aggregation questions like "which model has the highest AUC?".

## When to use

Use this skill when the user wants to:
- "Build the metrics index" / "roll up metrics across all docs"
- "Regenerate indexes/metrics_index.md"
- "Build all structured indexes"

Do NOT use this skill when:
- Per-doc extractions don't exist yet — run `structured-extract` first for that type.
- The user wants the formula index — that's `formula-index`.

## Inputs

- **Required argument:** `index_type` ∈ {`metrics`, `assumptions`, `data`, `governance`, `dependencies`} or `all`.
- `artifacts/structured/*.{index_type}.json` files.
- `schemas/{index_type}.schema.json` — for validation.

## Outputs

Per index type:
- `knowledge/indexes/{index_type}_index.md` — Gem-facing Markdown with table and caveats.
- `knowledge/indexes/{index_type}_index.csv` — machine-readable, one row per record.

### Markdown output structure (metrics example)

```markdown
# Model Performance Metrics — Cross-Doc Index

This index lists every performance metric reported across all model whitepapers. **Metrics are not directly comparable across different datasets or periods.** Always check the `dataset` and `period` columns before drawing conclusions.

Last built: 2026-04-17
Knowledge pack version: 2026.04.17
Total records: 287 across 30 documents

## How to use this index
- Filter by `metric` to compare the same metric across models.
- Filter by `doc_id` to see all metrics for one model.
- **Always surface `dataset` and `period` caveats when comparing across models.**

## Metrics table

| doc_id | model_name | metric | value | dataset | segment | period | sample_size | anchor |
|--------|-----------|--------|-------|---------|---------|--------|-------------|--------|
| model_a_pd_v3 | Model A PD | AUC | 0.82 | OOT 2024 | Overall | 2020-2023 | 125,430 | [model_a_pd_v3#performance] |
| model_a_pd_v3 | Model A PD | AUC | 0.79 | OOT 2024 | Small business | 2020-2023 | 18,200 | [model_a_pd_v3#performance] |
| model_a_pd_v3 | Model A PD | KS | 0.51 | OOT 2024 | Overall | 2020-2023 | 125,430 | [model_a_pd_v3#performance] |
| model_b_lgd_v2 | Model B LGD | R2 | 0.67 | OOT 2024 | Overall | 2019-2023 | 42,100 | [model_b_lgd_v2#validation] |

## Important caveats
- **Different datasets:** Models A and B are validated on overlapping but not identical periods; cross-model comparisons are indicative only.
- **Different segments:** Some models report segment-level metrics, others don't. Missing does not mean worse.
- **Metric name standardization:** Source docs use "AUC", "AUROC", "c-statistic" interchangeably; all are stored as `AUC` in this index.

## Extraction audit
Full verbatim quotes are available in `artifacts/structured/{doc_id}.metrics.json` for every record. For any cited value, the source sentence is preserved for verification.
```

## Procedure

1. **Gather inputs.** For the target `index_type`, glob `artifacts/structured/*.{index_type}.json`.
2. **Validate each JSON** against the schema. Reject invalid ones and surface the list to the user — do not silently drop.
3. **Flatten.** Each record becomes a row. Add `doc_id` and `model_name` (from the per-doc JSON) and preserve all record fields.
4. **Write CSV first.** Canonical column order matching the schema. Every record goes in. This is the machine-readable source of truth.
5. **Write Markdown** with:
   - Header metadata (date, version, total record count, doc count).
   - "How to use" section.
   - Main table. Truncate `verbatim_quote` column (too wide for Markdown table) — point readers to the JSON for full quotes.
   - Caveats section (partly static, partly computed — e.g., if datasets vary across docs, flag that).
   - Extraction audit footer.
6. **For `all`**, run per type and produce all index files.
7. **Report** per index: total records, docs covered, any records dropped for schema failure, any cross-doc patterns worth noting (e.g., "3 docs report AUC, 27 docs do not — consider whether these 27 should be revisited").

## Example invocations

- "Build the metrics index."
- "Roll up all structured indexes."
- "Rebuild indexes/metrics_index.md — I re-extracted for Model C."

## Common gotchas

- **Markdown tables have practical width limits.** If a column like `verbatim_quote` is wide, omit from the Markdown table but keep in the CSV. Gem reads the Markdown; CSV is for you.
- **Numeric formatting.** Keep raw numbers in the CSV (`0.82`) but render thousand-separators in the Markdown (`125,430` not `125430`).
- **Anchors must be clickable in Gem's Markdown renderer.** Use `[doc_id#section]` format — Gem doesn't resolve these as links, but the format is what the system prompt tells it to look for.
- **Don't hand-edit the index files.** If a record is wrong, fix it in `structured-extract` (prompt or QA) and re-run. Hand edits cause drift.
- **Caveats section is partly generated.** Compute dataset heterogeneity, period heterogeneity, and segment coverage stats; fold into the caveats list dynamically. Don't hardcode caveats that may not apply to a given build.
