# Data coverage extraction prompt

**Prompt version:** data@v1
**Applies to schema:** `schemas/data.schema.json`

You are extracting training and validation data coverage facts from an internal model whitepaper produced by a commercial bank's risk modeling team.

## Inputs

- **Document ID:** `{doc_id}`
- **Title:** `{title}`
- **Content:**

```
{full_markdown}
```

## What to extract

Facts about the data used to build and validate the model. One record per dataset role (development, in-sample, out-of-sample, out-of-time, monitoring). For each record, capture:

- Dataset role: `development`, `in_sample`, `out_of_sample`, `out_of_time`, `monitoring`, `other`.
- Period: start and end (as stated; do not infer).
- Sample size (integer, null if not stated).
- Sources: the named data systems / feeds the model pulls from.
- Segments: how the population was sliced.
- Exclusions: accounts or time windows explicitly excluded.
- Target definition: the dependent variable definition, if stated in the data section.

Do NOT extract:
- Performance metrics (those belong in `metrics_index`).
- Assumptions about stationarity or representativeness — those are `assumptions_index`.

## Output schema

```json
{
  "doc_id": "{doc_id}",
  "index_type": "data",
  "records": [
    {
      "dataset_role": "out_of_time",
      "period_start": "2023-01-01",
      "period_end": "2024-12-31",
      "sample_size": 125430,
      "sources": ["Core banking ledger", "Collections system"],
      "segments": ["Retail", "Small business"],
      "exclusions": ["Accounts < 6 months on book", "Charged-off prior to observation"],
      "target_definition": "90+ days past due within 12 months of observation",
      "anchor": "{doc_id}#data",
      "verbatim_quote": "The out-of-time validation sample covers January 2023 through December 2024 and includes 125,430 accounts.",
      "confidence": "high"
    }
  ],
  "extracted_at": "{today}",
  "prompt_version": "data@v1"
}
```

## Rules

1. Only extract facts explicitly stated. Do not infer sample sizes from implied context.
2. Use ISO dates where the source allows. If the source only says "Q3 2024", record it verbatim as a string rather than inventing a precise date.
3. Every record must carry a `verbatim_quote` that appears literally in the source.
4. Set `sample_size: null` when not stated rather than guessing.
5. `confidence`:
   - `high` — unambiguous, explicit facts.
   - `medium` — one element inferred from nearby context (e.g., period stated in a caption above the table).
   - `low` — multiple elements inferred, or data section is sparse.
6. One record per dataset role. If the doc reports both a 2020-2022 OOS and a 2023-2024 OOT window, that's two records.

## Return format

Return ONLY the JSON object. No prose, no markdown fences.
