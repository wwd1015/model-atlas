---
name: formula-index
description: Builds knowledge/formula_index.md — the cross-doc index of every formula with source doc, anchor, LaTeX, description, and variables. Use when the user asks to build or regenerate the formula index, or to list all formulas across models. Requires formula OCR outputs. For metrics/assumptions/data/governance/dependencies rollups use structured-index instead.
type: deterministic
---

# formula-index

Builds the cross-doc formula index — a single Markdown file listing every formula across all whitepapers with source, anchor, LaTeX, description, and variables. This file is a top-priority input to the Gem because it lets the Gem answer formula questions with a direct lookup instead of scanning content bundles.

## When to use

Use this skill when the user wants to:
- "Build the formula index" / "rebuild formula_index.md"
- "Regenerate the formula index after updating Model A"
- "Show me all formulas across all models"

Do NOT use this skill when:
- OCR hasn't run yet — there are no formula JSONs to index.
- The user wants a structured index of metrics or assumptions — that's `structured-index`.

## Inputs

- All `artifacts/formulas/**/*.json` files.
- All `artifacts/manifests/*.json` files (for OMML equations which aren't in the formulas dir).
- Optional: `skills/formula-index/grouping.yaml` for custom ordering (default: group by doc, then by anchor order within doc).

## Outputs

- `knowledge/formula_index.md`

### Output structure

```markdown
# Model Whitepaper Formula Index

This index lists every formula across all model whitepapers. For each formula, see the anchor for the authoritative source context. Formula IDs (F-001, F-002, ...) are stable across regenerations where possible but may change when formulas are added or removed.

Last built: 2026-04-17
Knowledge pack version: 2026.04.17
Total formulas: 432 across 30 documents

## How to use
- Search by topic or description to find a formula.
- Follow the anchor `[doc_id#section]` to the source doc for full context.
- Variables are defined inline where derivable from the source.

---

## F-001 — Loss Given Default (baseline)

**Source:** Model A — Loss Given Default Methodology (§3.2)
**Anchor:** `[model_a_lgd_v3#loss-given-default]`
**Confidence:** high
**Description:** Loss Given Default defined as one minus the recovery ratio on Exposure at Default.

$$
LGD = 1 - \frac{\text{Recovery}}{\text{EAD}}
$$

**Variables:**
- $LGD$ — Loss Given Default
- $\text{Recovery}$ — Realized recovery amount (discounted)
- $\text{EAD}$ — Exposure at Default

---

## F-002 — Probability of Default (logistic)

**Source:** Model B — PD Methodology (§4.1)
**Anchor:** `[model_b_pd_v2#pd-calibration]`
**Confidence:** high
**Description:** PD computed as a logistic transformation of the linear score.

$$
PD = \frac{1}{1 + e^{-(\beta_0 + \sum_i \beta_i x_i)}}
$$

**Variables:**
- $\beta_0$ — intercept
- $\beta_i$ — coefficient on feature $i$
- $x_i$ — feature value

---
```

## Procedure

1. **Gather all formula sources.**
   - Walk `artifacts/formulas/` for image-OCR'd formulas.
   - Walk `artifacts/manifests/` for OMML equations with non-null `latex_converted`.
   - Skip entries with `is_formula: false`.
2. **Assign stable IDs.** Sort by (doc_id, paragraph_index). Assign `F-001`, `F-002`, ... in order. If a mapping file `artifacts/formula_id_map.json` exists from a prior run, preserve existing IDs for unchanged formulas; only assign new IDs to new formulas.
3. **Render each entry.** Use the template in the output structure. Include variables section only if non-empty.
4. **Write `knowledge/formula_index.md`** with header metadata (date, version, total count).
5. **Write `artifacts/formula_id_map.json`** mapping `{doc_id, equation_id} → F-NNN` for stability across runs.
6. **Report** count of formulas indexed, new formulas since last run (if map existed), and removed formulas (flag these — they may indicate a doc was deleted or re-extracted).

## Example invocations

- "Build the formula index."
- "Regenerate formula_index.md."
- "How many formulas do we have across all docs?" (Claude Code can answer by running this skill and reporting the count.)

## Common gotchas

- **ID stability matters.** If F-042 refers to PD in v1 of the index and refers to LGD in v2, Gem answers citing F-042 become incorrect across versions. The ID map file is how stability is preserved.
- **Removed formulas are a signal.** If a formula disappears between runs, it might be (a) intentional — doc updated and formula gone, or (b) a bug — OCR failed silently. Surface the list to the user either way.
- **Low-confidence formulas should still appear** in the index but with a confidence flag. Do not filter them out; the Gem can decide how to handle.
- **OMML vs image equations go into the same index.** The source distinction doesn't matter to end users; they just want the formula.
