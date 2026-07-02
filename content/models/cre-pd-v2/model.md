---
type: Model Card
title: CRE PD Model v2.0
description: Probability-of-default model for the commercial real estate lending book. Sample space — replace with your real model.
tags: [model, credit-risk, cre, pd, sample]
owner: J. Rivera (Credit Risk Analytics)
timestamp: 2026-07-01
model_id: cre_pd_v2
family: credit-risk
status: In production
validation_status: Validated 2026-03 (annual)
materiality_tier: Tier 1
---

# CRE PD Model v2.0

> **Sample space.** This model card and its artifacts are illustrative — they show the shape a real model space takes in Atlas.

Estimates 12-month probability of default for commercial real estate obligors. Scores feed underwriting decisions, risk-based pricing, and portfolio expected-loss aggregation.

## At a glance

| | |
|---|---|
| Owner | J. Rivera (Credit Risk Analytics) |
| Status | In production since 2024-11 |
| Validation | Annual; last completed 2026-03 |
| Materiality | Tier 1 — full governance per [[model-risk-101]] |
| Upstream data | Loan servicing extract, property NOI feed, market vacancy index |
| Downstream users | Underwriting, portfolio risk, CECL reserving |

## Artifacts

- [Whitepaper](/models/cre-pd-v2/whitepaper.md) — methodology, assumptions, limitations.
- [User guide](/models/cre-pd-v2/user-guide.md) — how to run a scoring cycle.
- [Monitoring plan](/models/cre-pd-v2/monitoring-plan.md) — metrics, thresholds, escalation.

## Known limitations

- Calibrated on post-2015 data; performance in a prolonged rate shock is monitored via the sensitivity overlay (see whitepaper §Limitations).
- Related history: [[2024-assumption-drift]] — the vacancy-assumption drift found in this model family's monitoring.
