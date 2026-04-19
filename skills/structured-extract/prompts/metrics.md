# Metrics extraction prompt

**Prompt version:** metrics@v3
**Applies to schema:** `schemas/metrics.schema.json`

You are extracting model performance metrics from an internal model whitepaper produced by a commercial bank's risk modeling team.

## Inputs

- **Document ID:** `{doc_id}`
- **Title:** `{title}`
- **Content:** (full normalized Markdown follows)

```
{full_markdown}
```

## What to extract

Every reported performance metric. Include:

- Discrimination metrics: AUC, KS, Gini, Somers' D, c-statistic, concordance
- Goodness-of-fit: R², adjusted R², Pseudo-R², Hosmer-Lemeshow, Brier score
- Error metrics: RMSE, MAPE, MAE, MSE
- Classification metrics: Accuracy, Precision, Recall, F1, specificity, sensitivity
- Calibration metrics: calibration slope, calibration intercept, observed-to-expected ratios
- Stability metrics: PSI, CSI
- Any other numeric performance indicator explicitly reported

Do NOT extract:
- Coefficients of the model itself (those belong in a separate `coefficients_index` if built)
- Example calculations or hypothetical illustrations
- Regulatory thresholds (those belong in `governance_index`)

## Canonical metric names

Normalize variant names to these canonical forms:

- "AUC" / "AUROC" / "area under ROC" / "c-statistic" / "concordance index" → `AUC`
- "KS" / "Kolmogorov-Smirnov" / "K-S statistic" → `KS`
- "Gini" / "Gini coefficient" / "accuracy ratio" → `Gini`
- "R²" / "R-squared" / "coefficient of determination" → `R2`
- "MAPE" / "mean absolute percent error" → `MAPE`
- "HL" / "Hosmer-Lemeshow" / "HL test" → `HL`
- "PSI" / "Population Stability Index" → `PSI`

Preserve distinctions that matter: "Adjusted R²" is `R2_adjusted`, not `R2`. "Out-of-sample R²" is still `R2` but the `dataset` field captures the OOS nature.

## Output schema

Return JSON with this structure:

```json
{
  "doc_id": "{doc_id}",
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
      "anchor": "{doc_id}#performance",
      "verbatim_quote": "The out-of-time AUC for the overall portfolio is 0.82 over the 2020-2023 period (N=125,430).",
      "confidence": "high"
    }
  ],
  "extracted_at": "{today}",
  "prompt_version": "metrics@v3"
}
```

## Rules

1. **Only extract metrics explicitly stated in the doc.** Do not compute, interpolate, or infer values that aren't literally printed.
2. **Value normalization.** Convert percentages to decimals: "82%" → `value: 0.82, unit: "ratio"`. If the source reports in basis points, keep: `value: 25, unit: "bps"`. If the source reports as a decimal already, keep as decimal with `unit: "ratio"`.
3. **One record per (metric, dataset, segment) combination.** If AUC is reported for overall and for three segments on the same dataset, that's four records.
4. **Segment is null for portfolio-level metrics.** Do not make up segment names.
5. **Anchor.** Find the section heading closest above where the metric is reported. Use `{doc_id}#section-anchor` format.
6. **verbatim_quote must appear literally in the source.** Copy the exact sentence (or ≤30-word span) that reports the metric. If the metric is in a table, include enough table context that a reader can find it.
7. **Confidence:**
   - `high` — unambiguous single value, clear dataset, clear period.
   - `medium` — required inference (e.g., dataset implied from context but not stated next to the number).
   - `low` — value guessed from a figure, reported as a range collapsed to midpoint, or metric name is ambiguous.
8. **Ranges.** If reported as "AUC between 0.80 and 0.85", extract as `value: 0.825, confidence: "low"`, and include the full range description in `verbatim_quote`.
9. **Missing sample size.** Set `sample_size: null` rather than guessing.

## Return format

Return ONLY the JSON object. No prose, no markdown fences, no explanation.
