# CLAUDE.md — project context for Claude Code

This file is loaded automatically by Claude Code at the repo root. It captures conventions, mental model, and "do / don't" guidance specific to **Atlas** so you don't have to re-derive them from the docs on every session.

## What this repo is

**Atlas** — a centralized team knowledge hub plus the ingestion pipeline that feeds it.

- **Hub** (`hub/` + `content/`): a Dash app (local / Posit Connect) with channels for onboarding, models (whitepaper + user guide + monitoring plan per model space), compliance, lessons learned, and tooling. Full-text search (SQLite FTS5), TF-IDF + link-graph recommendations, and a grounded copilot sidebar — synthesized by the **local Claude Code CLI** when installed (headless `claude -p`, tools disallowed, retrieval passages only), offline-extractive otherwise. Content is a Google **OKF v0.1** bundle (markdown + YAML frontmatter, `type` required).
- **Pipeline** (`skills/`): converts source material — Word whitepapers (formulas as images), slide decks, videos, code repos — into portable markdown/OKF knowledge. Outputs also feed a Gemini Gem / Vertex AI Search / NotebookLM.

Claude Code (Enterprise) is the build tool. **No Anthropic SDK, no keys in the repo.** The pipeline runs entirely inside Claude Code. The hub's copilot picks its synthesis backend at startup: a custom `ATLAS_COPILOT_ADAPTER` if set, else the generic OpenAI-compatible HTTP adapter when `ATLAS_LLM_BASE_URL` is configured (stdlib-only, any LLM API, keys via deploy-time env only), else the user's own `claude` CLI headless (the local/testing default), else self-contained extractive answers. Dash UI callbacks for page-specific components MUST use pattern-matching IDs — a plain string ID missing from the current page silently kills its callback (this bit us twice).

## The mental model

Every pipeline step is a **skill** under `skills/`, not a standalone script. Skills come in two shapes:

- **Type A (deterministic):** `SKILL.md` + `helper.py`. Claude Code orchestrates; the helper does plumbing. No LLM reasoning inside the step.
  Skills: `docx-extract`, `md-normalize`, `formula-index`, `structured-index`, `qa-report`, `bundle-for-gem`, `knowledge-hub`.

- **Type B (LLM runbook):** `SKILL.md` + `prepare_worklist.py` + `runbook_template.md`. The prepare phase is deterministic (writes a worklist + runbook). The execute phase is Claude Code reading the runbook and using its own vision / reasoning, iterating over the worklist with resumability baked in.
  Skills: `formula-ocr`, `structured-extract`, `video-ingest`, `deck-ingest`, `code-ingest`.

The runbook pattern is non-negotiable for LLM work. **Don't** reach for the `anthropic` SDK or an external API — that's not this pipeline's model.

Skill folders follow the [Agent Skills](https://agentskills.io/specification) conventions (see `skills/README.md`): frontmatter `name` matches the folder, `description` states what the skill does *and* when to use it (that field is what triggers the skill), and `.claude/skills/` holds one discovery symlink per skill so Claude Code loads them natively. New skills start from `skills/_template/`; `tests/test_skills_structure.py` enforces the whole contract.

## File taxonomy

| Path | What it is | Who writes it | Committed? |
|------|------------|---------------|------------|
| `raw/` | Original source material (`.docx`, `videos/`, `decks/`) | Humans | **No** (gitignored, confidential) |
| `artifacts/` | Intermediate outputs (skeletons, manifests, worklists, runbooks, transcripts, inventories, QA HTML) | Pipeline | **No** (gitignored, disposable) |
| `content/` | The hub's OKF bundle — onboarding, model spaces, compliance, lessons, tooling | Humans + ingest skills | **Yes** (the hub's front-facing knowledge) |
| `knowledge/docs/` | One cleaned `.md` per whitepaper — the portable core | Pipeline | **Yes** (tracked, the gold) |
| `knowledge/formula_index.md`, `knowledge/indexes/*` | Cross-doc indexes — `.md` for runtime, `.csv` for audit | Pipeline | **Yes** |
| `knowledge/gem_bundle/` | Gem-ready consolidated files | Pipeline | **Yes** |
| `hub/` | The hub app: Dash UI + engine (loader/search/recommend/copilot) | Humans + Claude Code | **Yes** |
| `skills/` | Every step's SKILL.md, helpers, prompts, runbook templates | Humans + Claude Code | **Yes** (versioned — every prompt change is a commit) |
| `schemas/` | JSON schemas for formula + 5 structured index types | Humans | **Yes** |
| `docs/` | Long-form guidance split out of the original whitepaper | Humans | **Yes** |
| `tests/` | Hub engine/bundle contract tests (CI) + pipeline checks on the pilot doc | Humans | **Yes** |

## Do / don't

**Do**

- Read `README.md` for the high-level shape, `hub/README.md` for the app, and `docs/operating-model.md` for the conceptual model before making structural changes.
- When a skill needs to change, edit its `SKILL.md` and/or its helper / prompt, and commit. Prompts are versioned — include a `prompt_version` bump in the prompt file and reference it in extraction outputs.
- Keep every `content/` file OKF-conformant: parseable YAML frontmatter with non-empty `type`. Validate with `python skills/knowledge-hub/helper.py validate` (also enforced by `tests/test_hub_engine.py`).
- Preserve the anchor format `doc_id#section-slug`. Citations across the hub, Gem, Vertex, and NotebookLM all rely on it.
- Preserve the `verbatim_quote` field in every structured extraction. It is the audit trail; without it, the index is not defensible in a regulated review.
- Use `knowledge/docs/` as the source of truth for whitepapers. In `content/models/`, keep `model_id` frontmatter matching the pipeline `doc_id` so whitepapers attach to their model space automatically.
- Run `pytest tests/test_hub_engine.py` after touching `hub/` or `content/`, and `pytest tests/test_skills_structure.py` after touching `skills/` (frontmatter contract, shape files, discovery symlinks).

**Don't**

- Don't add vendor LLM SDKs (`anthropic`, `openai`, ...) or hardcoded keys/endpoints anywhere. The **pipeline** never calls a hosted model — Claude Code is its executor. The **hub copilot** may: only through `hub/engine/http_adapter.py` (stdlib `urllib`, OpenAI-compatible), with base URL / key / model coming exclusively from deploy-time env vars (`ATLAS_LLM_*`).
- Don't use `pdftotext`, `docx2txt`, or any flattening extractor. They destroy structure.
- Don't hand-edit files under `knowledge/`. Fix the source (raw docx / OCR prompt / skill) and re-run. (`content/` is different — it *is* hand-editable, via PR.)
- Don't bake page numbers into locators — use section anchors.
- Don't bundle for Vertex or NotebookLM. Those consume `knowledge/docs/` and `knowledge/indexes/` as-is. Bundling is Gem-specific.
- Don't put Dash-isms or hub-specific hacks into `content/` or `knowledge/` files — knowledge stays runtime-neutral.

## Conventions at a glance

- **`doc_id`** — `{family}_{short_name}_v{version}`, lowercase, underscores. Stable across whitepaper versions.
- **Concept ids (hub)** — bundle-relative path without extension (`compliance/npi-data-handling`); channel = first path segment.
- **Anchors** — `{doc_id}#{kebab-case-heading-slug}` / `/doc/{concept_id}#{slug}`. Generated identically by `docx-extract`, `md-normalize`, and `hub/engine/loader.py`; if they diverge, every downstream locator breaks.
- **OKF frontmatter** — `type` required; `title`, `description`, `tags`, `timestamp` recommended; `resource` for ingested media/repos. `index.md`/`log.md` are reserved (not concepts).
- **Wiki-links** — `[[target]]` or `[[target|label]]` in `content/`; resolved by id or unique basename; broken links tolerated (OKF: knowledge not yet written).
- **Model spaces** — `content/models/{slug}/model.md` (type: Model Card) + `whitepaper.md` / `user-guide.md` / `monitoring-plan.md`.
- **Formula IDs** — `F-NNN`; **Assumption IDs** — `A-NNN` per doc.
- **Knowledge pack version** — `YYYY.MM.DD`, tagged as `knowledge-vYYYY.MM.DD`.

## Where to look for what

- Hub won't show new content? Restart the app (corpus loads at startup); if still missing, `python skills/knowledge-hub/helper.py validate` — unparseable frontmatter is skipped.
- Search returning junk / copilot answering weakly? Ranking lives in `hub/engine/search.py` (BM25 weights, query stopwords) and the coverage gate in `hub/engine/copilot.py`.
- Skill triggers not firing? Rewrite the `description` frontmatter in the skill's `SKILL.md` — that's the only text Claude sees before deciding to load it. The body's "When to use" block guides behavior *after* it loads.
- LLM step producing bad output? Edit the prompt under the skill's `runbook_template.md` or `skills/structured-extract/prompts/{type}.md`, bump `prompt_version`, re-run.
- Session drops mid-runbook? Resumability is built in — re-issue "execute the runbook." Entries with valid existing output are skipped.
- Schema validation failing? Schemas live under `schemas/` — read the inline descriptions before relaxing anything.

## Current state

- **Hub: built and tested.** Engine + UI + seeded OKF sample bundle (2 illustrative model spaces, policies, lessons, tooling). `pytest tests/test_hub_engine.py` = green. Sample content is marked as such — replace with real material.
- **Ingest skills for video/deck/code: working.** Prepare helpers are implemented and tested; execute phases are Claude Code runbooks.
- **Docx pipeline: scaffold.** Helpers under `docx-extract`, `formula-ocr`, `md-normalize`, `formula-index`, `structured-*`, `qa-report`, `bundle-for-gem` are intentionally `NotImplementedError` stubs with contract docstrings. Flesh them out in order — `docx-extract` first — and validate each on the pilot doc before scaling up.
