# The pipeline, step by step

The pipeline converts a directory of `.docx` whitepapers into a portable knowledge pack under `knowledge/`. Every step is a skill under `skills/`. Run the pilot end-to-end on one doc before batching 30.

## Pilot criteria

Do not batch 30 docs first. Pick one representative whitepaper, run the full pipeline end-to-end, inspect every output. Only then scale up.

**Criteria for a good pilot doc.** Medium length (20–40 pages), contains at least 10 formulas, uses both inline and display math, has the section structure typical of your library. If formulas come in two flavors (native Word equations and pasted images), pick a doc with both.

**Success criteria before moving on.**

- Every formula image is accounted for (none lost, none duplicated).
- OCR LaTeX renders correctly for >95% of formulas — eyeball all of them.
- Section headings preserved with correct hierarchy.
- Locators (`[DocName / §Section / Heading]`) work.
- Cleaned Markdown is self-contained and human-readable.

---

## Step 1 — Classify equations (OMML vs image)

Word stores equations two ways. Native equations are OMML XML inside the document — those convert to LaTeX losslessly via pandoc or `docx2tex`. Pasted pictures of equations need vision OCR. Mixing them without classifying first wastes effort and loses fidelity on the native ones.

The `docx-extract` skill handles this:

1. Unzip the docx (it's a zip archive).
2. Parse `word/document.xml` with lxml.
3. Find `<m:oMath>` elements — these are native equations. Record their location and convert via `pandoc -f docx -t latex` on the surrounding context, or use a targeted OMML→LaTeX converter.
4. Find `<w:drawing>` and `<w:pict>` elements — these are images. Record image filename (from `word/media/`), the paragraph index, and surrounding text.
5. Emit `artifacts/manifests/{doc_id}.json` with a unified list of equations, each tagged `type: omml` or `type: image`, with position, section heading, and surrounding ~3 sentences of context.

**Why context matters.** Vision OCR accuracy jumps significantly when the model knows what the formula is about. "This is a formula for Loss Given Default" gets you better LaTeX than raw pixels alone.

## Step 2 — Extract clean Markdown skeleton

Use `mammoth` to convert each docx to HTML preserving headings, tables, lists, and image references. Then convert the HTML to Markdown. At this stage, formulas are still placeholders — either inline image references or `{{EQUATION_<id>}}` tokens you inject.

**Output.** `artifacts/extracted/{doc_id}.md` with tokenized equation slots and `artifacts/extracted/{doc_id}/images/` with the raw image files.

**Gotcha.** Mammoth sometimes flattens heading levels. After conversion, run a quick pass to verify H1/H2/H3 hierarchy matches the source. If the docs use custom styles, build a mammoth style map.

## Step 3 — OCR the image equations (Claude Code session, not API script)

This step runs *inside* Claude Code. No Python SDK, no API key. The driver script only prepares the work list; Claude Code does the vision work.

The `formula-ocr` skill's `prepare_worklist.py` helper produces two artifacts:

1. `artifacts/ocr_worklist.json` — a flat list of every image-type equation across all docs, each entry containing: `image_path`, `output_path`, `doc_id`, `section_heading`, `surrounding_context`, `image_id`.
2. `artifacts/ocr_runbook.md` — a prompt Claude Code will execute.

The runbook tells Claude Code, per entry, to: read the image with its view tool, apply the OCR prompt using the entry's context, validate the JSON against `schemas/formula.schema.json`, write to `output_path`, and log progress every 20 entries. It enforces resumability (skip entries whose output already exists and validates) and treats individual image failures as stubs — not run-halting errors.

**Throughput.** Roughly 30–60 seconds per formula in a session. For 450 formulas across 30 docs, budget one long session or split across 2–3 sessions per model family. Resumability means you can stop and restart without losing work.

**Model choice.** Claude Code Enterprise uses whichever model your org has provisioned. Opus-tier handles formula vision reliably; Sonnet-tier works for clean typeset formulas but may struggle on complex notation. If you notice garbled output on a batch, the first fix is to check which model Claude Code is using.

**Non-formula images.** Skip `is_formula: false` items but keep them in the manifest as non-formula images. Charts and diagrams may come back in a future charts index.

## Step 4 — Stitch LaTeX back into Markdown

Walk each `{{EQUATION_<id>}}` token in the skeleton Markdown and replace with:

```
$$
<latex>
$$
<!-- formula_id: <id> | desc: <description> -->
```

For inline equations, use `$...$` instead. Keep the HTML comment — it gives the Gem and future retrievers metadata without cluttering rendered output.

## Step 5 — Normalize and add frontmatter

Every final `.md` in `knowledge/docs/` gets YAML frontmatter:

```yaml
---
doc_id: model_a_lgd_v3
title: "Model A — Loss Given Default Methodology"
version: "3.2"
effective_date: 2025-06-01
model_family: "Credit Risk / LGD"
source_file: "Model_A_LGD_v3.2.docx"
section_count: 8
formula_count: 14
last_processed: 2026-04-17
---
```

Also normalize heading style: every section heading becomes `## <Number> <Title> {#anchor}` where anchor is a slug. The anchor is what citations point to.

## Step 6 — Build the master formula index

`knowledge/formula_index.md` — one entry per formula across all docs:

```markdown
## F-001 — Probability of Default (logistic)

**Source:** Model A, §3.2 Loss Given Default (p. N/A — Word, use section anchor)
**Anchor:** `model_a_lgd_v3#pd-logistic`
**Description:** Computes PD as a logistic transformation of the linear score.

$$
PD = \frac{1}{1 + e^{-(\beta_0 + \sum \beta_i x_i)}}
$$

**Variables:**
- $\beta_0$ — intercept
- $\beta_i$ — coefficient on feature $i$
- $x_i$ — feature value
```

This index is your killer feature. When a user asks "what's the PD formula in Model A," the Gem hits this file first and returns an exact answer with a pointer.

## Step 7 — Build the master TOC

`knowledge/master_toc.md` — a catalog of all whitepapers with their sections and formula counts. Lets the Gem answer "which doc covers economic capital for retail portfolios" before diving into content.

## Step 8 — QA report

`artifacts/qa/formula_review.html` — for every formula, show side by side: original image (as embedded base64 or relative link) and rendered LaTeX (via MathJax CDN). Flag low-confidence ones at the top. You review this manually before shipping. Budget a half-day for 30 docs.

---

## Structured cross-doc indexes (Phase 2.5)

The formula index pattern generalizes. Any question you'll ask *across* documents — comparative metrics, differing assumptions, data coverage, governance status, model dependencies — should have its own pre-computed structured index. These indexes are what make the Gem answer aggregation and comparison questions reliably, which vanilla RAG struggles with.

**Design principle.** Extract the structured data once per doc, with audit trails (verbatim quote + anchor), then roll it up into both human-readable Markdown and machine-queryable CSV. The CSV is for reproducibility and for future pipelines (Vertex SQL tools, BI dashboards); the Markdown is what the Gem reads.

### Which indexes to build

Start with the ones that answer your actual recurring questions. Suggested priority:

1. **`metrics_index`** — Performance and validation stats (AUC, KS, Gini, R², MAPE, RMSE, HL, Brier, etc.). Answers "which model has the highest X on dataset Y?"
2. **`assumptions_index`** — Key modeling assumptions per doc (distributional forms, stationarity, independence, segmentation rules). Answers "which models assume X?"
3. **`data_index`** — Training/validation data period, sample size, segments, exclusions. Answers "which models were trained on post-2020 data?"
4. **`governance_index`** — Owner, approval date, next review date, regulatory tier, tier-1/tier-2 classification. Answers "which models are due for review?"
5. **`dependencies_index`** — Which models feed into which. Answers "if Model A changes, what downstream models are affected?"

Pick the 2–3 that match your real use case. Don't build all five upfront.

### Step 9 — Define schemas

Before extracting, define a JSON schema per index type in `schemas/`. Every record must include `verbatim_quote` — the exact source text that supports the extracted value — and `anchor` (`doc_id#section-anchor`). This is the audit trail that makes structured indexes trustworthy in a regulated context. Without it they are not.

### Step 10 — Extract structured records per doc

Same pattern as formula OCR — `structured-extract` prepare writes a runbook, Claude Code executes it. The skill takes an `index_type` argument (`metrics` / `assumptions` / `data` / `governance` / `dependencies`) and uses the matching prompt file under `skills/structured-extract/prompts/`. Each prompt file is versioned independently; when you improve a prompt, that's one commit, and it's reviewable.

Long docs: if a doc exceeds a conservative context budget (roughly 50 pages), the runbook processes section-by-section and merges records — no silent truncation.

### Step 11 — Roll up into cross-doc indexes

For each index type, `structured-index` consolidates per-doc JSONs into two outputs:

- `knowledge/indexes/{type}_index.csv` — one row per record. Machine-readable, diff-friendly, future-proof for Vertex SQL tools.
- `knowledge/indexes/{type}_index.md` — the Gem-facing version with a "How to use" section, the main table, and a caveats section (partly computed: dataset / period / segment heterogeneity).

### Step 12 — QA the structured extraction

Metric extraction is fuzzier than formula OCR. Budget more QA time, not less.

Build a review HTML that shows, per extracted record: the value, the verbatim quote, and a link to the source Markdown anchor. Sort by confidence ascending — review low/medium confidence first. Spot-check at least 20% of high-confidence records too.

Common failure modes to watch for:

- Percentages not normalized (82 vs 0.82).
- Metric name variants not standardized (AUROC vs AUC vs c-statistic).
- Segment-level metric reported as overall.
- Time period misattributed (training period vs validation period).
- Range collapsed to midpoint without flag.

Fix extraction prompts when you find systematic errors, then re-run. Do not hand-edit the CSVs — fix the pipeline.

---

## Gem bundling (Phase 2.6)

### Step 13 — Bundle for Gem

Gems have a file cap (verify current limit before shipping — it has been ~10). Revised bundle strategy:

**Always include these index files (they're small and high-leverage):**

- `master_toc.md`
- `formula_index.md`
- `metrics_index.md` (and any other structured indexes you built)

**Then bundle the content docs:**

- Group by model family where natural (e.g., `bundle_credit_risk.md`, `bundle_market_risk.md`).
- Aim for 5–7 content bundles so total files stay under ~10 with indexes included.

Each content bundle starts with a table of contents listing included docs with their anchors. Use horizontal rules and clear `# DOC: <title>` separators between concatenated docs.

**File budget example (10-file cap):**

- 1 × `master_toc.md`
- 1 × `formula_index.md`
- 1 × `metrics_index.md`
- 1 × `assumptions_index.md` (if built)
- 6 × content bundles

If you build more indexes, sacrifice content bundle granularity — the indexes are more valuable than fine-grained content splits because the Gem follows anchors from the index into the bundle regardless of how the bundle is grouped.

**Do not bundle for Vertex.** Keep `knowledge/docs/` and `knowledge/indexes/` unchanged. That's the Vertex-ready version. The bundling step is Gem-specific.
