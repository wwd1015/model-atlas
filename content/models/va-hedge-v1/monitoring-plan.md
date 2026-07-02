---
type: Monitoring Plan
title: VA Hedging Model v1.3 — Monitoring Plan
description: Hedge effectiveness, behavior drift, and valuation stability metrics with thresholds and escalation. Sample document.
tags: [model, alm, variable-annuity, monitoring, sample]
owner: M. Chen (ALM & Hedging)
timestamp: 2026-07-01
---

# VA Hedging Model v1.3 — Monitoring Plan

> **Sample document.** Thresholds illustrative.

## Metrics and thresholds

| Metric | What it checks | Green | Amber | Red | Frequency |
|--------|----------------|-------|-------|-----|-----------|
| Hedge effectiveness (P&L offset ratio) | Program performance | ≥ 90% | 80–90% | < 80% | Monthly |
| Unexplained P&L residual | Attribution quality | < 5% of gross | 5–10% | > 10% | Weekly |
| Behavior drift (actual vs assumed lapse, rolling 6m) | Assumption validity | within ±10% | ±10–20% | beyond ±20% | Quarterly |
| Valuation stability (seed sensitivity) | Monte Carlo noise | < 0.5% of V₀ | 0.5–1% | > 1% | Quarterly |
| Run timeliness | Operational | ≥ 99% on-time | 97–99% | < 97% | Monthly |

## Escalation

- **Amber** — cycle memo note; model owner review within 5 business days (faster than quarterly-cycle models — this one trades daily).
- **Red** — same-day notification to model owner, desk head, and MRM liaison; remediation plan within 15 days. Framework: [[model-risk-101]].

## Annual review

Full behavior experience study refresh, champion–challenger on the dynamic-lapse specification, and back-population of hedge effectiveness across the year. Each assumption **A-NNN** in the [whitepaper](/models/va-hedge-v1/whitepaper.md) is re-affirmed in writing.
