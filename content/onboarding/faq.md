---
type: FAQ
title: New joiner FAQ
description: The questions every new analyst asks in the first month, with short answers and links to the full context.
tags: [onboarding, faq]
timestamp: 2026-07-01
---

# New joiner FAQ

## Where do I find the documentation for a model?

Every model has one space in the Models channel containing its whitepaper, user guide, and monitoring plan as tabs. Start from the [models index](/models/index.md). If a document is missing there, it doesn't exist — ask the model owner, don't go hunting shared drives.

## What's the difference between the whitepaper, the user guide, and the monitoring plan?

- **Whitepaper** — why the model exists and how it works: methodology, assumptions, limitations, validation history. The authoritative document.
- **User guide** — how to *run* it: inputs, steps, checks, outputs. Procedure, not theory.
- **Monitoring plan** — how we know it still works: metrics, thresholds, frequency, escalation.

## Can I use customer data on my laptop?

Read [[npi-data-handling]] first — short version: **no raw NPI outside approved environments**, ever. The approved patterns are listed there.

## Can I paste code or documents into an AI assistant?

Only under the rules in [[genai-acceptable-use]]. Approved enterprise tools yes (with data-class limits); public tools no.

## A number in a monitoring report looks wrong. What do I do?

Don't fix it silently. Raise it to the model owner and log it — silent fixes destroyed audit trails before; that's literally lesson [[2025-vendor-data-gap]].

## Who approves a model change?

Depends on materiality — the governance section of the model's whitepaper defines tiers. [[model-risk-101]] explains the framework in plain language.

## How do I add or fix content in Atlas?

Atlas content is a folder of markdown files (OKF format) in Git. Edit or add a file with frontmatter (`type`, `title`, `description`, `tags`), open a PR, done. The hub picks it up on restart. See [[atlas-pipeline]] for how source documents (docx, decks, video, code) get converted in.
