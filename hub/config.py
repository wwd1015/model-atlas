"""Central configuration for the Atlas hub.

Everything is path- or env-driven; no keys in the repo — the optional
hosted-LLM copilot backend is configured entirely via deploy-time env vars
(ATLAS_LLM_BASE_URL / ATLAS_LLM_API_KEY / ATLAS_LLM_MODEL).
Override roots with env vars when deploying (e.g. on Posit Connect).
"""

from __future__ import annotations

import os
from pathlib import Path

# Repo root. ATLAS_ROOT overrides for deployments where the app bundle
# is copied elsewhere (Posit Connect content directory, Docker, ...).
ROOT = Path(os.environ.get("ATLAS_ROOT", Path(__file__).resolve().parents[1]))

# The hand-authored OKF bundle (markdown + YAML frontmatter concepts).
CONTENT_DIR = Path(os.environ.get("ATLAS_CONTENT_DIR", ROOT / "content"))

# Pipeline-produced whitepapers (read-only from the hub's perspective).
KNOWLEDGE_DOCS_DIR = Path(os.environ.get("ATLAS_KNOWLEDGE_DOCS", ROOT / "knowledge" / "docs"))

APP_TITLE = "Atlas"
APP_TAGLINE = "The team's second brain — onboarding, models, compliance, lessons, tooling."

# Optional custom copilot LLM adapter, "package.module:factory" — the escape
# hatch for backends that don't speak the OpenAI chat-completions format.
# Most deployments won't need it: the bundled backends (Claude Code CLI,
# OpenAI-compatible API via ATLAS_LLM_* env vars, extractive fallback) are
# selected automatically in copilot.load_adapter().
COPILOT_ADAPTER = os.environ.get("ATLAS_COPILOT_ADAPTER", "")

# Channel registry — single source of truth for navigation and cards.
# Keys are the top-level directories of the content bundle.
CHANNELS: dict[str, dict] = {
    "onboarding": {
        "label": "Onboarding",
        "icon": "🧭",
        "blurb": "Start here: role orientation, first 90 days, FAQ, glossary, who to ask.",
    },
    "models": {
        "label": "Models",
        "icon": "📐",
        "blurb": "One space per model: whitepaper, user guide, monitoring plan — all in one place.",
    },
    "compliance": {
        "label": "Compliance",
        "icon": "🛡️",
        "blurb": "NPI data handling, GenAI acceptable use, model risk basics.",
    },
    "lessons": {
        "label": "Lessons Learned",
        "icon": "📓",
        "blurb": "Post-mortems and case studies — the mistakes we only want to make once.",
    },
    "tooling": {
        "label": "Tooling",
        "icon": "🧰",
        "blurb": "Catalog of the tools the team has already built, and how to use them.",
    },
}

DEFAULT_CHANNEL_META = {"label": None, "icon": "📁", "blurb": ""}
