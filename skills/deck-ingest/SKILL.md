---
name: deck-ingest
type: llm-runbook
---

# deck-ingest

Turns PowerPoint decks (trainings, review packs, methodology walkthroughs) into OKF markdown concepts for the Atlas hub. Runbook pattern: the prepare phase extracts per-slide text and speaker notes deterministically (python-pptx); Claude Code executes the runbook to synthesize the knowledge concept. No external API calls.

## When to use

Use this skill when the user wants to:
- "Ingest the deck(s) in raw/decks" / "prepare the deck ingest runbook" (prepare phase)
- "Execute the deck runbook" (execute phase)
- "Turn this pptx into a hub page"

Do NOT use this skill when:
- The source is a Word whitepaper — that's the `docx-extract` pipeline (structure and formulas need the full treatment).
- The deck is just an image dump with no text and no notes — flag it for manual conversion instead.

## Inputs

- **Prepare phase:** `.pptx` files under `raw/decks/`. Requires `python-pptx` (`pip install -e '.[ingest]'`).
- **Optional:** `--channel` (default `onboarding`) — target hub channel.

## Outputs

**Prepare phase produces:**
- `artifacts/decks/{slug}_slides.json` — per-slide `{n, title, bullets, notes, has_images, text_density}`.
- `artifacts/deck_worklist.json` — one entry per deck: `{slug, title, slides_path, source_path, channel, output_path, low_text_slides}`.
- `artifacts/deck_runbook.md` — instructions Claude Code executes next.

**Execute phase produces:**
- `content/{channel}/{slug}.md` — an OKF concept, `type: Deck Note`, organized by the deck's topic flow (not slide-by-slide), with a `resource:` pointer to the source file.

## Procedure

### Prepare phase

1. Run `python skills/deck-ingest/prepare_worklist.py [--channel onboarding]`.
2. It extracts every slide's title/body/notes, computes text density, marks slides that are mostly images (`low_text_slides`) for optional vision review, and writes the worklist + runbook.
3. Report: decks found, slide counts, how many slides are low-text.

### Execute phase

1. Read `artifacts/deck_runbook.md` — it is authoritative.
2. For each worklist entry: skip if `output_path` has valid frontmatter (resumability); read the slides JSON; synthesize the OKF concept per the runbook. If `low_text_slides` is non-empty and the user asked for full fidelity, request slide images (export pptx → PDF/PNG) and read them with vision.
3. Report processed / skipped / slides needing vision review.

## Example invocations

- "Ingest the model governance training deck."
- "Prepare the deck runbook for raw/decks, channel compliance."
- "Execute the deck runbook."

## Common gotchas

- **Speaker notes are gold.** They usually carry the narrative the bullets compress away — the runbook weighs them heavily.
- **Don't preserve slide order slavishly.** Decks repeat and interleave; the output should read as a document, organized by topic.
- **Numbers get quoted verbatim.** Thresholds, dates, and metrics from slides must not be paraphrased.
