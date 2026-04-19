---
name: bundle-for-gem
type: deterministic
---

# bundle-for-gem

Consolidates the portable `knowledge/docs/` and `knowledge/indexes/` into Gem-ready bundled files under `knowledge/gem_bundle/`. Accounts for Gem's file-count limit and renders each bundle with a table of contents and clear doc separators. This is the last step before uploading to a Gem.

## When to use

Use this skill when the user wants to:
- "Bundle for the Gem" / "produce gem bundles"
- "Rebuild gem bundles after updating Model C"
- "Check bundle sizes — are we under the limit?"

Do NOT use this skill when:
- `knowledge/docs/` or `knowledge/indexes/` are empty — run the upstream skills first.
- The user wants to upload to Vertex AI or NotebookLM — those don't use bundles. Point them at `knowledge/docs/` and `knowledge/indexes/` directly.

## Inputs

- `knowledge/docs/*.md` — per-doc normalized Markdown.
- `knowledge/indexes/*.md` — cross-doc structured indexes.
- `knowledge/formula_index.md` — the formula index.
- `knowledge/master_toc.md` — the top-level catalog.
- `skills/bundle-for-gem/grouping.yaml` — grouping config (see below).
- **Config:** `gem_file_limit` (default 10), `max_bytes_per_file` (default warn at 400KB, hard-limit at 1MB).

### grouping.yaml example

```yaml
# Each entry becomes one bundle file.
# Docs are assigned to bundles by regex on doc_id.
bundles:
  - name: "credit_risk"
    label: "Credit Risk — PD/LGD/EAD models"
    match: "^model_[abc]_"
  - name: "market_risk"
    label: "Market Risk models"
    match: "^model_[de]_"
  - name: "operational"
    label: "Operational Risk and other"
    match: ".*"  # catch-all for unmatched docs

# Indexes are always included as their own files (one bundle per index).
always_include_indexes:
  - master_toc.md
  - formula_index.md
  - metrics_index.md
  # add others as built
```

## Outputs

- `knowledge/gem_bundle/00_master_toc.md`
- `knowledge/gem_bundle/01_formula_index.md`
- `knowledge/gem_bundle/02_metrics_index.md`
- `knowledge/gem_bundle/03_credit_risk.md` (bundled content)
- `knowledge/gem_bundle/04_market_risk.md`
- `knowledge/gem_bundle/05_operational.md`
- `knowledge/gem_bundle/BUNDLE_MANIFEST.json` — what's in each file, for your records.

### Content bundle structure

```markdown
# Credit Risk — PD/LGD/EAD models

This bundle contains the following whitepapers:

- Model A — Loss Given Default Methodology [doc_id: model_a_lgd_v3]
- Model B — PD Methodology [doc_id: model_b_pd_v2]
- Model C — EAD Methodology [doc_id: model_c_ead_v1]

For cross-doc formulas, see the formula index. For performance metrics, see the metrics index.

---

# DOC: Model A — Loss Given Default Methodology

(full contents of knowledge/docs/model_a_lgd_v3.md including frontmatter)

---

# DOC: Model B — PD Methodology

(full contents of knowledge/docs/model_b_pd_v2.md)

---

# DOC: Model C — EAD Methodology

(full contents of knowledge/docs/model_c_ead_v1.md)
```

## Procedure

1. **Read `grouping.yaml`.** Validate that every `match` regex is valid.
2. **Enumerate inputs.** List all docs in `knowledge/docs/` and all indexes in `knowledge/indexes/`.
3. **Assign docs to bundles.** For each doc, find the first matching bundle by regex order. Surface docs that didn't match any bundle — the config should have a catch-all.
4. **Compose index bundles.** Copy each `always_include_indexes` entry to `knowledge/gem_bundle/` with a numeric prefix for upload order.
5. **Compose content bundles.** For each content bundle: render the bundle header + doc list, then concatenate each doc's contents with `---\n# DOC: <title>\n\n...` separators.
6. **Check sizes.** Warn if any single bundle exceeds `max_bytes_per_file` (soft 400KB, hard 1MB). Suggest splitting.
7. **Check total file count.** If total output files exceed `gem_file_limit` (default 10), warn prominently and suggest either merging small content bundles or dropping lower-priority indexes.
8. **Write `BUNDLE_MANIFEST.json`** — records which docs and indexes are in each bundle file, for your reference and for reproducibility.
9. **Report** per bundle: file size, doc count. Final summary: total files, total bytes, whether within Gem limit.

## Example invocations

- "Bundle everything for the Gem."
- "Rebuild the credit_risk bundle only."
- "What's the current bundle size?"

## Common gotchas

- **Gem limit is a moving target.** Verify the current file-count and per-file size limits before your final build. Tell the user to double-check.
- **Don't drop indexes to save file count.** Indexes are higher leverage than fine-grained content splits. If you're over budget, merge content bundles — not indexes.
- **Order matters to Gem behavior, sometimes.** Number bundles with prefixes (`00_`, `01_`, ...) so upload order is deterministic. Indexes first, content second.
- **Frontmatter stays in the bundled content.** Don't strip YAML from individual docs during bundling — the Gem can use that metadata, and it doesn't hurt to have it.
- **Catch-all regex.** Always have a bundle with `match: ".*"` as the final entry, or a new doc without a matching group will silently not ship.
- **Never bundle for Vertex.** This skill is Gem-specific. For Vertex, upload `knowledge/docs/` and `knowledge/indexes/` as-is — unbundled, one file per doc and index.
