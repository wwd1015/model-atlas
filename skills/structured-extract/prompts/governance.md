# Governance extraction prompt

**Prompt version:** governance@v1
**Applies to schema:** `schemas/governance.schema.json`

You are extracting governance facts from an internal model whitepaper produced by a commercial bank's risk modeling team.

## Inputs

- **Document ID:** `{doc_id}`
- **Title:** `{title}`
- **Content:**

```
{full_markdown}
```

## What to extract

Governance and lifecycle metadata for the model. One record per doc (the `records` array is typically length 1). Capture:

- Model owner (team or named individual, whichever the doc states).
- Approver (validation group, MRM committee, etc.).
- Approval date.
- Effective date.
- Next review date.
- Regulatory tier / materiality classification (e.g. "Tier 1", "High risk").
- Use cases the model is approved for.
- Limitations or conditions of approval.

Do NOT extract:
- Performance metrics (those belong in `metrics_index`).
- Assumptions (those belong in `assumptions_index`).
- Model dependencies (those belong in `dependencies_index`).

## Output schema

```json
{
  "doc_id": "{doc_id}",
  "index_type": "governance",
  "records": [
    {
      "owner": "Retail Credit Modeling",
      "approver": "Model Risk Management Committee",
      "approval_date": "2025-06-01",
      "effective_date": "2025-07-01",
      "next_review_date": "2026-07-01",
      "regulatory_tier": "Tier 1",
      "use_cases": ["IFRS 9 ECL", "Internal capital allocation"],
      "limitations": ["Not approved for regulatory capital calculation", "Scope excludes commercial real estate portfolios"],
      "anchor": "{doc_id}#governance",
      "verbatim_quote": "The model was approved by MRM on June 1, 2025, with an effective date of July 1, 2025 and annual review cadence.",
      "confidence": "high"
    }
  ],
  "extracted_at": "{today}",
  "prompt_version": "governance@v1"
}
```

## Rules

1. Dates must be ISO format (YYYY-MM-DD). If the source only gives a year or quarter, set the field to `null` and capture the coarse-grained value in `verbatim_quote`.
2. `regulatory_tier` should use the source's exact categorical label (e.g. "Tier 1", "High", "Moderate"). Do not re-map across firms' conventions.
3. `use_cases` and `limitations` are free-text lists. Keep each item under ~15 words.
4. `verbatim_quote` is required and must appear literally in the source.
5. `confidence`:
   - `high` — governance section is explicit and dates are ISO.
   - `medium` — at least one field inferred from surrounding context (e.g. owner inferred from the cover page).
   - `low` — governance section is absent; most fields are `null`.
6. If the doc has no governance section at all, return `records: []` and set `confidence` field at the record level is N/A — just set `error: "no_governance_section"` at the top level.

## Return format

Return ONLY the JSON object. No prose, no markdown fences.
