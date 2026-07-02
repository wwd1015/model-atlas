# Examples — demo the full Atlas flow

Placeholder source material for demonstrating the pipeline end-to-end: raw input → prepare (deterministic helper) → execute (Claude Code runbook) → OKF concept in `content/` → visible in the hub with search, related links, and copilot answers.

Real confidential material goes in `raw/` (gitignored). This folder is safe to commit — everything here is fabricated for demonstration.

## What's here

| File | Demonstrates |
|------|--------------|
| `videos/model-monitoring-town-hall.vtt` | `video-ingest`: WebVTT transcript → timestamped **Video Note** |
| `decks/make_demo_deck.py` | generates `new-analyst-orientation.pptx` for `deck-ingest`: slides + speaker notes → **Deck Note** |

## Run the demo

In Claude Code, just ask — "run the example video ingest" — or by hand:

```bash
# 1. Video → hub page (channel: models)
python skills/video-ingest/prepare_worklist.py \
    --videos-dir examples/videos --channel models
# then, in Claude Code: "execute the video runbook"

# 2. Deck → hub page (channel: onboarding)
python examples/decks/make_demo_deck.py          # creates the .pptx
python skills/deck-ingest/prepare_worklist.py \
    --decks-dir examples/decks --channel onboarding
# then, in Claude Code: "execute the deck runbook"

# 3. See it in the hub
python skills/knowledge-hub/helper.py validate
python -m hub.app        # → http://127.0.0.1:8050
```

The executed outputs of both demos ship with the repo (`content/models/model-monitoring-town-hall.md`, `content/onboarding/new-analyst-orientation.md`) so the hub demonstrates Video Note and Deck Note concepts out of the box — re-running the demo regenerates them.

## Things to try in the hub afterwards

- Search **"champion challenger town hall"** — lands in the video's outline with a `[mm:ss]` timestamp.
- Ask the copilot **"what did the town hall say about PSI?"** — grounded answer citing the Video Note.
- Open the Video Note and check *Related* / *Linked from* — the wiki graph picked it up.
