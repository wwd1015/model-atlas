---
type: Tool
title: Gem knowledge pack
description: The consolidated RAG bundle uploaded to the Gemini Gem runtime — built by the bundle-for-gem skill from knowledge/ artifacts.
tags: [tooling, gem, rag, knowledge-pack]
owner: Atlas maintainer
timestamp: 2026-07-01
---

# Gem knowledge pack

A Gem-ready consolidation of the knowledge base: `knowledge/gem_bundle/` groups the cleaned whitepapers and cross-doc indexes into ≤10 upload files per the Gem's constraints.

## Key facts

- Built by the `bundle-for-gem` skill; grouping rules live in `skills/bundle-for-gem/grouping.yaml`.
- **Gem-specific by design** — Vertex AI Search and NotebookLM consume `knowledge/docs/` and `knowledge/indexes/` directly; only the Gem needs bundling.
- Versioned as `knowledge-vYYYY.MM.DD` Git tags; the Gem's system prompt cites the pack version in every answer (version-drift control — see [[genai-acceptable-use]]).

## Relationship to the hub

The hub and the Gem are two runtimes over the same knowledge. The hub reads `content/` + `knowledge/docs/` live; the Gem gets a frozen, bundled snapshot. Lessons like [[2025-vendor-data-gap]] apply here too: after every re-bundle, spot-check that the pack actually contains what the manifest says it does.
