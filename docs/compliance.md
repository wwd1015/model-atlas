# Compliance, risk, and things not to do

## Compliance and risk considerations

Model risk in commercial banking. Flag these early, not late.

- **Data classification.** Whitepapers may be confidential or restricted. Confirm that uploading them to Gemini is approved under your firm's GenAI policy. Gem data handling differs from Vertex (enterprise controls).
- **Model validation linkage.** If this chatbot informs model risk reviews, it becomes a model-adjacent tool. Document it. Keep a log of questions/answers for a sample period.
- **Hallucination risk.** Even with tight system instructions, LLMs can paraphrase a formula incorrectly. Add to your system prompt: "When in doubt, quote the source directly rather than paraphrase." Make clear to users that the Gem is an aid, not an authoritative source — the whitepaper is.
- **Version drift.** If a user relies on an answer from an outdated Gem build, that's a risk. Surface the knowledge pack version in every answer: "Based on knowledge pack v2026.04.17."

## Things NOT to do

- **Don't use pdftotext, docx2txt, or any flattening extractor.** They destroy structure and lose formula locations.
- **Don't try to make the Gem do OCR at query time.** Pre-compute everything.
- **Don't hand-edit files in `knowledge/docs/` or `knowledge/indexes/`.** Re-run the pipeline. Hand edits cause drift.
- **Don't skip the QA step on formulas.** Subtle OCR errors (subscript vs superscript, sum vs product) silently poison answers.
- **Don't skip the QA step on structured extraction either.** Metric name variants and percentage normalization errors are just as poisonous as bad formulas, and harder to catch because they look plausible.
- **Don't drop the `verbatim_quote` field to save space.** It's the audit trail. Without it, structured indexes are untrustworthy in a regulated context.
- **Don't present cross-model metrics as directly comparable** when datasets or periods differ. The Gem system prompt enforces this; don't weaken it.
- **Don't bake page numbers into locators** — Word pagination is unstable. Use section anchors.
- **Don't over-tune for Gem.** Every Gem-specific hack you add is tech debt when you migrate to Vertex.
