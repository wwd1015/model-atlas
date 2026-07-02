---
type: Policy
title: NPI data handling
description: How to handle Non-public Personal Information in the commercial space — the three rules, approved patterns, and incident response.
tags: [compliance, npi, data, glba]
owner: Data Steward
timestamp: 2026-07-01
---

# NPI data handling

**NPI** (Non-public Personal Information — see the [[glossary]]) is personally identifiable financial information protected under GLBA. In the commercial space this includes guarantor personal financials, beneficial-owner details, and any obligor field that identifies an individual. Commercial ≠ exempt: the moment a natural person is identifiable, GLBA applies.

## The three rules

1. **NPI stays in approved environments.** The scoring grid, the risk mart, and the governed analytics workspace are approved. Laptops, personal drives, email attachments, and unapproved SaaS are not.
2. **Minimize before you move.** If a task needs aggregates, extract aggregates. If it needs obligor rows, drop the identifying columns first. The de-identified extract patterns below are pre-approved.
3. **Never into GenAI tools.** No NPI in prompts, uploads, or context — including enterprise tools, unless the tool is explicitly approved *for that data class*. Details: [[genai-acceptable-use]].

## Approved patterns

| Need | Approved pattern |
|------|------------------|
| Model development sample | De-identified extract via the data steward's tokenization job |
| Monitoring metrics | Aggregate queries run inside the approved environment; only aggregates leave |
| Debugging a scoring anomaly | Work inside the environment; export the *derived* diagnostic, not the row |
| Sharing with validators | Grant environment access — never ship files |

## If you suspect an exposure

1. Stop the activity; don't try to clean up yourself (deleting evidence complicates response).
2. Notify the data steward and your manager immediately — same business day.
3. Preserve what happened: what data, which system, who had access.

An exposure reported same-day is an incident; one discovered later is a finding. Model-cycle context: both sample user guides ([CRE PD](/models/cre-pd-v2/user-guide.md), [VA hedging](/models/va-hedge-v1/user-guide.md)) mark exactly which inputs carry NPI.
