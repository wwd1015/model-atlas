"""Contract tests for the Atlas hub engine and content bundle.

These run in CI (plain pytest) — they exercise the real `content/` bundle,
so they double as a conformance gate: broken frontmatter or a missing OKF
`type` fails the build before it ever hits the hub.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from hub.engine.copilot import Copilot, load_adapter  # noqa: E402
from hub.engine.loader import load_corpus, parse_frontmatter, slugify, validate_bundle  # noqa: E402
from hub.engine.recommend import Recommender  # noqa: E402
from hub.engine.search import SearchEngine  # noqa: E402


@pytest.fixture(scope="module")
def corpus():
    return load_corpus()


@pytest.fixture(scope="module")
def engine(corpus):
    search = SearchEngine(corpus)
    rec = Recommender(corpus)
    # adapter=None → offline extractive: deterministic, no CLI dependency in CI.
    return search, rec, Copilot(corpus, search, rec, adapter=None)


# -- OKF bundle conformance --------------------------------------------------

def test_bundle_is_okf_conformant():
    assert validate_bundle() == []


def test_corpus_loads_without_issues(corpus):
    assert corpus.issues == []
    assert len(corpus.docs) >= 20


def test_every_content_doc_has_type_and_title(corpus):
    for doc in corpus.docs.values():
        assert doc.dtype, f"{doc.id} missing type"
        assert doc.title, f"{doc.id} missing title"


def test_channels_present(corpus):
    assert set(corpus.channels()) >= {"onboarding", "models", "compliance", "lessons", "tooling"}


# -- loader mechanics ---------------------------------------------------------

def test_slugify_matches_pipeline_convention():
    assert slugify("Loss Given Default (LGD)") == "loss-given-default-lgd"
    assert slugify("  Días 31–60 — Contribute ") == "d-as-31-60-contribute"


def test_frontmatter_round_trip():
    meta, body = parse_frontmatter("---\ntype: Guide\ntitle: X\n---\n\n# X\nbody\n")
    assert meta["type"] == "Guide"
    assert body.strip().startswith("# X")


def test_frontmatter_tolerates_absence():
    meta, body = parse_frontmatter("# no frontmatter\n")
    assert meta == {} and body.startswith("# no")


def test_wiki_links_resolved_and_backlinked(corpus):
    welcome = corpus.docs["onboarding/welcome"]
    assert "compliance/npi-data-handling" in welcome.links_out
    assert "[[" not in welcome.body  # all wiki syntax rewritten
    npi = corpus.docs["compliance/npi-data-handling"]
    assert "onboarding/welcome" in npi.backlinks


def test_model_spaces_assembled(corpus):
    m = corpus.models["cre-pd-v2"]
    assert m.meta.get("owner")
    assert {"Whitepaper", "User Guide", "Monitoring Plan"} <= set(m.artifacts)
    assert corpus.model_for_doc(m.artifacts["Whitepaper"]) is m


def test_glossary_extraction(corpus):
    gloss = corpus.glossary()
    assert "psi" in gloss and "npi" in gloss
    term, definition, locator = gloss["psi"]
    assert "#" in locator and definition


# -- search -------------------------------------------------------------------

def test_search_finds_the_right_section(engine):
    search, _, _ = engine
    hits = search.search("NPI data handling")
    assert hits and hits[0].doc_id == "compliance/npi-data-handling"


def test_search_question_furniture_ignored(engine):
    search, _, _ = engine
    hits = search.search("How do we handle NPI data?")
    assert hits[0].doc_id == "compliance/npi-data-handling"


def test_search_channel_filter(engine):
    search, _, _ = engine
    hits = search.search("monitoring", channels=["lessons"])
    assert hits and all(h.channel == "lessons" for h in hits)


def test_search_snippet_is_inline_markdown(engine):
    search, _, _ = engine
    snip = search.search("PSI threshold")[0].snippet
    assert "\n" not in snip and "\x02" not in snip


def test_fallback_search_agrees_on_top_doc(corpus, engine):
    search, _, _ = engine
    fb = search._fallback_search(["npi", "data", "handling"], channels=None, limit=5)
    assert fb and fb[0].doc_id == "compliance/npi-data-handling"


# -- recommendations ----------------------------------------------------------

def test_related_excludes_self_and_is_relevant(engine, corpus):
    _, rec, _ = engine
    related = rec.related("compliance/npi-data-handling", k=5)
    ids = [r for r, _ in related]
    assert "compliance/npi-data-handling" not in ids
    assert "compliance/genai-acceptable-use" in ids  # linked + lexically close


def test_history_recommendations_exclude_viewed(engine):
    _, rec, _ = engine
    history = ["onboarding/welcome", "compliance/npi-data-handling"]
    recs = [r for r, _ in rec.recommend(history)]
    assert recs and not set(recs) & set(history)


# -- copilot ------------------------------------------------------------------

def test_copilot_grounds_answers_with_citations(engine):
    _, _, cop = engine
    ans = cop.ask("How do we handle NPI data?")
    assert ans.citations, "answer must cite sources"
    assert ans.citations[0].doc_id == "compliance/npi-data-handling"
    assert "/doc/compliance/npi-data-handling" in ans.text


def test_copilot_glossary_intent(engine):
    _, _, cop = engine
    ans = cop.ask("what is PSI?")
    assert "Population Stability Index" in ans.text
    assert ans.citations and ans.citations[0].doc_id == "onboarding/glossary"


def test_copilot_owner_intent(engine):
    _, _, cop = engine
    ans = cop.ask("who owns the CRE PD model?")
    assert "J. Rivera" in ans.text


def test_copilot_no_hits_degrades_gracefully(engine):
    _, _, cop = engine
    ans = cop.ask("zzzqqxx nonexistent topic")
    assert ans.text and not ans.citations


def test_copilot_help(engine):
    _, _, cop = engine
    ans = cop.ask("help")
    assert "copilot" in ans.text.lower() and ans.suggestions


# -- adapter selection ---------------------------------------------------------

def test_load_adapter_respects_off(monkeypatch):
    monkeypatch.setenv("ATLAS_COPILOT", "off")
    assert load_adapter() is None


def test_load_adapter_auto_detects_cli(monkeypatch):
    import hub.engine.claude_adapter as ca

    monkeypatch.setenv("ATLAS_COPILOT", "auto")
    monkeypatch.setattr(ca, "cli_available", lambda binary="claude": False)
    assert load_adapter() is None
    monkeypatch.setattr(ca, "cli_available", lambda binary="claude": True)
    adapter = load_adapter()
    assert adapter is not None and adapter.name == "Claude Code"


def test_claude_prompt_is_grounded():
    from hub.engine.claude_adapter import ClaudeCodeAdapter

    prompt = ClaudeCodeAdapter._build_prompt(
        "what are the PSI thresholds?",
        [{"title": "Monitoring Plan", "heading": "Thresholds",
          "url": "/doc/x#thresholds", "text": "PSI < 0.10 stable"}],
        [("user", "hi"), ("assistant", "hello")],
    )
    assert "ONLY from the context" in prompt
    assert "/doc/x#thresholds" in prompt and "PSI < 0.10 stable" in prompt
    assert "<conversation-so-far>" in prompt
    assert prompt.rstrip().endswith("what are the PSI thresholds?")


# -- app routes ---------------------------------------------------------------

def test_app_renders_all_routes():
    from hub.app import render_page

    for path, query in [
        ("/", ""), ("/channel/models", ""), ("/doc/onboarding/welcome", ""),
        ("/model/cre-pd-v2", "?tab=Whitepaper"), ("/search", "?q=NPI"), ("/bogus", ""),
    ]:
        out = render_page(path, query, [])
        assert out is not None
