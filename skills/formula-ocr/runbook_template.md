# Formula OCR runbook

**Status:** ready for execution
**Work list:** `{{worklist_path}}`
**Output schema:** `{{schema_path}}`
**Total entries:** {{total_count}}

## Your task

Process every entry in the work list. For each entry, convert a formula image to LaTeX using your vision capability. Write a JSON file per formula to the specified output path. Do not use external APIs — use your own vision tools directly.

## Execution loop

For each entry in `{{worklist_path}}`:

1. **Check if already done.** If `entry.output_path` exists and contains valid JSON matching the schema, skip this entry. Log the skip to `artifacts/ocr_progress.log`.

2. **Read the image.** Use the view tool on `entry.image_path`.

3. **Apply the OCR prompt below.** Substitute:
   - `{surrounding_context}` → `entry.surrounding_context`
   - `{section_heading}` → whatever appears before `#` in `entry.section_anchor` or use the anchor itself
   - `{doc_id}` → `entry.doc_id`
   - `{display_mode}` → `entry.display_mode` (display or inline)

4. **Validate the JSON** against the schema. Required fields: `equation_id`, `doc_id`, `latex`, `description`, `confidence`, `is_formula`, `anchor`. If invalid, retry once with a correction message. If still invalid, write a stub with `confidence: "low"`, `is_formula: false`, and an `error` field explaining why.

5. **Write the JSON** to `entry.output_path`. Ensure the parent directory exists.

6. **Every 20 entries**, append a progress line to `artifacts/ocr_progress.log`:
   `{timestamp} | processed={N} | skipped={M} | low_confidence={L} | errors={E}`

## OCR prompt (per image)

```
You are extracting a mathematical formula from a financial model whitepaper produced by a commercial bank's risk modeling team.

Document: {doc_id}
Section: {section_heading}
Display mode: {display_mode}

Surrounding context from the document:
---
{surrounding_context}
---

Examine the image and return a JSON object with exactly these fields:

- equation_id: copy from the entry (do not change)
- doc_id: copy from the entry
- latex: the formula in LaTeX. Use standard LaTeX math syntax. Do NOT wrap in $$ or $; just the raw LaTeX body. Preserve every subscript, superscript, and symbol exactly as rendered.
- description: one-sentence plain-English description of what the formula computes, derived from the surrounding context if possible.
- variables: an object mapping each symbol or variable name in the formula to its meaning. Infer from context. If a variable's meaning is unclear, set its value to null. Always include this field — use an empty object {} only if there are no variables.
- confidence: "high" if the formula is clearly legible and symbols are unambiguous. "medium" if some inference was needed. "low" if the image is unclear, symbols are ambiguous, or you had to guess.
- is_formula: true if this image is a mathematical formula. false if it is actually a chart, diagram, logo, or other non-formula image.
- display_mode: copy from the entry
- anchor: "{doc_id}#{section_anchor}" format (copy section_anchor from entry)

Rules:
- Return ONLY the JSON object. No prose, no markdown fences, no explanation.
- Preserve mathematical precision. "PD_i" and "PD^i" and "PD_{i}" are different — get the right one.
- For Greek letters, use LaTeX names (\\alpha, \\beta, \\Sigma).
- For multi-line equations, use \\\\ between lines inside an align* or similar environment.
- If you cannot read the image at all, still return valid JSON with is_formula: false and a confidence: "low" and an explanation in the description field.
```

## Error handling

- If the image file is missing, write a stub JSON with `is_formula: false`, `confidence: "low"`, `error: "image_not_found"`, and move on.
- If the JSON you produce fails schema validation twice, write a stub with the best-effort fields plus `error: "schema_validation_failed"` and move on.
- Do NOT halt the run on individual failures. Log and continue. The QA step will catch these.

## Completion

When the work list is exhausted:

1. Append a final summary line to `artifacts/ocr_progress.log`.
2. Report to the user: total entries, processed, skipped (already done), low-confidence count, error count.
3. If the low-confidence or error count is above 10% of total, recommend the user run `qa-report` and review before proceeding to `md-normalize`.
