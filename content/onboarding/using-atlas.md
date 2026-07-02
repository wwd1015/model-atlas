---
type: Guide
title: Using Atlas
description: How to get the most out of this hub — search tricks, the copilot, the knowledge graph — and how to add or fix a page yourself.
tags: [onboarding, atlas, how-to]
owner: Atlas maintainer
timestamp: 2026-07-01
---

# Using Atlas

Atlas is the team's front door to knowledge. This page is the two-minute usage guide; if you want to run your own copy locally, see the repo's `GETTING-STARTED.md`.

## Finding things

- **Search** (navbar, or the big box on Home) indexes every *section* of every page — results link to the exact heading, not just the document. Filter by channel on the results page.
- **Browse** by channel: [Onboarding](/onboarding/index.md), [Models](/models/index.md), [Compliance](/compliance/index.md), [Lessons](/lessons/index.md), [Tooling](/tooling/index.md). Every model has one space with its whitepaper, user guide, and monitoring plan as tabs.
- **Follow the graph.** Each page's right rail shows *Related* (content similarity) and *Linked from* (backlinks). Two clicks usually beat one search.

## Asking the copilot

The 💬 button (top right) opens the copilot. It answers from hub content only and links every claim to its source — if there's no 📎 citation, treat it as navigation help, not fact. The badge at the top shows the backend: **⚡ Claude Code** means your local Claude writes the answers (follow-up questions work — it keeps the conversation context); **📎 offline extractive** means it quotes the source sections directly.

Works well:
- *"How do we handle NPI data?"* — policy questions land on the policy section.
- *"what is PSI?"* — glossary terms get instant definitions.
- *"who owns the VA hedging model?"* — model metadata questions get structured answers.
- It knows which page you're reading — asking on a model page biases answers to that model.

It deliberately says "I couldn't find anything" rather than guessing. That's a feature — see [[genai-acceptable-use]] for why.

## Adding or fixing a page

Atlas content is markdown files in Git (`content/`, one folder per channel), in Google's OKF format — a YAML header with at least a `type:` field, then normal markdown.

1. Copy a similar page in the right channel folder (there's a [[lesson-template]] for lessons).
2. Fill the header: `type`, `title`, `description`, `tags`, `timestamp`.
3. Cross-link generously with `[[wiki-links]]` — links are what make the graph useful.
4. Open a PR. After merge, the hub picks it up on restart.

Spotted an error on a page? Same process — or flag it to the owner listed on the page. For governed documents (whitepapers in the Models channel produced by the pipeline), **don't edit the page** — the fix goes in the source document and gets re-ingested; see [[atlas-pipeline]].

## Ingesting bigger things

Recordings, decks, whitepapers, and code repos don't need hand-writing — the [[atlas-pipeline]] converts them. Drop the source in `raw/` and ask Claude Code to ingest it; a draft page (like the [town hall notes](/models/model-monitoring-town-hall.md)) comes out the other end for you to review.
