"""Claude Code copilot backend.

Uses the **local `claude` CLI** — the tool Atlas users already have installed
and authenticated — as the copilot's synthesis engine. This keeps the repo's
core rule intact: no API keys, no SDK imports, no hosted-model calls from
Python. The CLI is invoked headless (`claude -p`), with all tools disallowed,
and only ever sees the retrieval passages the Atlas engine hands it.

If the CLI is missing, slow, or errors, the copilot silently falls back to
its offline extractive mode — the hub never breaks without Claude.
"""

from __future__ import annotations

import os
import shutil
import subprocess

_DISALLOWED_TOOLS = "Bash,Read,Edit,Write,Glob,Grep,WebFetch,WebSearch,Task,Agent,NotebookEdit"

_SYSTEM = """\
You are the Atlas copilot — the assistant inside a team knowledge hub for a
model analytics team (channels: onboarding, models, compliance, lessons
learned, tooling).

Rules:
- Answer ONLY from the context passages below. Do not use tools. Do not add
  facts that are not in the context.
- Quote thresholds, numbers, and formulas verbatim — never paraphrase them.
- When you use a passage, cite it inline as a markdown link with its given
  URL, e.g. [NPI data handling › The three rules](/doc/compliance/npi-data-handling#the-three-rules).
- If the context does not contain the answer, say so in one sentence and
  point to the most likely channel instead. Do not guess.
- Style: concise (under 180 words), markdown, bold the key terms.
"""


def cli_available(binary: str = "claude") -> bool:
    return shutil.which(binary) is not None


class ClaudeCodeAdapter:
    """LLMAdapter implementation backed by the local Claude Code CLI."""

    name = "Claude Code"

    def __init__(self, binary: str = "claude", timeout: int | None = None,
                 model: str | None = None, cwd: str | None = None):
        self.binary = binary
        self.timeout = timeout or int(os.environ.get("ATLAS_COPILOT_TIMEOUT", "90"))
        self.model = model or os.environ.get("ATLAS_CLAUDE_MODEL", "")
        self.cwd = cwd

    def generate(self, question: str, passages: list[dict],
                 history: list[tuple[str, str]] | None = None) -> str:
        prompt = self._build_prompt(question, passages, history or [])
        cmd = [self.binary, "-p", prompt,
               "--output-format", "text",
               "--disallowedTools", _DISALLOWED_TOOLS]
        if self.model:
            cmd += ["--model", self.model]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=self.timeout, cwd=self.cwd,
            )
        except (subprocess.SubprocessError, OSError) as e:
            raise RuntimeError(f"claude CLI failed: {e}") from e
        text = (result.stdout or "").strip()
        if result.returncode != 0 or not text:
            raise RuntimeError(
                f"claude CLI exit {result.returncode}: {(result.stderr or '')[:200]}"
            )
        return text

    @staticmethod
    def _build_prompt(question: str, passages: list[dict],
                      history: list[tuple[str, str]]) -> str:
        parts = [_SYSTEM]
        if history:
            parts.append("<conversation-so-far>")
            for role, text in history[-6:]:
                parts.append(f"{role}: {text[:500]}")
            parts.append("</conversation-so-far>")
        parts.append("<context>")
        for i, p in enumerate(passages, 1):
            label = f"{p['title']} › {p['heading']}" if p.get("heading") else p["title"]
            parts.append(f"[{i}] {label} ({p['url']})\n{p['text'][:1500]}")
        parts.append("</context>")
        parts.append(f"Question: {question}")
        return "\n\n".join(parts)
