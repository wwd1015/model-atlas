---
type: User Guide
title: CRE PD Model v2.0 — User Guide
description: How to run a monthly scoring cycle — inputs, procedure, checks, outputs. Sample document.
tags: [model, credit-risk, cre, runbook, sample]
owner: J. Rivera (Credit Risk Analytics)
timestamp: 2026-07-01
---

# CRE PD Model v2.0 — User Guide

> **Sample document** illustrating the user-guide shape: procedure, not theory. Theory lives in the [whitepaper](/models/cre-pd-v2/whitepaper.md).

## Inputs

| Input | Source | Refresh | NPI? |
|-------|--------|---------|------|
| Loan servicing extract | Servicing warehouse | Monthly, BD+2 | **Yes** — handle per [[npi-data-handling]] |
| Property NOI feed | Asset management system | Monthly | No |
| Market vacancy index | Vendor feed | Quarterly | No |

## Procedure

1. Confirm all three inputs landed and pass row-count reconciliation (±2% vs prior month). A silent vendor short-load is exactly what caused [[2025-vendor-data-gap]] — do not skip this.
2. Run the scoring job in the approved environment. Raw NPI never leaves it.
3. Review the exception report: obligors with missing DSCR or stale NOI (>6 months) are scored with the conservative fallback and must be listed in the cycle memo.
4. Compare score distribution to prior month — PSI computed automatically; anything above 0.10 goes in the memo, above 0.25 escalates per the [monitoring plan](/models/cre-pd-v2/monitoring-plan.md).
5. Publish scores to the risk mart and file the cycle memo.

## Outputs

- Obligor-level PD table (risk mart, versioned by cycle date).
- Cycle memo: input reconciliation, exceptions, distribution shift, sign-off.

## Common issues

- **Vendor vacancy file late** — score with prior quarter's index and flag in the memo; do not substitute an unapproved source.
- **New metro appears in book** — vacancy mapping table needs a row; request from the model owner, don't guess.
