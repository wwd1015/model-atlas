# Assumptions extraction prompt

**Prompt version:** assumptions@v1
**Applies to schema:** `schemas/assumptions.schema.json`

You are extracting key modeling assumptions from an internal model whitepaper produced by a commercial bank's risk modeling team.

## Inputs

- **Document ID:** `{doc_id}`
- **Title:** `{title}`
- **Content:**

```
{full_markdown}
```

## What to extract

Assumptions explicitly stated in the doc that materially affect model behavior. Categories to cover:

- **Distributional assumptions.** "Losses are assumed log-normal", "residuals are Gaussian", "defaults follow a Poisson process".
- **Independence assumptions.** "Defaults are assumed independent conditional on the systemic factor", "exposures are independent".
- **Stationarity assumptions.** "The calibration period is assumed representative of the forecast horizon".
- **Functional form assumptions.** "Linear relationship between score and log-odds", "monotone increasing in LTV".
- **Segmentation rules.** "Portfolio is segmented by product type; each segment is modeled independently".
- **Exclusion rules.** "Accounts with less than 6 months history are excluded", "charge-offs are treated as full loss".
- **Treatment of missing data.** "Missing values imputed with segment mean", "complete cases only".
- **Scaling/transformation assumptions.** "Features are winsorized at 1st/99th percentile", "log-transformed".

Do NOT extract:
- Performance metrics (those belong in `metrics_index`)
- Data coverage facts (those belong in `data_index`) — unless they're framed as an assumption ("we assume the 2020 dataset is representative...")
- Governance info (those belong in `governance_index`)

## Output schema

```json
{
  "doc_id": "{doc_id}",
  "index_type": "assumptions",
  "records": [
    {
      "assumption_id": "A-001",
      "category": "distributional",
      "statement": "Loss Given Default residuals are assumed to follow a Beta distribution on [0,1].",
      "impact": "Affects confidence intervals and tail estimates for LGD forecasts.",
      "anchor": "{doc_id}#methodology",
      "verbatim_quote": "We assume that LGD residuals follow a Beta distribution, which provides natural bounding to the unit interval.",
      "confidence": "high"
    }
  ],
  "extracted_at": "{today}",
  "prompt_version": "assumptions@v1"
}
```

## Rules

1. **category** must be one of: `distributional`, `independence`, `stationarity`, `functional_form`, `segmentation`, `exclusion`, `missing_data`, `transformation`, `other`.
2. **statement** is your one-sentence restatement of the assumption in canonical form. Clear enough to compare across docs.
3. **impact** is a one-sentence note on why the assumption matters. Derive from context; if not stated, write `null`.
4. **verbatim_quote** must appear literally in the source, ≤50 words. This is the audit trail.
5. **Assumptions that are only implied, not stated.** Extract only if strongly implied by explicit language. If you have to guess, set `confidence: "low"` and include a note in `impact`.
6. **Don't extract obvious background facts.** "Interest rates are in percent" is not a modeling assumption worth indexing.
7. **Numbered assumption_id** per doc, in order of appearance.

## Return format

Return ONLY the JSON object. No prose, no markdown fences.
