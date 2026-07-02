# Atlas hub — the app

The team knowledge hub: Dash UI + local search/copilot engine over the OKF content bundle (`content/`) and pipeline whitepapers (`knowledge/docs/`). Runs locally or on Posit Connect. **No API keys, no external calls** — search and copilot are fully offline.

## Run locally

```bash
pip install -e '.[hub]'
python -m hub.app                    # → http://127.0.0.1:8050
python -m hub.app --port 8080        # any port, as a parameter
```

Env knobs: `ATLAS_PORT` (default 8050; the `--port` flag wins), `ATLAS_HOST`, `ATLAS_DEBUG`, `ATLAS_CONTENT_DIR`, `ATLAS_KNOWLEDGE_DOCS`.

## What's in the UI

- **Home** — global search, channel cards, "Start here" onboarding trail, recently updated, and "Recommended for you" (based on your session's reading history).
- **Channels** — Onboarding · Models · Compliance · Lessons Learned · Tooling.
- **Model spaces** (`/model/<id>`) — one page per model with tabs: Overview (model card), Whitepaper, User Guide, Monitoring Plan. Pipeline-produced whitepapers from `knowledge/docs/` attach automatically when `doc_id` matches the space's `model_id`.
- **Doc pages** (`/doc/<id>`) — rendered markdown (LaTeX via MathJax) with anchored sections, an "On this page" TOC, related concepts, and backlinks — the second-brain graph.
- **Search** (`/search`) — SQLite FTS5 / BM25 over every section, channel filters, snippets deep-linking to `#section-anchors`.
- **Copilot** (sidebar, every page) — ask in plain language; answers are *extractive and grounded*: the best sentences from the best sections, each claim linked to its source anchor. Glossary and "who owns X" questions get structured answers. It knows what page you're reading and gently prefers it.

## Architecture

```
hub/
├── app.py              # Dash app, router, callbacks (entrypoints: app / server)
├── config.py           # paths, channels registry, env
├── engine/
│   ├── loader.py       # OKF bundle + knowledge docs → Corpus (sections, wiki-links, backlinks)
│   ├── search.py       # SQLite FTS5 (BM25, section-level) + pure-Python fallback
│   ├── recommend.py    # TF-IDF cosine + link-graph boost → related / for-you
│   ├── copilot.py      # retrieval → extractive grounded answer; optional LLM adapter
│   └── state.py        # lazy singletons, refresh()
├── ui/
│   ├── components.py   # cards, badges, panels, markdown rendering (prefix-aware links)
│   └── views.py        # home / channel / doc / model / search
└── assets/atlas.css
```

The corpus loads at process start. After editing content, restart the app (or call `hub.engine.state.refresh()`).

## Deploy to Posit Connect

```bash
pip install rsconnect-python
rsconnect deploy dash . --entrypoint hub.app:app --title "Atlas"
```

Notes:
- The app is prefix-aware (`requests_pathname_prefix`), so it works under Connect's `/content/<guid>/` paths.
- Include `content/` and `knowledge/docs/` in the deploy bundle — the engine reads them from disk at startup.
- Any WSGI host also works: `gunicorn hub.app:server`.

## Copilot backends

The copilot picks its synthesis backend at startup (footer + sidebar badge show which):

1. **Claude Code (default when available).** If the `claude` CLI is on PATH — true for anyone already using Claude Code, which Atlas assumes — answers are synthesized by your local, already-authenticated Claude via headless `claude -p`. All tools are disallowed for the call; Claude sees only the retrieval passages Atlas hands it, must quote numbers verbatim, and cites with the passage URLs. Still no API keys and no SDK in this repo — the CLI is the user's own tool.
2. **Offline extractive (automatic fallback).** No CLI, a timeout, or `ATLAS_COPILOT=extractive` → grounded quote-and-link answers, fully self-contained. The hub never breaks without Claude.
3. **Custom enterprise gateway (deploy-time).** `ATLAS_COPILOT_ADAPTER="your_pkg.adapter:make_adapter"`, where `make_adapter()` returns an object with `.generate(question, passages, history=None) -> str`. Takes precedence over both modes above.

Either way, **retrieval and citations stay Atlas-side** — the backend only writes prose over passages Atlas selected. Knobs: `ATLAS_COPILOT` (`auto`/`claude`/`extractive`), `ATLAS_CLAUDE_MODEL` (optional model override), `ATLAS_COPILOT_TIMEOUT` (seconds, default 90).

## Content model (OKF)

`content/` is a Google [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog) v0.1 bundle: every concept is a markdown file with YAML frontmatter (`type` required; `title`, `description`, `tags`, `timestamp` recommended). Top-level directories are channels. `[[wiki-links]]` are resolved by the loader and power backlinks + recommendations. Validate with:

```bash
python skills/knowledge-hub/helper.py validate
```
