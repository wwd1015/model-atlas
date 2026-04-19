# Operating model — how to run this pipeline in Claude Code

Read this before building anything. It sets the mental model for the whole pipeline.

## The core idea: skills over scripts

Every pipeline step is a **Claude Code skill**, not a standalone Python script. A skill is a folder under `skills/` containing:

- `SKILL.md` — natural-language description of what the skill does, when to use it, what inputs it expects, what outputs it produces. This is what Claude Code reads to decide when and how to invoke the skill.
- Helper files — Python scripts, prompt templates, schemas, config. Called by Claude Code as part of executing the skill.

You invoke skills in natural language. Instead of `python scripts/01_extract.py --doc raw/Model_A.docx`, you say "extract the pilot doc" and Claude Code loads `skills/docx-extract/SKILL.md`, sees it matches, and follows its instructions.

## Two kinds of skills in this pipeline

**Type A — Deterministic skills.** Pure plumbing: parse docx, stitch Markdown, roll up CSVs, render HTML. The `SKILL.md` describes the procedure; the helper script does the work; Claude Code glues them together and reports results. No LLM reasoning inside the step itself — Claude Code only orchestrates.

Examples: `docx-extract`, `md-normalize`, `formula-index`, `structured-index`, `qa-report`, `bundle-for-gem`.

**Type B — LLM-driven skills (runbook pattern).** Steps that need vision or reasoning over document content. These skills split execution into two phases:

1. **Prepare phase (deterministic):** the skill's helper generates a *work list* (JSON enumerating every unit of work) and a *runbook* (Markdown telling Claude Code how to process the list — prompt, schema, output paths, resumability rules).
2. **Execute phase (Claude Code native):** Claude Code reads the runbook and works through the list using its own vision/reasoning. No external API, no SDK — Claude Code *is* the executor.

Examples: `formula-ocr`, `structured-extract`.

The reason for the split: the prepare phase is cheap, deterministic, and diffable. The execute phase is where the LLM work happens. Separating them means you can re-run the prepare phase safely, inspect what work will be done before executing, and resume mid-run if a session drops.

## What a typical operating session looks like

Open Claude Code in the repo. Conversation flow for a pilot run:

```
You: Set up the pilot on raw/Model_A_LGD_v3.2.docx.
Claude Code: [loads docx-extract SKILL.md, runs helper, reports manifest summary]

You: Prepare the formula OCR runbook.
Claude Code: [loads formula-ocr SKILL.md, generates worklist + runbook, reports doc]

You: Execute the runbook.
Claude Code: [reads runbook, processes each image, writes JSONs, reports progress]

You: Normalize the doc and build the formula index.
Claude Code: [runs md-normalize, then formula-index, shows resulting files]

You: Now prepare the metrics extraction runbook for this doc.
Claude Code: [loads structured-extract SKILL.md with index_type=metrics,
              generates worklist + runbook]

You: Execute it.
Claude Code: [processes, writes JSONs]

You: Build the metrics index and QA report.
Claude Code: [rollup + HTML generation, links to outputs]
```

You never invoke Python directly. You never manage API keys. You never hand-edit intermediate files. Claude Code is the interface; skills are the vocabulary.

## Writing good SKILL.md files

A good `SKILL.md` has four sections:

1. **When to use** — plain-language triggers. "Use this skill when the user wants to extract clean Markdown from a Word whitepaper, including embedded formula image references."
2. **Inputs** — what the skill expects. Paths, config, conventions.
3. **Outputs** — what the skill produces, including exact paths.
4. **Procedure** — step-by-step instructions Claude Code follows, including which helper scripts to invoke and how to handle errors.

Keep them concise. If `SKILL.md` is longer than 200 lines, the skill is probably doing too much — split it.

## Version control and reproducibility

Skills are Git-tracked. Every prompt, every schema, every helper script is versioned. When you update a prompt to fix an extraction bug, that change is a commit. When a model validator asks "how was this metric extracted six months ago?", you `git checkout` the tag from that time and re-run.

This is a meaningful audit advantage over scripts-with-secrets. The entire behavior of the pipeline is in Git; nothing is hidden in environment variables or external services.

## When something breaks

- **Skill doesn't trigger.** Your natural-language request didn't match what `SKILL.md` describes. Either rephrase or update the "When to use" section to be more permissive.
- **Skill misbehaves.** Check the helper's logs in `artifacts/`. Most issues are schema or path related.
- **LLM step produces bad output.** Edit the prompt in the skill (or in `skills/structured-extract/prompts/`), commit, re-run. If the prompt changed, re-run the full affected set, not just the failures — consistency matters.
- **Session drops mid-runbook.** Restart Claude Code, re-issue "execute the runbook." The resumability rules in the runbook will skip completed entries.

## Claude Code permissions

Your enterprise Claude Code has whatever filesystem permissions your org provisioned. Confirm up front that it can:

- Read `raw/` (your confidential whitepapers).
- Read/write `artifacts/` and `knowledge/`.
- Read files under `skills/` as part of loading SKILL.md.

If any of these are restricted, talk to your admin before building. Also confirm whether there's a per-session context or usage limit — it affects how you batch the runbook runs.

## Skill authoring conventions

- `SKILL.md` must have the four sections: When to use / Inputs / Outputs / Procedure.
- Keep each under ~200 lines. Split if larger.
- Include 1–2 example invocations in natural language under "When to use" so Claude Code triggers correctly.
- Type B skills must call out the two-phase execution explicitly so Claude Code doesn't try to do LLM work during the prepare phase.
