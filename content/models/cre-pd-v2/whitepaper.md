---
type: Whitepaper
title: CRE PD Model v2.0 — Whitepaper
description: Methodology, assumptions, and limitations of the CRE PD model. Sample document.
tags: [model, credit-risk, cre, pd, sample]
owner: J. Rivera (Credit Risk Analytics)
timestamp: 2026-07-01
doc_id: cre_pd_v2
prompt_version: n/a (hand-authored sample)
---

# CRE PD Model v2.0 — Whitepaper

> **Sample document.** Real whitepapers are produced by the docx pipeline into `knowledge/docs/` and attach to this space automatically.

## Purpose

Provide 12-month point-in-time PD estimates for CRE obligors, supporting underwriting, pricing, and expected-loss aggregation:

$$EL = PD \times LGD \times EAD$$

## Methodology

Logistic regression on obligor and property-level factors:

$$PD_i = \frac{1}{1 + e^{-(\beta_0 + \beta_1 \cdot DSCR_i + \beta_2 \cdot LTV_i + \beta_3 \cdot VAC_m + \beta_4 \cdot NOI\Delta_i)}}$$

where `DSCR` is debt-service coverage ratio, `LTV` loan-to-value, `VAC_m` market vacancy for the property's metro, and `NOIΔ` trailing-12-month net-operating-income change.

## Key assumptions

- **A-001** — Market vacancy is a sufficient proxy for local demand shocks. *Reviewed quarterly; see [[2024-assumption-drift]] for why.*
- **A-002** — Default definition is 90+ DPD or nonaccrual, aligned to the regulatory definition.
- **A-003** — Development sample (2015–2023) spans at least one full CRE cycle.

## Limitations

- Thin data in specialty property types (self-storage, data centers) — scores there carry a conservatism overlay.
- Not calibrated for construction loans; those route to the project-finance model.
- Rate-shock sensitivity is assessed via overlay analysis, not embedded in the regression.

## Validation history

| Date | Type | Outcome |
|------|------|---------|
| 2024-09 | Initial validation | Approved with 2 findings (closed) |
| 2025-03 | Annual | Approved |
| 2026-03 | Annual | Approved; monitoring threshold for PSI tightened |
