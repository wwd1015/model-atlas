---
type: User Guide
title: VA Hedging Model v1.3 — User Guide
description: Daily hedge-cycle procedure — snap, run, review, publish. Sample document.
tags: [model, alm, variable-annuity, runbook, sample]
owner: M. Chen (ALM & Hedging)
timestamp: 2026-07-01
---

# VA Hedging Model v1.3 — User Guide

> **Sample document.** Daily-cadence procedure; theory lives in the [whitepaper](/models/va-hedge-v1/whitepaper.md).

## Daily cycle

1. **Market snap (16:15)** — confirm the market data snapshot is complete: equity levels, swap curve, vol surface inputs. A stale surface fails the run downstream, so check the timestamp *now*.
2. **Inforce check** — policy file is weekly; the daily run uses the latest weekly file plus new-business adjustments. Reconcile policy counts vs prior day (±0.5%).
3. **Run valuation** — 10k paths, policy-level. Runtime ~40 min in the approved grid environment. The inforce file contains **NPI** — it never leaves the grid; see [[npi-data-handling]].
4. **Review Greeks** — day-over-day delta/rho moves outside the tolerance bands (monitoring plan §Thresholds) require a written rationale before publishing (market move, inforce change, or assumption update — one of the three, named).
5. **Publish targets** — hedge targets to the desk by 17:30. Late publication is itself a loggable event.

## Weekly / periodic

- Attribution: explain hedge P&L into market, behavior, basis, and residual. Unexplained residual above threshold escalates.
- Assumption table updates land only with model-owner sign-off and a version bump in the run manifest.

## Common issues

- **Vol surface fit fails** — fall back to prior-day surface, flag the run as degraded, notify the desk. Never hand-edit surface nodes.
- **Grid capacity** — degraded 5k-path run is permitted intraday with wider tolerance bands; full run must complete overnight.
