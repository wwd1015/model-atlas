# Atlas

A centralized team knowledge hub with two halves:

1. **The hub** (`hub/`) — a Dash app (local or Posit Connect) where the team onboards, browses model documentation, reads compliance policies and lessons learned, discovers tooling, searches everything, and asks a grounded copilot. Think "team second brain," LLM-wiki style: every concept cross-linked, backlinked, and recommendable.
2. **The pipeline** (`skills/`) — Claude Code skills that convert source material — Word whitepapers (formulas as images), slide decks, videos, code repos — into clean, portable markdown knowledge. The same artifacts also feed a Gemini Gem, Vertex AI Search, or NotebookLM.

**Knowledge format.** Hub content is an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog) (OKF v0.1) bundle: markdown + YAML frontmatter, `type` on every concept. Readable in any editor, renderable on GitHub, consumable by any OKF-aware agent.

**Build tool.** Claude Code (Enterprise). No Anthropic SDK, no API keys. LLM-heavy steps use the two-phase **runbook pattern**: a deterministic prepare phase writes a work list + runbook, then Claude Code executes it with its own vision/reasoning.

---

## Quick start — the hub

> New here? **[`GETTING-STARTED.md`](GETTING-STARTED.md)** is the 10-minute walkthrough: install → launch → tour → add your first page.

```bash
pip install -e '.[hub]'
python -m hub.app            # → http://127.0.0.1:8050  (--port / $ATLAS_PORT to change)
```

You get: channel navigation (Onboarding / Models / Compliance / Lessons / Tooling), per-model spaces with whitepaper + user guide + monitoring plan as tabs, full-text search with section deep-links, related-content recommendations, and a copilot sidebar whose every answer cites its source. Details and Posit Connect deployment: [`hub/README.md`](hub/README.md).

The repo ships with a seeded sample bundle under `content/` (two illustrative model spaces, real policy/lesson/tooling shapes) so the hub is usable on first run — replace samples with your material as it's ingested.

---

## Repository layout

```
atlas/
├── hub/            # the knowledge hub app (Dash UI + search/copilot engine)
├── content/        # OKF bundle: onboarding, models, compliance, lessons, tooling
├── raw/            # source material — GITIGNORED, confidential
│   ├── *.docx      #   whitepapers
│   ├── videos/     #   recordings + transcripts (.vtt/.srt/.txt)
│   └── decks/      #   .pptx
├── artifacts/      # intermediate outputs — GITIGNORED, disposable
├── knowledge/      # pipeline outputs — the portable gold
│   ├── docs/                 # one cleaned .md per whitepaper
│   ├── formula_index.md      # master cross-doc formula index
│   ├── indexes/              # cross-doc structured indexes (.md + .csv)
│   └── gem_bundle/           # Gem-ready consolidated files (≤10)
├── schemas/        # JSON schemas for structured extraction types
├── skills/         # pipeline logic — every step is a SKILL.md + helper
│   ├── docx-extract/         # whitepaper → skeleton + manifest
│   ├── formula-ocr/          # runbook: formula images → LaTeX
│   ├── md-normalize/         # skeleton + formulas → knowledge/docs/*.md
│   ├── formula-index/        # cross-doc formula index
│   ├── structured-extract/   # runbook: 5 structured index types
│   ├── structured-index/     # rollups to knowledge/indexes/
│   ├── qa-report/            # side-by-side HTML review
│   ├── bundle-for-gem/       # Gem-specific packaging
│   ├── video-ingest/         # runbook: video/transcript → OKF concept
│   ├── deck-ingest/          # runbook: pptx → OKF concept
│   ├── code-ingest/          # runbook: code repo → OKF Tool entry
│   └── knowledge-hub/        # run the hub, validate the OKF bundle
├── tests/          # engine + bundle contract tests (CI) and pipeline checks
└── docs/           # long-form build guidance
```

---

## How you operate it

Open Claude Code at the repo root and speak in natural language:

```
You: Run docx-extract on raw/Model_A_LGD_v3.2.docx, then prepare and execute
     the formula OCR runbook.
You: Ingest the monitoring training recording in raw/videos, channel onboarding.
You: Ingest the governance deck, channel compliance.
You: Document the pricing-toolkit repo in the hub.
You: Validate the bundle and start the hub.
```

Each request triggers the matching skill's `SKILL.md`. LLM steps (OCR, extraction, video/deck/code synthesis) run inside Claude Code — resumable, no external API.

## Execution order (new-repo checklist)

1. `pip install -e '.[dev,hub]'` (add `.[ingest]` for deck support), run `pytest` — the hub engine tests pass against the seeded sample bundle.
2. Start the hub, click around the sample content to learn the shapes.
3. Pilot the docx pipeline on one representative whitepaper (see [`docs/pipeline.md`](docs/pipeline.md)); its output in `knowledge/docs/` appears in the hub's Models channel automatically.
4. Replace sample model spaces in `content/models/` with your real model cards; keep `model_id` matching the pipeline `doc_id` so whitepapers attach.
5. Ingest decks, videos, and tool repos as they come up. Commit `content/` changes like code.
6. When feeding the Gem: `bundle-for-gem` → upload → tag `knowledge-vYYYY.MM.DD`.

---

## Deeper guidance

- [`hub/README.md`](hub/README.md) — hub architecture, deployment, copilot adapter, OKF content model.
- [`docs/operating-model.md`](docs/operating-model.md) — skills over scripts, runbook pattern, permissions.
- [`docs/pipeline.md`](docs/pipeline.md) — the docx pipeline, phase by phase.
- [`docs/gem-configuration.md`](docs/gem-configuration.md) — Gem system instructions, upload order, test set.
- [`docs/maintenance-and-roadmap.md`](docs/maintenance-and-roadmap.md) — versioning, update loop, runtime migrations.
- [`docs/compliance.md`](docs/compliance.md) — data classification, model risk linkage, things not to do.

## Portability guarantees

- Hub content is plain OKF markdown — no Dash-isms in the knowledge files; any runtime can consume `content/` and `knowledge/`.
- `knowledge/docs/` is always one clean markdown file per whitepaper; frontmatter fields are stable (they become Vertex metadata filters).
- Section anchors (`doc_id#section-slug`) are generated identically everywhere; citations never break across runtimes.
- Gem quirks live only in `gem_bundle/` and the Gem system prompt.

## License

Internal use only. Material under `raw/` may be confidential or restricted — confirm your firm's GenAI policy before uploading anywhere.
