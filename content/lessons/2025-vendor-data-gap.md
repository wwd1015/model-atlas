---
type: Lesson Learned
title: "2025: Vendor data gap silently shrank the scoring population"
description: A vendor feed short-loaded for two cycles; downstream jobs ran clean and nobody noticed until reconciliation. Sample case study.
tags: [lesson, data-quality, vendor, monitoring]
timestamp: 2026-07-01
severity: Medium
---

# 2025: Vendor data gap silently shrank the scoring population

> **Sample case study.**

## What happened

A vendor's property-data feed changed its file-splitting behavior after an upstream upgrade; the second file of a two-file delivery was silently dropped by our loader, which treated "file one present" as "delivery complete." For two monthly cycles, ~8% of obligors were scored with the conservative missing-data fallback instead of their actual property metrics. Jobs ran green; the exception report grew, but the growth was attributed to seasonal churn — and an analyst *hand-corrected two obviously-wrong scores in the output table* rather than investigating why they were wrong, which erased the strongest available signal.

## How it was caught

Quarterly reconciliation against the servicing system flagged the population gap. Root-cause took an afternoon once someone looked.

## Root cause

- Load validation checked file *presence*, not row-count reconciliation against the prior cycle.
- Exception-report growth had no threshold — it was reviewed by eyeball.
- The silent hand-fix broke the audit trail: outputs no longer traced to inputs.

## What changed

1. Every input now reconciles row counts vs prior cycle (±2%) **before** scoring starts — step 1 of the [CRE PD user guide](/models/cre-pd-v2/user-guide.md).
2. Exception-report size is a monitored metric with an amber threshold.
3. Policy: **no silent fixes, ever.** A wrong number in a published table is raised and corrected through a logged rerun. This is now in the [[faq]] because every new joiner asks.

## The transferable lesson

"Job succeeded" and "data is right" are different claims. Validate the second explicitly. And when an output looks wrong, the wrongness is *evidence* — investigate it, don't erase it. See also: [[npi-data-handling]] for why ad-hoc local copies to "debug" the data would have compounded this incident.
