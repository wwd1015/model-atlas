# model-atlas

Offline pipeline that turns a library of internal model whitepapers (Word `.docx` with embedded formulas) into a portable RAG knowledge pack. Today it feeds a Gemini Gem; tomorrow the same artifacts feed Vertex AI Search or NotebookLM without rework.

**Design principle.** Pre-chew the docs offline so the runtime (Gem / Vertex) does as little reasoning about structure as possible. Every output lives under `knowledge/` as clean Markdown + structured indexes — nothing is Gem-specific except the `gem_bundle/` step.

**Build tool.** Claude Code (Enterprise). No Anthropic SDK, no API keys. Every pipeline step is a Claude Code **skill** under `skills/`. LLM-heavy steps (formula OCR, structured extraction) use a two-phase **runbook pattern**: a deterministic prepare phase writes a work list + runbook, then Claude Code itself executes the runbook using its own vision / reasoning.

---

## Repository layout

```
model-atlas/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── raw/            # original .docx files — GITIGNORED, confidential
├── artifacts/      # intermediate outputs — GITIGNORED, disposable
│   ├── extracted/  # mammoth HTML + image dumps + Markdown skeletons
│   ├── manifests/  # per-doc equation manifests (JSON)
│   ├── formulas/   # per-image LaTeX + metadata (JSON)
│   ├── structured/ # per-doc structured records (JSON)
│   └── qa/         # side-by-side HTML review
├── knowledge/      # FINAL portable outputs — the gold
│   ├── docs/                 # one cleaned .md per whitepaper
│   ├── formula_index.md      # master cross-doc formula index
│   ├── indexes/              # cross-doc structured indexes (.md + .csv)
│   ├── master_toc.md         # catalog of all docs with section maps
│   └── gem_bundle/           # Gem-ready consolidated files (≤10)
├── schemas/        # JSON schemas for every structured extraction type
├── skills/         # pipeline logic — every step is a SKILL.md + helper
│   ├── docx-extract/
│   ├── formula-ocr/          # runbook pattern (prepare + execute)
│   ├── md-normalize/
│   ├── formula-index/
│   ├── structured-extract/   # runbook pattern, 5 index types via prompts/
│   ├── structured-index/
│   ├── qa-report/
│   └── bundle-for-gem/
├── tests/
│   └── test_one_doc.py       # end-to-end contract checks on the pilot
└── docs/           # build guidance split out of the original whitepaper
```

`raw/` and `artifacts/` are gitignored. `knowledge/` is the value — version it carefully; this is what migrates to Vertex AI. `skills/` is the pipeline — every prompt and schema is a commit.

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env   # edit paths if needed
```

No API keys required. The LLM work in `formula-ocr` and `structured-extract` runs inside Claude Code using its native tools.

Drop one pilot `.docx` in `raw/` before running anything.

---

## How you operate it

You never invoke Python directly. You open Claude Code at the repo root and speak in natural language. A typical pilot session:

```
You: Run docx-extract on raw/Model_A_LGD_v3.2.docx.
Claude Code: [loads skills/docx-extract/SKILL.md, runs helper, reports manifest]

You: Prepare the formula OCR runbook for this doc.
Claude Code: [runs prepare_worklist.py, writes artifacts/ocr_runbook.md]

You: Execute the runbook.
Claude Code: [reads each image with its vision tool, writes formula JSONs]

You: Normalize the doc and build the formula index.
Claude Code: [md-normalize, then formula-index]

You: Prepare metrics extraction.
Claude Code: [structured-extract prepare with index_type=metrics]

You: Execute it.
Claude Code: [processes, writes per-doc metrics JSONs]

You: Build the metrics index and the QA report.
Claude Code: [structured-index, then qa-report]
```

For the conceptual model behind this — the skills-over-scripts idea, the Type A / Type B split, how Claude Code permissions matter, how to write a good `SKILL.md` — see [`docs/operating-model.md`](docs/operating-model.md).

---

## Execution order (new-repo checklist)

**Pilot phase:**

1. Scaffold: this repo, committed.
2. Drop one representative `.docx` in `raw/`.
3. `docx-extract` → inspect the manifest.
4. `formula-ocr` prepare → read the runbook before executing.
5. `formula-ocr` execute → watch the first few formulas; fix the prompt in `runbook_template.md` if the LaTeX looks wrong.
6. `md-normalize` → open the final `.md` and read it end-to-end.
7. `formula-index` → spot-check entries.
8. `qa-report` for formulas → review every formula.

**Structured phase:**

9. `structured-extract` prepare + execute for `metrics` on the pilot.
10. `structured-index` for `metrics` → inspect CSV + Markdown.
11. `qa-report` for structured → verify every `verbatim_quote` matches the source.

**Scale-up:**

12. Drop the remaining docs in `raw/`. Re-run the extract → OCR → normalize → index loop across all.
13. Add other index types as needed (`assumptions`, `data`, `governance`, `dependencies`).
14. `bundle-for-gem` → upload to the Gem. Run the 25-question test set.
15. Tag Git: `knowledge-vYYYY.MM.DD`. Note which Gem build uses that tag.

Details for every phase are in [`docs/pipeline.md`](docs/pipeline.md).

---

## Deeper guidance

- [`docs/operating-model.md`](docs/operating-model.md) — skills over scripts, runbook pattern, writing `SKILL.md`, permissions, troubleshooting.
- [`docs/pipeline.md`](docs/pipeline.md) — step-by-step Phase 1–2.6: pilot criteria, each pipeline step, structured cross-doc indexes, Gem bundling.
- [`docs/gem-configuration.md`](docs/gem-configuration.md) — Gem system instructions, upload order, test set.
- [`docs/maintenance-and-roadmap.md`](docs/maintenance-and-roadmap.md) — versioning, update loop, paths to NotebookLM / Vertex / multi-agent.
- [`docs/compliance.md`](docs/compliance.md) — data classification, model risk linkage, hallucination risk, things not to do.

---

## Portability guarantees

These hold across every runtime migration:

- `knowledge/docs/` is always one clean Markdown file per whitepaper. No Gem-specific hacks inside docs.
- Frontmatter fields are stable — they become Vertex metadata filters.
- Section anchors are stable across versions — citations must not break.
- Formula index is always regenerated from `knowledge/docs/`, never hand-edited.
- Gem quirks live only in the Gem system prompt, never in knowledge files.

## License

Internal use only. Whitepapers under `raw/` may be confidential or restricted — confirm your firm's GenAI policy before uploading anywhere.
