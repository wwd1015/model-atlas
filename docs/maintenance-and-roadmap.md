# Maintenance and roadmap

## Maintenance loop

Whitepapers will update. The pipeline is idempotent and diff-friendly.

**When a doc updates:**

1. Drop new version in `raw/`.
2. Run the pipeline — old artifacts overwrite cleanly because filenames are doc-id-based.
3. Diff `knowledge/docs/{doc_id}.md` against git history. Review changes.
4. If formulas changed, `formula_index.md` regenerates automatically — spot-check new entries.
5. Re-run `structured-extract` for that doc across all index types. Diff the per-doc JSONs against git history.
6. Regenerate cross-doc indexes (`metrics_index.md`, etc.). Diff against git — any changed row gets spot-checked against its verbatim quote.
7. Re-bundle and re-upload to Gem. Bump a version tag in `knowledge/VERSION.md`.
8. Re-run the test set. Investigate regressions.

**Versioning.** Tag Git commits as `knowledge-vYYYY.MM.DD`. Note which Gem build uses which tag. For a regulated environment this matters — you need to reproduce what answer the Gem gave on date X.

**Why the verbatim quotes pay off here.** When a validator asks "did Model A's AUC change between v3.1 and v3.2?", you can git-diff `metrics_index.csv` and see the value change plus the verbatim quote change in one view. That's the audit artifact.

---

## Future roadmap (when infra unlocks)

This section exists so today's build decisions don't paint you into a corner.

### Path A — NotebookLM Enterprise unlocks

**Effort.** Low. Upload `knowledge/docs/*.md` directly. Skip the Gem bundling step entirely. NotebookLM handles citations natively.

**What to do.** Run both Gem and NotebookLM in parallel on the same 20-question test set. Compare answer quality and citation precision. Migrate users to whichever wins.

**What changes in the repo.** Nothing. `knowledge/docs/` is already the right shape.

### Path B — Vertex AI Search / RAG Engine unlocks

**Effort.** Medium. Create a data store pointing at a Cloud Storage bucket or Drive folder containing `knowledge/docs/`. Configure chunking (semantic or fixed), embeddings (text-embedding-005 or newer), and optionally a re-ranker.

**What to do.** Build a thin agent on Agent Builder or use the Grounded Generation API. Expose via a Chat app or internal web UI. Keep the Gem alive as a fallback during transition.

**What changes in the repo.** Add a `vertex/` directory with Terraform / gcloud config. The `knowledge/` artifacts feed in unchanged.

### Path C — Full multi-agent / function-calling RAG

**Effort.** High. Only pursue if whitepaper RAG is just one surface and you want to federate with structured data (loss forecasts, rating transitions, etc.).

**What to do.** Layer a router + tool-using agent on top of Vertex AI RAG Engine. Add SQL tools for structured data. Add function calling for calculations.

**When to consider.** Only after Path B is in production and users are asking questions that cross unstructured + structured boundaries.

### Portability guarantees you maintain today

- Keep `knowledge/docs/` as one clean Markdown file per whitepaper, always.
- Keep frontmatter consistent — it becomes metadata filters in Vertex.
- Keep anchors stable across versions — citation links should not break.
- Keep the formula index generated from `knowledge/docs/`, never hand-edited.
- Never bake Gem-specific instructions into the docs themselves — all Gem quirks live in the Gem system prompt, not the knowledge files.
