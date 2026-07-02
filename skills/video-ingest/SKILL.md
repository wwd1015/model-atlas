---
name: video-ingest
type: llm-runbook
---

# video-ingest

Turns recorded videos (trainings, walkthroughs, town halls) into OKF markdown concepts for the Atlas hub. Runbook pattern: the prepare phase parses transcripts deterministically; Claude Code executes the runbook to write the knowledge concept. No external API calls, no speech-to-text service — a transcript must exist (export it from the meeting tool, or drop the `.vtt`/`.srt` next to the video).

## When to use

Use this skill when the user wants to:
- "Ingest the video(s) in raw/videos" / "prepare the video ingest runbook" (prepare phase)
- "Execute the video runbook" (execute phase)
- "Turn this recording/transcript into a hub page"

Do NOT use this skill when:
- There is no transcript and no embedded subtitles — Claude Code cannot hear audio. Ask the user to export a transcript first (Teams/Zoom/Meet all support this).
- The source is a Word doc or deck — that's `docx-extract` or `deck-ingest`.

## Inputs

- **Prepare phase:** video/transcript files under `raw/videos/`. A transcript is any of:
  - `{stem}.vtt` / `{stem}.srt` / `{stem}.txt` sharing the video's file stem (or standing alone);
  - subtitles embedded in the container (extracted automatically if `ffmpeg` is on PATH).
- **Optional:** `--channel` (default `onboarding`) — which hub channel the concepts belong to.

## Outputs

**Prepare phase produces:**
- `artifacts/videos/{slug}_transcript.md` — normalized transcript with `[mm:ss]` timestamps.
- `artifacts/video_worklist.json` — one entry per video: `{slug, title, transcript_path, media_path, channel, output_path}`.
- `artifacts/video_runbook.md` — instructions Claude Code executes next.

**Execute phase produces:**
- `content/{channel}/{slug}.md` — an OKF concept, `type: Video Note`, with Summary / Key points / Timestamped outline / Follow-ups, frontmatter `resource:` pointing at the media path.

## Procedure

### Prepare phase

1. Run `python skills/video-ingest/prepare_worklist.py [--channel onboarding]`.
2. It scans `raw/videos/`, pairs transcripts with media, extracts embedded subtitles via ffmpeg when no sidecar transcript exists, normalizes everything to `[mm:ss]` blocks, and writes the worklist + runbook.
3. Report: videos found, transcripts resolved, any videos skipped for missing transcripts.

### Execute phase

1. Read `artifacts/video_runbook.md` — it is authoritative.
2. For each worklist entry: skip if `output_path` exists with valid frontmatter (resumability); read the transcript; write the OKF concept per the runbook's template and prompt.
3. Report processed / skipped / flagged, and remind the user to restart the hub (or run refresh) to see the new page.

## Example invocations

- "Ingest the onboarding recording I dropped in raw/videos."
- "Prepare the video runbook for the compliance town hall, channel compliance."
- "Execute the video runbook."

## Common gotchas

- **Don't summarize during prepare.** Prepare is deterministic parsing only.
- **Keep timestamps.** The `[mm:ss]` outline is what makes a video note navigable — viewers jump to the moment.
- **NPI check.** Transcripts of customer calls may contain NPI — the runbook requires flagging and stopping if detected, per `content/compliance/npi-data-handling.md`.
