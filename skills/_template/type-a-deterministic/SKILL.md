---
name: my-skill
description: >
  One or two sentences on WHAT this skill produces, then WHEN to use it —
  include the trigger phrases users actually say (e.g. "build the X",
  "regenerate Y"), the prerequisites, and what it is NOT for (name the
  neighboring skill instead). This field is what triggers the skill; spend
  more effort here than anywhere else. Max 1024 chars, no angle brackets.
type: deterministic
---

# my-skill

One-paragraph summary: what this step does and where it sits in the pipeline.

## When to use

Use this skill when the user wants to:
- "trigger phrase one"
- "trigger phrase two"

Do NOT use this skill when:
- Prerequisite outputs don't exist yet — name the upstream skill.
- The request actually belongs to a neighboring skill — name it.

## Inputs

- **Required:** paths / arguments.
- **Config:** optional config files under this skill's folder.

## Outputs

- `artifacts/...` or `knowledge/...` paths, with schemas if structured.

## Procedure

Claude Code should follow these steps when the skill is triggered:

1. **Validate inputs.**
2. **Call `helper.py`.** The helper does all the plumbing — no LLM reasoning
   inside a Type A step.
3. **Report summary** to the user, and name the next skill in the chain.
4. **On error:** surface it clearly; never silently skip.

## Example invocations

- "..."

## Common gotchas

- ...
