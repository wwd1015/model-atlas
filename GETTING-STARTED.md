# Getting started with Atlas

This is the 10-minute path from a fresh clone to a running knowledge hub with your own content in it. For architecture and deployment depth, see [`hub/README.md`](hub/README.md); for the ingestion pipeline, see [`README.md`](README.md).

## 1. Install

```bash
git clone <your-repo-url> atlas && cd atlas
python -m venv .venv && source .venv/bin/activate
pip install -e '.[hub]'          # add ,ingest] if you'll ingest .pptx decks
```

Requires Python 3.10+. No API keys, no external services — everything runs on your machine.

## 2. Launch

```bash
python -m hub.app
```

Open **http://127.0.0.1:8050**. That's it — the hub starts with a seeded sample bundle so every feature is visible immediately.

Port taken or want a different one? It's a parameter:

```bash
python -m hub.app --port 8080        # CLI flag
ATLAS_PORT=8080 python -m hub.app    # or env var (flag wins)
```

Other knobs: `--host`, `--no-debug`, `ATLAS_CONTENT_DIR`, `ATLAS_KNOWLEDGE_DOCS` (see `.env.example`).

## 3. Take the tour

Five things to try, in order:

1. **Search** (box on the home page or navbar): try `PSI threshold` — results deep-link to the exact section of the exact document.
2. **Open a model space**: *Models → CRE PD Model v2.0* — whitepaper, user guide, and monitoring plan live as tabs on one page.
3. **Open the 💬 Copilot** (top right): ask *"How do we handle NPI data?"*, *"what is PSI?"*, or *"who owns the CRE PD model?"* — every answer cites its source with a 📎 link. If you have the **Claude Code CLI** installed (you probably do — it's this repo's build tool), the copilot automatically uses your local Claude to write the answers (badge shows ⚡ Claude Code); without it, answers are extractive quotes. Either way it's grounded in hub content only — no API keys involved.
4. **Follow the graph**: on any doc, the right rail shows *On this page*, *Related*, and *Linked from* (backlinks).
5. **See an ingested page**: *Models → Model Monitoring Town Hall — June 2026* was generated from a video transcript by the `video-ingest` skill (source in `examples/`).

## 4. Add your first page (2 minutes)

Content is just markdown files with a YAML header (Google's OKF format). Create one in the channel folder where it belongs:

```bash
cat > content/tooling/my-first-tool.md <<'EOF'
---
type: Tool
title: My First Tool
description: One sentence saying what it does and who it's for.
tags: [tooling, demo]
timestamp: 2026-07-01
---

# My First Tool

What it does, how to run it. Link other pages with [[glossary]]-style
wiki-links — Atlas resolves them and builds backlinks automatically.
EOF
```

Then check it and restart:

```bash
python skills/knowledge-hub/helper.py validate   # catches bad frontmatter
python -m hub.app
```

Your page is now browsable, searchable, recommended, and citable by the copilot. Rules of thumb:

- `type` is the only **required** frontmatter field (`Guide`, `Policy`, `Tool`, `Lesson Learned`, `Model Card`, … — pick what fits).
- The **channel = the folder**: `content/compliance/…` shows up under Compliance.
- A **new model space** is a folder: `content/models/<slug>/` with `model.md` (the card) + `whitepaper.md` + `user-guide.md` + `monitoring-plan.md`.
- Commit content changes like code — PRs, reviews, history.

## 5. Ingest instead of writing (videos, decks, code, whitepapers)

Have source material? Let the pipeline draft the page. In Claude Code at the repo root, just ask:

```
Ingest the recording in raw/videos, channel onboarding.
Ingest the deck raw/decks/governance.pptx, channel compliance.
Document the ~/projects/pricing-toolkit repo in the hub.
Run docx-extract on raw/Model_A_LGD_v3.2.docx.        # whitepaper pipeline
```

Each runs a two-phase skill: a deterministic *prepare* step you can inspect, then Claude Code executes the runbook and writes the OKF page. Try it right now with the shipped placeholders — see [`examples/README.md`](examples/README.md).

## 6. Share it with the team

- **Posit Connect**: `rsconnect deploy dash . --entrypoint hub.app:app --title "Atlas"` (include `content/` and `knowledge/` in the bundle).
- **Any WSGI host**: `gunicorn hub.app:server`.
- **Just your machine**: `python -m hub.app --host 0.0.0.0` and share your IP (mind your network policy).

## Troubleshooting

| Symptom | Fix |
|---|---|
| New page doesn't appear | Restart the app (content loads at startup); then `python skills/knowledge-hub/helper.py validate` — files with broken frontmatter are skipped |
| "Address already in use" | Another app owns the port — `python -m hub.app --port 8080` |
| Page renders but formulas don't | Use `$$ … $$` LaTeX blocks; MathJax renders them |
| Copilot says it can't find something that exists | The copilot only answers when retrieval coverage is strong — check the page is indexed (searchable) and phrased with the terms you're asking with |
| Copilot slow or badge says 📎 offline extractive | ⚡ mode needs the `claude` CLI on PATH; check `claude --version`. Force a mode with `ATLAS_COPILOT=claude` or `=extractive`; timeout via `ATLAS_COPILOT_TIMEOUT` |
| Deck ingest fails | `pip install -e '.[ingest]'` (python-pptx) |
