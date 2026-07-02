---
type: Model Card
title: VA Hedging Model v1.3
description: Dynamic hedging model for the variable annuity guarantee block. Sample space — replace with your real model.
tags: [model, alm, variable-annuity, hedging, sample]
owner: M. Chen (ALM & Hedging)
timestamp: 2026-07-01
model_id: va_hedge_v1
family: alm
status: In production
validation_status: Validated 2025-11 (annual)
materiality_tier: Tier 1
---

# VA Hedging Model v1.3

> **Sample space.** Illustrative content showing a second model family (ALM/insurance) alongside credit risk.

Computes Greeks for the variable annuity guarantee block (GMxB riders) and generates daily hedge rebalancing targets for the equity and rates overlay.

## At a glance

| | |
|---|---|
| Owner | M. Chen (ALM & Hedging) |
| Status | In production since 2023-05; v1.3 deployed 2025-12 |
| Validation | Annual; last completed 2025-11 |
| Materiality | Tier 1 — full governance per [[model-risk-101]] |
| Upstream data | Policy inforce file, market data snap, actuarial assumption tables |
| Downstream users | Hedging desk, ALM committee, statutory reporting |

## Artifacts

- [Whitepaper](/models/va-hedge-v1/whitepaper.md)
- [User guide](/models/va-hedge-v1/user-guide.md)
- [Monitoring plan](/models/va-hedge-v1/monitoring-plan.md)

## Known limitations

- Policyholder behavior (lapse/withdrawal) assumptions are the dominant model risk — see whitepaper §Assumptions and the behavior-drift metric in the monitoring plan.
- Intraday market moves between the snap and execution are borne by the desk, not the model.
