---
name: md-normalize
description: Stitches OCR'd LaTeX back into extracted Markdown skeletons, adds OKF frontmatter, normalizes headings and section anchors, and writes final per-doc Markdown to knowledge/docs/. Use when the user asks to normalize docs or produce final Markdown (e.g. "normalize the pilot doc", "re-stitch after re-OCR"). Requires docx-extract and formula-ocr outputs; runs before indexing and bundling.
type: deterministic
---

# md-normalize

Stitches OCR'd LaTeX back into the Markdown skeletons, adds YAML frontmatter, normalizes heading style, and produces the final per-doc Markdown files in `knowledge/docs/`. These files are the portable core of the knowledge pack — they feed the Gem today and will feed Vertex AI or NotebookLM tomorrow.

## When to use

Use this skill when the user wants to:
- "Normalize the pilot doc" / "produce the final Markdown for Model A"
- "Normalize all docs"
- "Re-stitch after I updated the formula prompt" (re-runs normalization after re-OCR)

Do NOT use this skill when:
- Formula OCR isn't done yet — check that `artifacts/formulas/{doc_id}/` has JSONs for every image-type equation in the manifest.
- The user wants to bundle for Gem — that's `bundle-for-gem`, which runs after this.

## Inputs

- `artifacts/extracted/{doc_id}.md` — the skeleton from `docx-extract`.
- `artifacts/manifests/{doc_id}.json` — the equation manifest.
- `artifacts/formulas/{doc_id}/*.json` — OCR'd formulas from `formula-ocr`.
- **Config:** optional `skills/md-normalize/frontmatter_defaults.yaml` for org-wide defaults like `model_family`, `regulatory_tier`.

## Outputs

- `knowledge/docs/{doc_id}.md` — final cleaned Markdown with frontmatter, anchors, and inlined LaTeX.

### Output structure

```markdown
---
doc_id: model_a_lgd_v3
title: "Model A — Loss Given Default Methodology"
version: "3.2"
effective_date: 2025-06-01
model_family: "Credit Risk / LGD"
source_file: "Model_A_LGD_v3.2.docx"
section_count: 8
formula_count: 14
last_processed: 2026-04-17
knowledge_pack_version: 2026.04.17
---

# Model A — Loss Given Default Methodology

## 1 Executive Summary {#executive-summary}

...

## 3.2 Loss Given Default {#loss-given-default}

The LGD is estimated using the following logistic specification where collateral coverage is the primary driver:

$$
LGD = 1 - \frac{\text{Recovery}}{\text{EAD}}
$$
<!-- formula_id: eq_001 | desc: Loss Given Default defined as one minus the recovery ratio on Exposure at Default. -->

Where:
- $LGD$ — Loss Given Default
- $\text{Recovery}$ — Realized recovery amount (discounted)
- $\text{EAD}$ — Exposure at Default
```

## Procedure

1. **Validate prerequisites.** For each target doc:
   - Skeleton at `artifacts/extracted/{doc_id}.md` exists.
   - Manifest at `artifacts/manifests/{doc_id}.json` exists.
   - For every equation in the manifest with `type: image`, a corresponding JSON exists at `artifacts/formulas/{doc_id}/{equation_id}.json`. If any are missing, surface the list and halt — do not produce a doc with missing formulas.
2. **Call `helper.py` per doc.** It performs:
   - **Token substitution.** For each `{{EQUATION_<id>}}` token in the skeleton, look up the formula JSON (image type) or the `latex_converted` field in the manifest (OMML type). Replace with `$$\n<latex>\n$$\n<!-- formula_id: <id> | desc: <description> -->` for display mode, or `$<latex>$` for inline.
   - **Variable definitions.** If the formula JSON has a non-empty `variables` object, append a "Where:" bullet list after the formula.
   - **Heading normalization.** Every heading gets an explicit anchor `{#slug}` where slug is lowercase-hyphenated heading text. Anchors must match the `section_anchor` values used in manifests and formula JSONs — if they don't, the slug logic here is out of sync with `docx-extract`'s and needs to be reconciled.
   - **Frontmatter.** Build from: manifest metadata + frontmatter defaults + counts computed from the doc + current knowledge pack version.
3. **Write** to `knowledge/docs/{doc_id}.md`.
4. **Report** per doc: formula count inlined, heading count, any warnings (e.g., "inline equation detected but no formula JSON — kept as image reference").

## Example invocations

- "Normalize the pilot."
- "Produce knowledge/docs for all extracted whitepapers."
- "Re-normalize Model A, I updated eq_003."

## Common gotchas

- **Slug collisions.** Two headings with the same text get the same slug. Append `-2`, `-3`, etc. deterministically. This must be stable across runs or anchors will drift.
- **Missing formulas are fatal.** If `eq_007.json` doesn't exist but `{{EQUATION_007}}` appears in the skeleton, do NOT silently produce a doc with an unreplaced token. Halt and tell the user.
- **Frontmatter is machine-read downstream.** Keep field names consistent across docs. `model_family` not `family`, `effective_date` not `date_effective`.
- **Don't hand-edit `knowledge/docs/*.md`.** Ever. If a doc needs a fix, fix the source (raw docx, OCR prompt, or this skill) and re-run. Hand edits silently diverge from the pipeline and break reproducibility.
