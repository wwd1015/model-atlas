---
type: Glossary
title: Glossary
description: Acronyms and terms of art used across the team, with one-paragraph definitions.
tags: [onboarding, reference]
timestamp: 2026-07-01
---

# Glossary

Definitions are deliberately one paragraph. If a term needs more, it should be a concept of its own — link it.

## NPI

Non-public Personal Information — personally identifiable financial information collected from customers, protected under GLBA. If a field can identify a customer *and* relates to their finances, treat it as NPI. Handling rules: [[npi-data-handling]].

## PD

Probability of Default — the likelihood that a borrower defaults within a horizon (usually 12 months). Core output of credit risk models like the [CRE PD model](/model/cre-pd-v2).

## LGD

Loss Given Default — the share of exposure lost when a default occurs, after recoveries and collateral. Paired with PD and EAD in expected-loss calculations.

## EAD

Exposure at Default — the outstanding amount expected to be owed at the moment of default, including expected drawdowns of undrawn commitments.

## CRE

Commercial Real Estate — the lending segment covering income-producing property. Our PD coverage for this book is the [CRE PD model](/model/cre-pd-v2).

## VA

Two meanings, context matters: **Valuation Analyst** (the job family this onboarding is written for) and **Variable Annuity** (the insurance product hedged by the [VA hedging model](/model/va-hedge-v1)).

## MRM

Model Risk Management — the second-line function that validates models and enforces the governance framework. Plain-language intro: [[model-risk-101]].

## OKF

Open Knowledge Format — Google's open spec (2026) for knowledge as a directory of markdown files with YAML frontmatter; every concept declares a `type`. Atlas content is an OKF bundle, which is why any agent or search tool can consume it.

## Champion–challenger

Running a candidate model (challenger) alongside the production model (champion) on the same data to compare performance before switching. Required for material model replacements.

## Backtesting

Comparing model predictions against realized outcomes over a historical window. The primary evidence in monitoring reports.

## PSI

Population Stability Index — a drift metric comparing the score distribution of the current population against the development sample. Rule of thumb: below 0.10 stable, 0.10–0.25 investigate, above 0.25 significant shift.
