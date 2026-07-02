"""Page views for the Atlas hub — pure render functions, one per route."""

from __future__ import annotations

from urllib.parse import parse_qs

import dash_bootstrap_components as dbc
from dash import dcc, html

from hub import config
from hub.engine.state import Engine
from hub.ui import components as ui

_START_HERE = [
    "onboarding/welcome",
    "onboarding/first-90-days",
    "compliance/npi-data-handling",
    "compliance/genai-acceptable-use",
    "onboarding/faq",
]


# --------------------------------------------------------------------------
# Home
# --------------------------------------------------------------------------

def home(engine: Engine, history: list[str]) -> html.Div:
    corpus = engine.corpus
    hero = html.Div(
        [
            html.H1("Atlas", className="hero-title"),
            html.P(config.APP_TAGLINE, className="hero-tagline"),
            dbc.Input(
                id={"role": "atlas-go", "loc": "home"},
                placeholder="Search everything — try “NPI”, “PSI threshold”, “first 90 days”…",
                type="search",
                size="lg",
                className="hero-search",
                debounce=True,
            ),
            html.P(
                "…or open the copilot (top right) and just ask.",
                className="text-muted small mt-2",
            ),
        ],
        className="hero",
    )

    channel_cards = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div(ui.channel_meta(c)["icon"], className="channel-icon"),
                            html.H5(dcc.Link(ui.channel_meta(c)["label"],
                                             href=ui.href(f"/channel/{c}"))),
                            html.P(ui.channel_meta(c)["blurb"],
                                   className="text-muted small mb-1"),
                            html.Span(f"{len(corpus.by_channel(c))} items",
                                      className="text-muted small"),
                        ]
                    ),
                    className="channel-card h-100",
                ),
                md=True, xs=6, className="mb-3",
            )
            for c in corpus.channels()
        ],
        className="mb-4",
    )

    start_items = [
        ui.doc_link_item(corpus.docs[d]) for d in _START_HERE if d in corpus.docs
    ]
    recent = sorted(
        (d for d in corpus.docs.values() if d.timestamp),
        key=lambda d: d.timestamp, reverse=True,
    )[:6]
    recent_items = [
        html.Li(
            [ui.channel_badge(d.channel), dcc.Link(d.title, href=ui.href(d.url)),
             html.Span(f" · {d.timestamp}", className="text-muted small")],
            className="mb-2",
        )
        for d in recent
    ]

    reco_ids = engine.recommender.recommend(history or [], k=6)
    reco_items = [
        html.Li(
            [ui.channel_badge(corpus.docs[rid].channel),
             dcc.Link(corpus.docs[rid].title, href=ui.href(corpus.docs[rid].url))],
            className="mb-2",
        )
        for rid, _ in reco_ids if rid in corpus.docs
    ]

    columns = dbc.Row(
        [
            dbc.Col(
                [html.H5("🧭 Start here"), html.Ol(start_items, className="start-list")],
                md=4,
            ),
            dbc.Col(
                [html.H5("🕒 Recently updated"), html.Ul(recent_items, className="plain-list")],
                md=4,
            ),
            dbc.Col(
                [
                    html.H5("✨ Recommended for you"),
                    html.Ul(reco_items, className="plain-list")
                    if reco_items
                    else html.P("Read a few pages and Atlas will suggest what's next.",
                                className="text-muted small"),
                ],
                md=4,
            ),
        ]
    )
    return html.Div([hero, channel_cards, columns])


# --------------------------------------------------------------------------
# Channel
# --------------------------------------------------------------------------

def channel(engine: Engine, chan: str) -> html.Div:
    corpus = engine.corpus
    docs = corpus.by_channel(chan)
    if not docs:
        return not_found(f"No channel “{chan}”.")
    meta = ui.channel_meta(chan)
    header = html.Div(
        [
            html.H2(f"{meta['icon']} {meta['label']}"),
            html.P(meta["blurb"], className="text-muted"),
        ],
        className="page-header",
    )

    if chan == "models":
        model_cards = dbc.Row(
            [
                dbc.Col(ui.model_card(m, corpus), md=6, className="mb-3")
                for m in corpus.models.values()
            ]
        )
        attached = {m.overview for m in corpus.models.values()} | {
            d for m in corpus.models.values() for d in m.artifacts.values()
        }
        loose = [d for d in docs if d.id not in attached]
        loose_block = (
            [html.H5("Other model documents", className="mt-4"),
             dbc.Row([dbc.Col(ui.doc_card(d), md=4, className="mb-3") for d in loose])]
            if loose else []
        )
        return html.Div([header, model_cards, *loose_block])

    grid = dbc.Row([dbc.Col(ui.doc_card(d), md=4, className="mb-3") for d in docs])
    return html.Div([header, grid])


# --------------------------------------------------------------------------
# Document
# --------------------------------------------------------------------------

def doc(engine: Engine, doc_id: str) -> html.Div:
    corpus = engine.corpus
    d = corpus.docs.get(doc_id)
    if d is None:
        return not_found(f"No document “{doc_id}”.")
    model = corpus.model_for_doc(doc_id)

    crumbs = [
        dcc.Link("Home", href=ui.href("/")),
        html.Span(" / "),
        dcc.Link(ui.channel_meta(d.channel)["label"], href=ui.href(f"/channel/{d.channel}")),
    ]
    if model:
        crumbs += [html.Span(" / "), dcc.Link(model.name, href=ui.href(model.url))]
    crumbs += [html.Span(" / "), html.Span(d.title, className="text-muted")]

    header = html.Div(
        [
            html.Div(crumbs, className="breadcrumbs small mb-2"),
            html.H2(d.title),
            html.Div(
                [ui.channel_badge(d.channel), ui.type_badge(d.dtype), ui.tag_chips(d.tags)],
                className="mb-1",
            ),
            ui.meta_line(d),
        ],
        className="page-header",
    )

    related = engine.recommender.related(doc_id, k=5)
    sidebar = html.Div(
        [
            ui.toc_panel(d),
            ui.related_panel(corpus, related),
            ui.backlinks_panel(corpus, d),
            html.Div(
                dbc.Button("💬 Ask the copilot about this page",
                           id={"type": "copilot-open", "loc": "doc"},
                           color="primary", outline=True, size="sm", className="w-100"),
                className="sidebar-panel",
            ),
        ],
        className="doc-sidebar",
    )

    return html.Div(
        [
            header,
            dbc.Row(
                [
                    dbc.Col(html.Div(ui.section_blocks(d), className="doc-body"), lg=8),
                    dbc.Col(sidebar, lg=4),
                ]
            ),
        ]
    )


# --------------------------------------------------------------------------
# Model space
# --------------------------------------------------------------------------

def model(engine: Engine, model_id: str, query: str = "") -> html.Div:
    corpus = engine.corpus
    m = corpus.models.get(model_id)
    if m is None:
        return not_found(f"No model space “{model_id}”.")
    meta = m.meta
    want_tab = (parse_qs(query.lstrip("?")).get("tab", [""])[0]) if query else ""

    header = html.Div(
        [
            html.Div(
                [
                    dcc.Link("Home", href=ui.href("/")), html.Span(" / "),
                    dcc.Link("Models", href=ui.href("/channel/models")), html.Span(" / "),
                    html.Span(m.name, className="text-muted"),
                ],
                className="breadcrumbs small mb-2",
            ),
            html.H2(m.name),
            html.P(meta.get("description", ""), className="text-muted"),
            dbc.Row(
                [
                    dbc.Col(_fact("Owner", meta.get("owner", "—")), md=3, xs=6),
                    dbc.Col(_fact("Status", meta.get("status", "—")), md=3, xs=6),
                    dbc.Col(_fact("Validation", meta.get("validation_status", "—")), md=3, xs=6),
                    dbc.Col(_fact("Materiality", meta.get("materiality_tier", "—")), md=3, xs=6),
                ],
                className="model-facts mb-3",
            ),
        ],
        className="page-header",
    )

    tabs = []
    overview = corpus.docs.get(m.overview)
    if overview:
        tabs.append(dbc.Tab(html.Div(ui.section_blocks(overview), className="doc-body pt-3"),
                            label="Overview", tab_id="Overview"))
    ordered = ["Whitepaper", "User Guide", "Monitoring Plan"]
    roles = ordered + [r for r in m.artifacts if r not in ordered]
    for role in roles:
        doc_id = m.artifacts.get(role)
        if not doc_id:
            continue
        d = corpus.docs.get(doc_id)
        if d:
            tabs.append(
                dbc.Tab(
                    html.Div(
                        [
                            html.Div(
                                dcc.Link("Open as standalone page ↗", href=ui.href(d.url),
                                         className="small"),
                                className="text-end mt-2",
                            ),
                            html.Div(ui.section_blocks(d), className="doc-body"),
                        ]
                    ),
                    label=role, tab_id=role,
                )
            )

    active = want_tab if want_tab in {t.tab_id for t in tabs} else "Overview"
    return html.Div([header, dbc.Tabs(tabs, active_tab=active, className="model-tabs")])


def _fact(label: str, value: str) -> html.Div:
    return html.Div(
        [html.Div(label, className="text-muted small"), html.Div(value, className="fw-semibold")],
        className="model-fact",
    )


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------

def search(engine: Engine, query: str = "") -> html.Div:
    params = parse_qs(query.lstrip("?")) if query else {}
    q = params.get("q", [""])[0]
    corpus = engine.corpus
    # Pattern-matching IDs: these controls exist only on this page, and plain
    # string IDs referenced by callbacks must exist on every page — the cause
    # of the original "search does nothing" bug.
    controls = dbc.Row(
        [
            dbc.Col(
                dbc.Input(id={"role": "search-q", "idx": 0}, value=q, type="search",
                          size="lg", placeholder="Search Atlas…", debounce=True),
                md=8,
            ),
            dbc.Col(
                dbc.Checklist(
                    id={"role": "search-ch", "idx": 0},
                    options=[{"label": ui.channel_meta(c)["label"], "value": c}
                             for c in corpus.channels()],
                    value=[],
                    inline=True,
                    className="pt-2",
                ),
                md=4,
            ),
        ],
        className="mb-3",
    )
    return html.Div(
        [
            html.H2("Search"),
            controls,
            html.Div(search_results(engine, q, []), id={"role": "search-results", "idx": 0}),
        ]
    )


def search_results(engine: Engine, q: str, channels: list[str]) -> list:
    if not (q or "").strip():
        return [html.P("Type a query — every section of every document is indexed.",
                       className="text-muted")]
    hits = engine.search.search(q, channels=channels or None, limit=25)
    if not hits:
        return [html.P(f"No results for “{q}”.", className="text-muted")]
    items = []
    for h in hits:
        items.append(
            html.Div(
                [
                    html.Div([ui.channel_badge(h.channel), ui.type_badge(h.dtype)]),
                    html.H5(
                        dcc.Link(
                            f"{h.title}" + (f" › {h.heading}" if h.heading else ""),
                            href=ui.href(h.url),
                        ),
                        className="mb-1",
                    ),
                    ui.render_markdown(h.snippet, className="atlas-md search-snippet"),
                ],
                className="search-hit",
            )
        )
    return [html.P(f"{len(hits)} results for “{q}”", className="text-muted small"), *items]


# --------------------------------------------------------------------------
# 404
# --------------------------------------------------------------------------

def not_found(msg: str = "Page not found.") -> html.Div:
    return html.Div(
        [
            html.H2("Hmm — nothing here"),
            html.P(msg, className="text-muted"),
            dcc.Link("← Back to Atlas home", href=ui.href("/")),
        ],
        className="pt-5 text-center",
    )
