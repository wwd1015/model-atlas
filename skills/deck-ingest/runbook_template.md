# Deck ingest runbook

prompt_version: 1.0
Work list: `{{worklist_path}}` ({{total_count}} decks, target channel: `{{channel}}`)

You (Claude Code) are the executor. Process each worklist entry as follows.

## Per-entry procedure

1. **Resumability check.** If `output_path` already exists and starts with `---` frontmatter containing a `type:` field, skip and log as skipped.
2. **Read** the slide extraction at `slides_path`. Weigh speaker `notes` heavily — they carry the narrative the bullets compress away.
3. **Low-text slides.** If `low_text_slides` is non-empty, note in the output's Follow-ups section that those slides are image-heavy and were summarized from context only. If the user asked for full fidelity, ask them for a PDF/PNG export and read those slides with vision before writing.
4. **Write the OKF concept** to `output_path`:

```markdown
---
type: Deck Note
title: <clean human title>
description: <one sentence — what the deck covers and who it's for>
tags: [<channel>, deck, <2-4 topical tags>]
timestamp: <today, YYYY-MM-DD>
resource: <source_path>
prompt_version: "1.0"
---

# <title>

## Summary

<3-6 sentences — purpose of the deck, audience, main message.>

## <topic sections>

<Reorganize by TOPIC, not slide-by-slide. Merge repeated slides. Use the
deck's own section headers where they exist. Reference slides inline as
(slide 12) so readers can find the original.>

## Follow-ups

<open questions, image-only slides not fully captured, material that seems
stale — anything a human should verify. Omit if empty.>
```

5. **Numbers are verbatim.** Thresholds, dates, metric values from slides must be quoted exactly, with their slide number.
6. **Cross-link.** Link concepts that already exist in the hub with `[[wiki-link]]` syntax (models, policies, lessons, tools).

## After the batch

- Report: processed / skipped / slides flagged for vision review.
- Remind the user to restart the hub and commit `content/` changes.
