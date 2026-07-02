---
type: Guide
title: Model risk 101
description: The model governance framework in plain language — tiers, validation, monitoring, and what it means for your daily work.
tags: [compliance, mrm, governance]
owner: MRM Liaison
timestamp: 2026-07-01
---

# Model risk 101

Model risk is the risk of loss from decisions based on incorrect or misused model outputs. The framework (SR 11-7 lineage) sounds bureaucratic until you see it as three questions asked continuously: *Is the model built right? Is it still right? Is it being used right?*

## Materiality tiers

| Tier | Meaning | Governance |
|------|---------|------------|
| Tier 1 | Material to financial statements or customer outcomes | Annual validation, full monitoring plan, change control |
| Tier 2 | Meaningful but bounded impact | Biennial validation, core monitoring |
| Tier 3 | Low impact / advisory | Registration + periodic self-assessment |

Both sample spaces ([CRE PD](/model/cre-pd-v2), [VA hedging](/model/va-hedge-v1)) are Tier 1 — that's why each carries a full monitoring plan.

## The lifecycle

1. **Development** — documented in the whitepaper: methodology, assumptions (each with an ID like `A-001`), limitations. If it isn't written down, it doesn't exist.
2. **Validation** — independent (second line) challenge before use, then on the tier's cycle.
3. **Monitoring** — the monitoring plan defines metrics, thresholds, escalation. Amber/red states carry deadlines, not vibes.
4. **Change control** — material changes re-validate; the change memo says what changed and why.
5. **Retirement** — decommissioned models keep their documentation; audits ask about dead models too.

## What this means for you day to day

- Every number you publish should trace to a governed doc and a run you can reproduce.
- Assumptions are living objects: re-affirmed annually by ID. [[2024-assumption-drift]] is what happens when they quietly aren't.
- Overrides are allowed but logged — the override *rate* is itself a monitored metric.
- Tools that inform model decisions (including AI tools — see [[genai-acceptable-use]]) get documented proportionally to their influence.
