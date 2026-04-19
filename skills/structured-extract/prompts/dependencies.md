# Dependencies extraction prompt

**Prompt version:** dependencies@v1
**Applies to schema:** `schemas/dependencies.schema.json`

You are extracting model-to-model dependencies from an internal model whitepaper produced by a commercial bank's risk modeling team.

## Inputs

- **Document ID:** `{doc_id}`
- **Title:** `{title}`
- **Content:**

```
{full_markdown}
```

## What to extract

Upstream and downstream dependencies. A dependency exists whenever the model consumes the output of another model as an input, or whenever this model's output is documented as feeding into another named model.

For each dependency, capture:

- Direction: `upstream` (this model consumes another's output) or `downstream` (this model feeds another).
- The other model's name or ID, as stated in the source.
- What is passed (PD, LGD, EAD, score, rating, forecast, etc.).
- Whether the dependency is hard (required for this model to run) or soft (used as a validation cross-check).

Do NOT extract:
- Data-source dependencies (those belong in `data_index`).
- Calibration anchors that are not themselves model outputs (e.g. external macro series).

## Output schema

```json
{
  "doc_id": "{doc_id}",
  "index_type": "dependencies",
  "records": [
    {
      "direction": "upstream",
      "other_model_id": "model_a_pd_v3",
      "other_model_name": "Retail PD Model",
      "passed_artifact": "PD",
      "hardness": "hard",
      "anchor": "{doc_id}#inputs",
      "verbatim_quote": "Expected loss is computed as PD × LGD × EAD, where PD is supplied by the Retail PD Model (internal reference: model_a_pd_v3).",
      "confidence": "high"
    },
    {
      "direction": "downstream",
      "other_model_id": null,
      "other_model_name": "IFRS 9 ECL Engine",
      "passed_artifact": "LGD point estimate",
      "hardness": "hard",
      "anchor": "{doc_id}#downstream",
      "verbatim_quote": "The LGD point estimate is consumed by the IFRS 9 ECL engine for accounting provision calculations.",
      "confidence": "medium"
    }
  ],
  "extracted_at": "{today}",
  "prompt_version": "dependencies@v1"
}
```

## Rules

1. Prefer `other_model_id` in `{model_family}_{name}_v{version}` form where the source provides enough to infer it. If not, leave `other_model_id: null` and rely on `other_model_name`.
2. `direction` must be one of `upstream` or `downstream`. If the same relationship is mentioned from both directions in the same doc, prefer `upstream` (we're documenting this model's inputs).
3. `hardness` is `hard` if the dependency is required for production use; `soft` if it's only a benchmark or cross-check.
4. `verbatim_quote` must appear literally in the source.
5. `confidence`:
   - `high` — dependency explicitly stated with model name and artifact.
   - `medium` — one of {name, artifact, direction} inferred.
   - `low` — dependency implied rather than stated.
6. Deduplicate: if the same (direction, other_model, artifact) appears in multiple sections, keep a single record with the most specific verbatim_quote.

## Return format

Return ONLY the JSON object. No prose, no markdown fences.
