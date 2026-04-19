# CLAUDE.md — project context for Claude Code

This file is loaded automatically by Claude Code at the repo root. It captures conventions, mental model, and "do / don't" guidance specific to `model-atlas` so you don't have to re-derive them from the docs on every session.

## What this repo is

An offline pipeline that converts a library of internal model whitepapers (Word `.docx`, formulas often embedded as images) into a portable RAG knowledge pack. Today's runtime is a Gemini Gem; tomorrow's is Vertex AI Search or NotebookLM. Every artifact under `knowledge/` must stay portable across those runtimes.

Claude Code (Enterprise) is the build tool. **No Anthropic SDK, no API keys.** The pipeline is designed to run entirely inside Claude Code.

## The mental model

Every pipeline step is a **skill** under `skills/`, not a standalone script. Skills come in two shapes:

- **Type A (deterministic):** `SKILL.md` + `helper.py`. Claude Code orchestrates; the helper does plumbing. No LLM reasoning inside the step.
  Skills: `docx-extract`, `md-normalize`, `formula-index`, `structured-index`, `qa-report`, `bundle-for-gem`.

- **Type B (LLM runbook):** `SKILL.md` + `prepare_worklist.py` + `runbook_template.md`. The prepare phase is deterministic (writes a worklist + runbook). The execute phase is Claude Code reading the runbook and using its own vision / reasoning, iterating over the worklist with resumability baked in.
  Skills: `formula-ocr`, `structured-extract`.

The runbook pattern is non-negotiable for LLM work. **Don't** reach for the `anthropic` SDK or an external API — that's not this pipeline's model.

## File taxonomy

| Path | What it is | Who writes it | Committed? |
|------|------------|---------------|------------|
| `raw/` | Original `.docx` whitepapers | Humans | **No** (gitignored, confidential) |
| `artifacts/` | Intermediate outputs (skeletons, manifests, per-formula JSONs, per-doc structured JSONs, QA HTML) | Pipeline | **No** (gitignored, disposable) |
| `knowledge/docs/` | One cleaned `.md` per whitepaper — the portable core | Pipeline | **Yes** (tracked, the gold) |
| `knowledge/formula_index.md`, `knowledge/indexes/*` | Cross-doc indexes — `.md` for runtime, `.csv` for audit | Pipeline | **Yes** |
| `knowledge/gem_bundle/` | Gem-ready consolidated files | Pipeline | **Yes** |
| `skills/` | Every step's SKILL.md, helpers, prompts, runbook templates | Humans + Claude Code | **Yes** (versioned — every prompt change is a commit) |
| `schemas/` | JSON schemas for formula + 5 structured index types | Humans | **Yes** |
| `docs/` | Long-form guidance split out of the original whitepaper | Humans | **Yes** |
| `tests/` | End-to-end contract checks on the pilot doc | Humans | **Yes** |

## Do / don't

**Do**

- Read `README.md` for the high-level shape and `docs/operating-model.md` for the conceptual model before making structural changes.
- When a skill needs to change, edit its `SKILL.md` and/or its helper / prompt, and commit. Prompts are versioned — include a `prompt_version` bump in the prompt file and reference it in extraction outputs.
- Preserve the anchor format `doc_id#section-slug`. Citations across the Gem, Vertex, and NotebookLM all rely on it.
- Preserve the `verbatim_quote` field in every structured extraction. It is the audit trail; without it, the index is not defensible in a regulated review.
- Use `knowledge/docs/` as the source of truth for everything downstream (formula index, structured extraction, bundling). Never hand-edit a file there.

**Don't**

- Don't add API key handling, `anthropic` SDK imports, or any code that calls a hosted model from Python. Claude Code is the executor.
- Don't use `pdftotext`, `docx2txt`, or any flattening extractor. They destroy structure.
- Don't hand-edit files under `knowledge/`. Fix the source (raw docx / OCR prompt / skill) and re-run.
- Don't bake page numbers into locators — Word pagination is unstable. Use section anchors.
- Don't bundle for Vertex or NotebookLM. Those consume `knowledge/docs/` and `knowledge/indexes/` as-is. Bundling is Gem-specific.
- Don't over-tune for Gem. Every Gem-ism in a knowledge file becomes tech debt on the next runtime migration.

## Conventions at a glance

- **`doc_id`** — `{family}_{short_name}_v{version}`, lowercase, underscores. Stable across whitepaper versions.
- **Anchors** — `{doc_id}#{kebab-case-heading-slug}`. Generated identically by `docx-extract` and `md-normalize`; if they diverge, every downstream locator breaks.
- **Formula IDs** — `F-NNN` in `formula_index.md`. Stability is maintained by `artifacts/formula_id_map.json`; only new formulas get new IDs.
- **Assumption IDs** — `A-NNN` per doc, in order of appearance.
- **Knowledge pack version** — `YYYY.MM.DD`, written into doc frontmatter and index headers, and tagged in Git as `knowledge-vYYYY.MM.DD`.

## Where to look for what

- Skill triggers not firing? Rewrite the "When to use" block in the skill's `SKILL.md`.
- LLM step producing bad output? Edit the prompt under `skills/formula-ocr/runbook_template.md` or `skills/structured-extract/prompts/{type}.md`, bump `prompt_version`, re-run.
- Session drops mid-runbook? Resumability is built in — just re-issue "execute the runbook." Entries with valid existing output are skipped.
- Schema validation failing? Schemas live under `schemas/`. Every field in `records[]` has a reason — read the inline descriptions before relaxing anything.
- Want the full build guidance? `README.md` links to the five docs under `docs/`.

## Current state

Scaffold only. Helper scripts are intentionally `NotImplementedError` stubs with docstrings that describe the contract. Flesh them out in order — `docx-extract` first, then the rest — and use the pilot doc to validate each before scaling up.
