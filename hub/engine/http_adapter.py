"""Generic hosted-LLM copilot backend (OpenAI-compatible chat completions).

Lets the copilot use **any** LLM service that speaks the de-facto standard
``POST {base_url}/chat/completions`` format — OpenAI, Azure OpenAI, Gemini's
compatibility endpoint, vLLM, Ollama, LiteLLM, or an enterprise gateway.
Stdlib-only (`urllib`): no vendor SDK enters the repo.

Configuration is env-only, set at deploy time — never a key in the repo:

    ATLAS_LLM_BASE_URL   activates this backend, e.g. https://gateway.corp/v1
    ATLAS_LLM_MODEL      model name passed through (most servers require it)
    ATLAS_LLM_API_KEY    bearer token (optional — some gateways use network auth)
    ATLAS_LLM_TIMEOUT    seconds, default 60

Like every backend, it only writes prose over the retrieval passages the
Atlas engine hands it; on any failure the copilot falls back to extractive.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

# Single source of truth for the copilot's grounding rules.
from hub.engine.claude_adapter import _SYSTEM as SYSTEM_PROMPT


def configured() -> bool:
    return bool(os.environ.get("ATLAS_LLM_BASE_URL", "").strip())


class OpenAICompatAdapter:
    """LLMAdapter implementation for any OpenAI-compatible endpoint."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None,
                 model: str | None = None, timeout: int | None = None):
        self.base_url = (base_url or os.environ.get("ATLAS_LLM_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("ATLAS_LLM_API_KEY", "")
        self.model = model or os.environ.get("ATLAS_LLM_MODEL", "")
        self.timeout = timeout or int(os.environ.get("ATLAS_LLM_TIMEOUT", "60"))
        if not self.base_url:
            raise ValueError("OpenAICompatAdapter requires ATLAS_LLM_BASE_URL")
        self.name = f"LLM API · {self.model}" if self.model else "LLM API"

    def generate(self, question: str, passages: list[dict],
                 history: list[tuple[str, str]] | None = None) -> str:
        payload: dict = {
            "messages": self._build_messages(question, passages, history or []),
            "temperature": 0.2,
        }
        if self.model:
            payload["model"] = self.model
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.load(resp)
        except (urllib.error.URLError, OSError, TimeoutError, ValueError) as e:
            raise RuntimeError(f"LLM API call failed: {e}") from e
        try:
            text = (data["choices"][0]["message"]["content"] or "").strip()
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"LLM API returned an unexpected shape: {e}") from e
        if not text:
            raise RuntimeError("LLM API returned an empty answer")
        return text

    @staticmethod
    def _build_messages(question: str, passages: list[dict],
                        history: list[tuple[str, str]]) -> list[dict]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for role, text in history[-6:]:
            api_role = "assistant" if role.lower().startswith("a") else "user"
            messages.append({"role": api_role, "content": text[:500]})
        blocks = []
        for i, p in enumerate(passages, 1):
            label = f"{p['title']} › {p['heading']}" if p.get("heading") else p["title"]
            blocks.append(f"[{i}] {label} ({p['url']})\n{p['text'][:1500]}")
        context = "\n\n".join(blocks)
        messages.append({
            "role": "user",
            "content": f"<context>\n{context}\n</context>\n\nQuestion: {question}",
        })
        return messages
