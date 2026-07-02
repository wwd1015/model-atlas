---
type: Whitepaper
title: VA Hedging Model v1.3 — Whitepaper
description: Methodology, assumptions, and limitations of the VA guarantee hedging model. Sample document.
tags: [model, alm, variable-annuity, hedging, sample]
owner: M. Chen (ALM & Hedging)
timestamp: 2026-07-01
doc_id: va_hedge_v1
prompt_version: n/a (hand-authored sample)
---

# VA Hedging Model v1.3 — Whitepaper

> **Sample document** for the second model space.

## Purpose

Value the embedded guarantees (GMDB, GMWB) in the variable annuity block and produce risk sensitivities (Greeks) that drive the dynamic hedge program.

## Methodology

Risk-neutral Monte Carlo valuation of guarantee cash flows over policy-level projections:

$$V_0 = \mathbb{E}^{\mathbb{Q}}\left[\sum_{t} e^{-\int_0^t r_s\,ds}\, CF_t(S_t, B_t, \lambda_t)\right]$$

where `S_t` is the account value path, `B_t` the guarantee base, and `λ_t` the behavior-adjusted decrement intensity. Greeks are computed by bump-and-revalue on 10k paths with common random numbers.

## Key assumptions

- **A-001** — Dynamic lapse: lapse rates scale with guarantee moneyness via the calibrated dynamic-lapse multiplier. *The single largest sensitivity — reviewed semi-annually.*
- **A-002** — Withdrawal utilization follows the experience-study cohort table (2024 study).
- **A-003** — Volatility surface is interpolated SVI, fit daily from the market snap.

## Limitations

- Behavior assumptions extrapolate poorly in unprecedented market regimes; the monitoring plan's behavior-drift metric is the early-warning control.
- Basis risk between hedge instruments and separate-account funds is measured but not optimized by this model version.

## Validation history

| Date | Type | Outcome |
|------|------|---------|
| 2023-04 | Initial validation | Approved with 3 findings (closed) |
| 2024-11 | Annual | Approved |
| 2025-11 | Annual (v1.3) | Approved; new behavior-drift metric mandated |
