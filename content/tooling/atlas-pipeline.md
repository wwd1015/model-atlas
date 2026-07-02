---
type: Tool
title: Atlas ingestion pipeline
description: Claude Code skills that convert source material — Word whitepapers, slide decks, videos, code repos — into OKF markdown knowledge.
tags: [tooling, pipeline, ingestion, okf]
owner: Atlas maintainer
timestamp: 2026-07-01
resource: https://github.com/your-org/atlas
---

# Atlas ingestion pipeline

The pipeline half of this repo: a set of Claude Code **skills** under `skills/` that turn source documents into clean, portable markdown. No API keys, no SDK — Claude Code is the executor; LLM-heavy steps use the two-phase runbook pattern (deterministic *prepare*, agent-driven *execute*).

## What it ingests

| Source | Skill(s) | Output |
|--------|----------|--------|
| Word whitepapers (`.docx`, formula images) | `docx-extract` → `formula-ocr` → `md-normalize` → `formula-index` | `knowledge/docs/*.md` + formula index |
| Slide decks (`.pptx`) | `deck-ingest` (prepare + execute) | OKF concept in `content/` |
| Videos (with transcripts) | `video-ingest` (prepare + execute) | OKF concept in `content/` |
| Code repos / tools | `code-ingest` (prepare + execute) | OKF Tool entry in `content/tooling/` |
| Structured facts (metrics, assumptions, governance…) | `structured-extract` → `structured-index` | Cross-doc indexes in `knowledge/indexes/` |

## How to run it

Open Claude Code at the repo root and ask in natural language — "ingest the deck at raw/decks/kickoff.pptx" or "run docx-extract on raw/Model_A.docx". Each skill's `SKILL.md` defines its triggers, inputs, outputs, and procedure.

## Design guarantees

- Everything lands as markdown + YAML frontmatter (OKF) — portable across the hub, the Gem, Vertex AS, NotebookLM.
- Section anchors (`doc_id#section-slug`) are stable; citations never break across runtimes.
- Every structured record keeps a `verbatim_quote` — the audit trail per [[genai-acceptable-use]].
