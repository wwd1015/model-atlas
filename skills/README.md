# skills/ — the Atlas pipeline toolbox

Every pipeline step is a Claude Code **skill**: a folder with a `SKILL.md`
entrypoint plus its supporting files. This layout follows the
[Agent Skills](https://agentskills.io/specification) open standard (the same
conventions used by [anthropics/skills](https://github.com/anthropics/skills)),
with a couple of deliberate Atlas-specific extensions noted below.

## Layout

```
skills/
├── README.md                  # this file
├── _template/                 # starter skeletons — copy one to add a skill
│   ├── type-a-deterministic/  #   SKILL.md + helper.py
│   └── type-b-runbook/        #   SKILL.md + prepare_worklist.py + runbook_template.md
├── docx-extract/              # one folder per skill, kebab-case
│   ├── SKILL.md               #   required entrypoint (frontmatter + instructions)
│   └── helper.py              #   supporting files live next to it
└── ...
```

`.claude/skills/` at the repo root contains one symlink per skill folder, so
Claude Code discovers these skills natively (auto-trigger on matching
requests, `/skill-name` invocation). `skills/` stays the canonical home —
edit here, never in `.claude/skills/`.

## SKILL.md contract

Frontmatter (validated by `tests/test_skills_structure.py`):

| Field | Rule |
|-------|------|
| `name` | Required. Must equal the folder name. Lowercase letters, digits, hyphens; max 64 chars. |
| `description` | Required. **The highest-leverage text in the skill** — it is all Claude sees when deciding whether to trigger it. State what the skill produces *and* when to use it (trigger phrases, prerequisites, what it's NOT for). Max 1024 chars; no `<`/`>`. |
| `argument-hint` | Optional. Autocomplete hint for skills that take arguments, e.g. `[formula|structured] [doc_id]`. |
| `type` | Atlas extension (not part of the open spec; other runtimes ignore it). `deterministic` (Type A) or `llm-runbook` (Type B). |

Body: keep it under 500 lines (progressive disclosure — the body only loads
when the skill triggers, but it then stays in context). Long reference
material belongs in supporting files referenced from `SKILL.md`, like
`structured-extract/prompts/*.md`.

## The two shapes

- **Type A (`deterministic`)** — `SKILL.md` + `helper.py`. Claude Code
  orchestrates; the helper does all plumbing. No LLM reasoning in the step.
- **Type B (`llm-runbook`)** — `SKILL.md` + `prepare_worklist.py` +
  `runbook_template.md`. Deterministic prepare phase writes a worklist and
  runbook; Claude Code executes the runbook with its own vision/reasoning,
  resumable by design. Never an external API.

## Adding a skill

1. Copy the matching `_template/` skeleton to `skills/{new-name}/`.
2. Write the `description` first — it decides whether the skill ever fires.
3. Symlink it for discovery: `ln -s ../../skills/{new-name} .claude/skills/{new-name}`.
4. `pytest tests/test_skills_structure.py` — it enforces everything above.

## Deviations from the community layout, and why

- **`helper.py` at the skill root instead of `scripts/`** — the open spec
  allows supporting files anywhere; these paths are load-bearing across the
  repo docs (`python skills/knowledge-hub/helper.py validate`) and one helper
  per skill doesn't need a subfolder.
- **`prompts/` instead of `references/`** — same idea (files loaded on
  demand), named for what they actually are. Each prompt carries its own
  `prompt_version`.
- **`type` frontmatter** — Atlas needs to distinguish the two shapes for
  validation and onboarding; unknown fields are legal and ignored elsewhere.
