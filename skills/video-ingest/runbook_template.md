# Video ingest runbook

prompt_version: 1.0
Work list: `{{worklist_path}}` ({{total_count}} videos, target channel: `{{channel}}`)

You (Claude Code) are the executor. Process each worklist entry as follows.

## Per-entry procedure

1. **Resumability check.** If `output_path` already exists and starts with `---` frontmatter containing a `type:` field, skip the entry and log it as skipped.
2. **Read** the normalized transcript at `transcript_path`.
3. **NPI gate.** If the transcript appears to contain customer-identifying financial information (names + account details, guarantor financials), STOP for that entry, write nothing, and flag it to the user citing `content/compliance/npi-data-handling.md`.
4. **Write the OKF concept** to `output_path`:

```markdown
---
type: Video Note
title: <clean human title>
description: <one sentence — what the video covers and who should watch it>
tags: [<channel>, video, <2-4 topical tags>]
timestamp: <today, YYYY-MM-DD>
resource: <media_path>
prompt_version: "1.0"
---

# <title>

## Summary

<3-6 sentences. What the session covered, key decisions or takeaways.>

## Key points

<bulleted list; each point one line, concrete>

## Outline

<one line per major segment, keeping the [mm:ss] timestamps from the transcript
so viewers can jump to the moment: `- [04:00] Q&A on monitoring thresholds`>

## Follow-ups

<action items or open questions raised, if any; otherwise omit this section>
```

5. **Ground everything in the transcript.** Do not add facts that are not in it. Where the speaker states a number or threshold, quote it rather than paraphrase.
6. **Cross-link.** Where the video discusses a concept that exists in the hub (a model, a policy, a lesson), link it with `[[wiki-link]]` syntax.

## After the batch

- Report: processed / skipped / flagged-for-NPI counts.
- Remind the user to restart the hub (or run the refresh) so the new pages appear, and to commit `content/` changes.
