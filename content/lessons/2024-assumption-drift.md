---
type: Lesson Learned
title: "2024: Assumption drift in CRE vacancy"
description: A model assumption stayed 'affirmed' on paper for two years while the market moved — caught late by a validator, not by monitoring. Sample case study.
tags: [lesson, assumptions, monitoring, cre]
timestamp: 2026-07-01
severity: High
---

# 2024: Assumption drift in CRE vacancy

> **Sample case study** — illustrative of the shape a lesson-learned writeup takes.

## What happened

The CRE PD model's assumption **A-001** (market vacancy as a sufficient proxy for local demand shocks — see the [whitepaper](/models/cre-pd-v2/whitepaper.md)) was written in 2022, when office and retail vacancy moved together. Through 2023–2024, post-pandemic office vacancy decoupled sharply from the metro-level composite index the model used. PDs in office-heavy sub-portfolios were understated for roughly three quarters.

## How it was caught

Not by monitoring. The composite PSI stayed green because the *score distribution* barely moved — the drift was in the relationship between an input and reality, not in the input's distribution. The 2024 annual validation caught it by segment-level backtesting: office-segment calibration ratio was 1.6 while the composite sat at 1.1.

## Root cause

- The assumption re-affirmation step was a checkbox, not an analysis. "Reviewed, no change" was written by someone who hadn't been asked to produce evidence.
- Monitoring metrics were portfolio-level; the failure was segment-level.

## What changed

1. Assumption re-affirmation now requires **evidence attached per assumption ID** — a chart, a table, or an explicit experience comparison. Checkbox affirmations are rejected. (See the annual-review section of the [monitoring plan](/models/cre-pd-v2/monitoring-plan.md).)
2. Calibration ratio is now computed **per segment**, with segment-level amber/red thresholds.
3. The whitepaper's assumption section links each assumption to the monitoring metric that would catch its failure. An assumption with no detecting metric is itself a finding.

## The transferable lesson

Portfolio-level green can hide segment-level red. When you affirm an assumption, ask: *what monitoring metric would fire if this assumption broke?* If the answer is "none," say so loudly. Framework context: [[model-risk-101]].
