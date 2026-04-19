---
name: formula-ocr
type: llm-runbook
---

# formula-ocr

Converts formula images to LaTeX using Claude Code's own vision capability. Uses the runbook pattern: a prepare phase writes a work list, then Claude Code executes the runbook to do the actual OCR. No external API calls.

## When to use

Use this skill when the user wants to:
- "Prepare the formula OCR runbook" (prepare phase)
- "Execute the formula OCR runbook" / "run formula OCR" (execute phase)
- "OCR the formulas for Model A" (implies both phases if no runbook exists yet)
- Re-run OCR after updating the prompt template

Do NOT use this skill when:
- Manifests don't exist yet — run `docx-extract` first.
- The user wants final Markdown with LaTeX inlined — that's `md-normalize`, which runs after this.

## Inputs

- **Prepare phase:** one or more `doc_id`s (or "all") indicating which docs to include.
- **Execute phase:** `artifacts/ocr_runbook.md` (produced by prepare phase).
- **Config:** `schemas/formula.schema.json` for output validation.

## Outputs

**Prepare phase produces:**
- `artifacts/ocr_worklist.json` — every image-type equation across the targeted docs as a flat list.
- `artifacts/ocr_runbook.md` — the instructions Claude Code will execute next.

**Execute phase produces:**
- `artifacts/formulas/{doc_id}/{equation_id}.json` — one file per formula, schema below.
- `artifacts/ocr_progress.log` — progress log, appended during execution.
- `artifacts/ocr_errors.log` — failures, if any.

### Formula output schema (`schemas/formula.schema.json`)

```json
{
  "equation_id": "eq_001",
  "doc_id": "model_a_lgd_v3",
  "latex": "LGD = 1 - \\frac{\\text{Recovery}}{\\text{EAD}}",
  "description": "Loss Given Default defined as one minus the recovery ratio on Exposure at Default.",
  "variables": {
    "LGD": "Loss Given Default",
    "Recovery": "Realized recovery amount (discounted)",
    "EAD": "Exposure at Default"
  },
  "confidence": "high",
  "is_formula": true,
  "display_mode": "display",
  "anchor": "model_a_lgd_v3#loss-given-default"
}
```

## Procedure

### Prepare phase

1. **Validate manifests exist** for the targeted docs. If not, tell the user to run `docx-extract` first.
2. **Build the work list.** Call `prepare_worklist.py`. It iterates manifests, filters `type: image` equations, and emits `artifacts/ocr_worklist.json` with one entry per image: `{equation_id, doc_id, image_path, section_anchor, surrounding_context, output_path, display_mode}`.
3. **Write the runbook.** Render `runbook_template.md` substituting the work list path and schema path. Write to `artifacts/ocr_runbook.md`.
4. **Report** count of formulas, pilot subset size, and the runbook path. Ask the user to confirm before moving to execute phase — they may want to spot-check the worklist first.

### Execute phase

1. **Read the runbook.** Open `artifacts/ocr_runbook.md` and follow its instructions. The runbook is authoritative; this procedure is a high-level guide.
2. **For each worklist entry:**
   - Check if `output_path` already contains a valid JSON matching the schema. If yes, skip (resumability).
   - Read the image using the view tool.
   - Apply the OCR prompt with the entry's context substituted.
   - Produce JSON matching `schemas/formula.schema.json`.
   - Validate locally before writing. If invalid, retry once with a correction prompt. If still invalid, write a stub with `confidence: "low"` and an `error` field.
   - Write to `output_path`.
   - Every 20 entries, append a progress line to `artifacts/ocr_progress.log`.
3. **Report** on completion: total processed, skipped (already done), low-confidence count, error count. Direct the user to run `qa-report` next.

## Example invocations

- "Prepare the formula OCR runbook for the pilot."
- "Execute the OCR runbook." (assumes prepare already ran)
- "Re-run formula OCR for Model A." (re-prepare, then execute for that doc)
- "OCR the formulas." (if ambiguous, Claude Code should ask: which docs? pilot or all?)

## Common gotchas

- **Don't try to do OCR during the prepare phase.** The prepare phase is deterministic Python only; it writes a work list, it does not look at images.
- **Don't call an external API.** Claude Code's own vision is the executor. If you find yourself reaching for `anthropic` SDK, stop — that's not this pipeline's model.
- **Respect resumability.** If a session drops halfway through a 450-formula run, restarting should skip the ~200 already done, not redo them.
- **Surrounding context matters.** Vision OCR accuracy goes up meaningfully when the surrounding sentences are included. If context is missing from the manifest, fix `docx-extract` — don't try to OCR blind.
- **Low-confidence is not failure.** A `confidence: "low"` record is still a record; it flags for human QA rather than being silently wrong.
