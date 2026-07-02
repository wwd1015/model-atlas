---
type: Policy
title: GenAI acceptable use
description: What may and may not go into AI tools, by data classification — and how AI outputs must be treated.
tags: [compliance, genai, ai, policy]
owner: Compliance Officer
timestamp: 2026-07-01
---

# GenAI acceptable use

AI assistants are approved tools here — Atlas itself has a copilot, and the ingestion pipeline runs on an enterprise AI agent. The rules are about *what goes in* and *how outputs are treated*.

## What may go in

| Data class | Public AI tools | Approved enterprise AI |
|------------|----------------|------------------------|
| Public information | Yes | Yes |
| Internal (non-confidential) | No | Yes |
| Confidential (whitepapers, methodology) | No | Yes, if the tool is approved for confidential data |
| **NPI / customer data** | **Never** | **Never**, unless explicitly approved for that class — see [[npi-data-handling]] |

When in doubt about a tool's approval status, ask before pasting — [[who-to-ask]] routes GenAI questions.

## How outputs must be treated

- **AI output is a draft, not a source.** Anything factual must trace to a governed document before it's relied on. The Atlas copilot enforces this by linking every claim to its source section.
- **Quote, don't paraphrase, for formulas and thresholds.** LLMs paraphrase plausibly and wrongly; a transposed subscript in a formula is invisible in review. This is why the pipeline keeps `verbatim_quote` fields in every structured extraction.
- **Model-adjacent use must be documented.** If an AI tool informs a model risk decision, it becomes a model-adjacent tool under [[model-risk-101]] — log the usage.
- **Version what you relied on.** Answers grounded in a knowledge pack should carry its version (Atlas surfaces this in the footer).

## Non-negotiables

- No NPI in any prompt, ever.
- No uploading whitepapers to personal AI accounts.
- No silent AI-generated changes to governed documents — every change goes through review like any other edit.
