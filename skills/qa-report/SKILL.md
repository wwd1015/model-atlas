---
name: qa-report
type: deterministic
---

# qa-report

Produces human-reviewable side-by-side HTML reports for formula OCR and structured extraction. This is the non-negotiable quality gate before shipping to the Gem — LLM outputs that look plausible can still be wrong, and only human review catches subtle errors.

## When to use

Use this skill when the user wants to:
- "Generate the formula QA report"
- "QA the metrics extraction"
- "I'm ready to review OCR results" / "show me the structured extraction review"
- Before shipping a production knowledge pack — always.

Do NOT use this skill when:
- The data to QA doesn't exist yet. Run `formula-ocr` or `structured-extract` first.

## Inputs

- **Required argument:** `qa_type` ∈ {`formula`, `structured`}.
- **For formula:** `artifacts/formulas/**/*.json` + source images in `artifacts/extracted/*/images/`.
- **For structured:** `artifacts/structured/*.{index_type}.json` + `knowledge/docs/*.md` for source lookup.
- Optional: `doc_id` to filter (default: all).

## Outputs

- `artifacts/qa/formula_review.html` — for formula QA.
- `artifacts/qa/structured_review.{index_type}.html` — for structured QA.

### Formula review layout

- **Summary header.** Total formulas, counts per confidence tier, pointer to where to flag issues.
- **Sort order.** Low confidence first, then medium, then high. Within each tier, sort by doc_id.
- **Per-formula row.** Left: original image embedded (base64 or relative path). Right: rendered LaTeX via MathJax CDN, plus description, variables, confidence, doc/anchor.
- **Flag controls.** Each row has an "issue?" checkbox the reviewer can tick. Saved state is just visual — the reviewer compiles a fix list separately.

### Structured review layout

- **Summary header.** Total records, counts per confidence tier, quote-mismatch count (highlight if > 0).
- **Sort order.** Quote mismatches first, then low confidence, then medium, then high.
- **Per-record row.** Left: extracted value (metric name, value, dataset, etc.). Right: the verbatim_quote, plus a link to the anchor in the source doc. If quote_mismatch is true, highlight prominently in red.

## Procedure

1. **Validate the qa_type argument.** Exactly one of `formula` or `structured`.
2. **For formula:**
   - Walk `artifacts/formulas/` collecting all JSONs.
   - For each, locate the source image (manifest gives the path).
   - Render HTML via a Jinja2 template. Use MathJax CDN for LaTeX rendering in-browser.
3. **For structured:**
   - Walk `artifacts/structured/*.{index_type}.json` for the specified type (or all types if `all`).
   - For each record, locate the source doc in `knowledge/docs/`.
   - Verify the `verbatim_quote` appears in the source (already done in the runbook, but re-check — don't trust). Mark mismatches.
   - Render HTML.
4. **Include review metadata.** At the bottom of the HTML: build timestamp, knowledge pack version, input counts. Print-friendly — the reviewer may want to export as PDF for archive.
5. **Open the report** or surface its path to the user. Recommend they review before declaring a pack ready to ship.

## Review budget guidance (include in the report header)

- **Formula QA:** review 100% of low/medium confidence records. Sample 20% of high confidence. For 450 formulas with normal confidence distribution, budget 4-6 hours.
- **Structured QA:** review 100% of quote mismatches (these are non-negotiable — a mismatch means the extraction is hallucinating). Review 100% of low/medium confidence. Sample 10% of high confidence. For 300 metric records across 30 docs, budget 3-4 hours.

## Example invocations

- "Build the formula QA report."
- "QA the structured extraction for metrics."
- "Show me the formula review for Model A only."

## Common gotchas

- **Don't skip QA on the second pipeline run.** Even if the first run's QA was clean, a prompt update or a new doc can introduce new failures. Re-QA every production build.
- **MathJax must be loaded from CDN in the HTML.** If you're offline during review, add a fallback note telling the reviewer to eyeball the raw LaTeX.
- **Side-by-side is non-negotiable for formulas.** Reviewing rendered LaTeX without the source image is useless — the whole point is comparing "what the OCR said" to "what the image shows".
- **Quote mismatches in structured QA are a signal that the prompt is hallucinating.** Don't just fix the record — investigate the prompt. A few mismatches per batch is normal; a pattern means the prompt needs work.
