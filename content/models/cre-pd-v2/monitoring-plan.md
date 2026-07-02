---
type: Monitoring Plan
title: CRE PD Model v2.0 — Monitoring Plan
description: Metrics, thresholds, frequency, and escalation for ongoing performance monitoring. Sample document.
tags: [model, credit-risk, cre, monitoring, sample]
owner: J. Rivera (Credit Risk Analytics)
timestamp: 2026-07-01
---

# CRE PD Model v2.0 — Monitoring Plan

> **Sample document.** Thresholds shown are illustrative.

## Metrics and thresholds

| Metric | What it checks | Green | Amber | Red | Frequency |
|--------|----------------|-------|-------|-----|-----------|
| AUC (12m rolling) | Rank-ordering power | ≥ 0.72 | 0.68–0.72 | < 0.68 | Quarterly |
| Calibration ratio (actual/predicted defaults) | Level accuracy | 0.8–1.2 | 0.6–0.8 or 1.2–1.5 | outside | Quarterly |
| PSI vs development sample | Population drift | < 0.10 | 0.10–0.25 | > 0.25 | Monthly |
| Input completeness | Data quality | ≥ 98% | 95–98% | < 95% | Monthly |
| Override rate | Judgmental overrides of model score | < 5% | 5–10% | > 10% | Quarterly |

## Escalation

- **Amber** — note in the cycle memo; model owner reviews within 10 business days.
- **Red** — immediate notification to model owner and MRM liaison; remediation plan within 30 days; interim conservatism overlay if scores remain in use. Framework context: [[model-risk-101]].
- Two consecutive ambers on the same metric escalate as red.

## Annual review

Backtesting on the full realized-default window, champion–challenger comparison if a candidate exists, assumption re-affirmation (each A-NNN in the [whitepaper](/models/cre-pd-v2/whitepaper.md) explicitly re-confirmed or revised — the control added after [[2024-assumption-drift]]).
