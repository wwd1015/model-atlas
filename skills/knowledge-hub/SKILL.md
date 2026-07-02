---
name: knowledge-hub
type: deterministic
---

# knowledge-hub

Operates the Atlas hub app: run it locally, validate the OKF content bundle, and sanity-check the search/copilot engine after content changes. Type A — the helper does the plumbing; no LLM reasoning inside the step.

## When to use

Use this skill when the user wants to:
- "Run the hub" / "start Atlas" / "serve the knowledge hub"
- "Validate the content bundle" / "check OKF conformance"
- "Why isn't my new page showing up?" (validate, then restart)

Do NOT use this skill when:
- The user wants to *add* content — write the markdown (or use an ingest skill), then use this to validate.
- The user wants Gem bundling — that's `bundle-for-gem`.

## Inputs

- The OKF bundle under `content/` and pipeline docs under `knowledge/docs/`.
- Port (optional): `--port 8080` on `serve` / `python -m hub.app`, or env `ATLAS_PORT` (default 8050). Also `ATLAS_HOST`, `ATLAS_CONTENT_DIR`, `ATLAS_KNOWLEDGE_DOCS`.

## Outputs

- `validate`: OKF conformance report (missing frontmatter, missing `type`) + corpus stats to stdout. Exit code 1 on problems.
- `serve`: the app on `http://127.0.0.1:$ATLAS_PORT`.

## Procedure

1. **Validate** after any content change:
   ```bash
   python skills/knowledge-hub/helper.py validate
   ```
   Fix any reported file before serving — a missing `type` field means the file is not a valid OKF concept.
2. **Serve** locally:
   ```bash
   python -m hub.app        # or: python skills/knowledge-hub/helper.py serve
   ```
3. **Content not appearing?** The corpus is loaded at process start — restart the server. If it still doesn't appear, run validate: unparseable frontmatter files are skipped with a warning.
4. **Deploy** to Posit Connect: see `hub/README.md` (entrypoint `hub.app:app`).

## Example invocations

- "Validate the Atlas bundle."
- "Start the hub on port 8080."
- "I added a lesson learned but don't see it — check it."
