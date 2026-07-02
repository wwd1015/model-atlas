---
okf_version: "0.1"
title: Atlas knowledge bundle
description: OKF bundle backing the Atlas knowledge hub — onboarding, models, compliance, lessons learned, tooling.
---

# Atlas knowledge bundle

This directory is an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog) (OKF v0.1) bundle. Every non-reserved `.md` file is a *concept*: YAML frontmatter with a required `type`, followed by a markdown body. The Atlas hub renders it; any OKF-aware agent or search tool can consume it directly.

## Channels

- [Onboarding](/onboarding/index.md) — role orientation, first 90 days, FAQ, glossary, who to ask.
- [Models](/models/index.md) — one space per model: whitepaper, user guide, monitoring plan.
- [Compliance](/compliance/index.md) — NPI data handling, GenAI acceptable use, model risk basics.
- [Lessons Learned](/lessons/index.md) — post-mortems and case studies.
- [Tooling](/tooling/index.md) — catalog of tools the team has built.

## Conventions

- Concept ids are bundle-relative paths without extension (e.g. `onboarding/welcome`).
- Cross-links may use `[[wiki-links]]`; the hub resolves them and computes backlinks.
- Whitepapers produced by the pipeline live in `knowledge/docs/` and are surfaced
  in the Models channel automatically — never duplicated into this bundle.
