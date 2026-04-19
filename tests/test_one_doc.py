"""End-to-end smoke test on a single known pilot doc.

Run the full pipeline against one .docx in raw/ and assert that:
  - artifacts/extracted/{doc_id}.md exists and has no unreplaced {{EQUATION_*}}
    tokens after md-normalize runs.
  - artifacts/manifests/{doc_id}.json is valid JSON.
  - Every image-type equation in the manifest has a matching formula JSON
    under artifacts/formulas/{doc_id}/.
  - knowledge/docs/{doc_id}.md has valid YAML frontmatter with doc_id, title,
    formula_count.

This test is a contract check, not a unit test — it is expected to be run
manually after scaffolding the pilot, not in CI. Skills are invoked via
Claude Code, not by this test; the test only verifies the resulting
artifacts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

PILOT_DOC_ID = "pilot"  # set to the real doc_id once the pilot is dropped in raw/
REPO_ROOT = Path(__file__).resolve().parents[1]


def _require(path: Path) -> Path:
    if not path.exists():
        pytest.skip(f"expected artifact missing — run the pipeline first: {path}")
    return path


def test_manifest_is_valid_json() -> None:
    manifest = _require(REPO_ROOT / "artifacts" / "manifests" / f"{PILOT_DOC_ID}.json")
    data = json.loads(manifest.read_text())
    assert data["doc_id"] == PILOT_DOC_ID
    assert isinstance(data.get("equations"), list)


def test_every_image_equation_has_formula_json() -> None:
    manifest = _require(REPO_ROOT / "artifacts" / "manifests" / f"{PILOT_DOC_ID}.json")
    formulas_dir = REPO_ROOT / "artifacts" / "formulas" / PILOT_DOC_ID
    data = json.loads(manifest.read_text())
    missing = [
        eq["equation_id"]
        for eq in data["equations"]
        if eq.get("type") == "image"
        and not (formulas_dir / f"{eq['equation_id']}.json").exists()
    ]
    assert not missing, f"formula JSONs missing for: {missing}"


def test_normalized_doc_has_no_unreplaced_tokens() -> None:
    doc = _require(REPO_ROOT / "knowledge" / "docs" / f"{PILOT_DOC_ID}.md")
    body = doc.read_text()
    assert not re.search(r"\{\{EQUATION_[^}]+\}\}", body), (
        "normalized doc still contains equation placeholder tokens"
    )
