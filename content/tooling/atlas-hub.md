---
type: Tool
title: Atlas hub
description: This app — the team knowledge hub. Dash UI with channel navigation, full-text search, related-content recommendations, and a grounded copilot sidebar.
tags: [tooling, hub, dash, search, copilot]
owner: Atlas maintainer
timestamp: 2026-07-01
---

# Atlas hub

The front door to the team's knowledge: the app you are reading this in.

## What it does

- **Channels** — onboarding, models, compliance, lessons learned, tooling. Model spaces gather whitepaper / user guide / monitoring plan in one place.
- **Search** — full-text (SQLite FTS5, BM25) across every section of every concept, with per-channel filtering and deep links to the exact section.
- **Copilot** — the sidebar assistant. When the Claude Code CLI is installed (the default assumption for Atlas users), your local Claude synthesizes answers over passages the hub retrieves — grounded, citing every claim, in line with [[genai-acceptable-use]]. Without the CLI it falls back to offline extractive answers; an enterprise LLM adapter can also be plugged in at deploy time. No API keys in any mode.
- **Second-brain graph** — wiki-links between concepts produce backlinks and power related-content recommendations on every page.

## How to run it

```bash
pip install -e '.[hub]'
python -m hub.app          # http://127.0.0.1:8050
```

Deploys to Posit Connect as a Dash app (`hub.app:app`). Content is the OKF bundle in `content/` plus pipeline whitepapers in `knowledge/docs/` — restart (or call the refresh endpoint) to pick up new content.

## Adding content

Write a markdown file with `type`, `title`, `description`, `tags` frontmatter in the right channel folder; open a PR. Or let the [[atlas-pipeline]] generate it from a source document.
