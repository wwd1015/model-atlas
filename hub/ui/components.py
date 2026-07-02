"""Reusable UI building blocks for the Atlas hub."""

from __future__ import annotations

import re

import dash_bootstrap_components as dbc
from dash import dcc, html

from hub import config
from hub.engine.loader import Corpus, Doc, Model

# Set by app.py at startup so content links work under a deployment
# prefix (e.g. Posit Connect serves the app at /content/<guid>/).
_PREFIX = "/"


def set_prefix(prefix: str) -> None:
    global _PREFIX
    _PREFIX = prefix or "/"


def href(path: str) -> str:
    """Prefix-aware absolute link for html/dcc components."""
    return _PREFIX.rstrip("/") + path


def _rewrite_md_links(text: str) -> str:
    """Rewrite root-absolute markdown links to the deployment prefix."""
    if _PREFIX in ("", "/"):
        return text
    return re.sub(r"\]\(/", "](" + _PREFIX.rstrip("/") + "/", text)


def render_markdown(text: str, className: str = "atlas-md") -> dcc.Markdown:
    return dcc.Markdown(
        _rewrite_md_links(text),
        mathjax=True,
        className=className,
    )


_CHANNEL_COLOR = {
    "onboarding": "primary",
    "models": "success",
    "compliance": "danger",
    "lessons": "warning",
    "tooling": "info",
}


def channel_meta(channel: str) -> dict:
    meta = config.CHANNELS.get(channel, dict(config.DEFAULT_CHANNEL_META))
    return {**meta, "label": meta.get("label") or channel.title()}


def channel_badge(channel: str) -> dbc.Badge:
    meta = channel_meta(channel)
    return dbc.Badge(
        meta["label"],
        color=_CHANNEL_COLOR.get(channel, "secondary"),
        className="me-1 channel-badge",
        href=href(f"/channel/{channel}"),
    )


def type_badge(dtype: str) -> dbc.Badge:
    return dbc.Badge(dtype, color="light", text_color="dark", className="me-1 type-badge")


def tag_chips(tags: list[str]) -> html.Span:
    return html.Span(
        [dbc.Badge(t, color="secondary", className="me-1 tag-chip", pill=True) for t in tags],
    )


def meta_line(doc: Doc) -> html.Div:
    bits = []
    if doc.owner:
        bits.append(html.Span(f"👤 {doc.owner}", className="me-3"))
    if doc.timestamp:
        bits.append(html.Span(f"🕒 {doc.timestamp}", className="me-3"))
    return html.Div(bits, className="text-muted small")


def doc_card(doc: Doc, show_channel: bool = False) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [channel_badge(doc.channel) if show_channel else None, type_badge(doc.dtype)],
                    className="mb-1",
                ),
                html.H5(dcc.Link(doc.title, href=href(doc.url), className="doc-card-title")),
                html.P(doc.description, className="text-muted mb-2 small"),
                meta_line(doc),
            ]
        ),
        className="doc-card h-100",
    )


def doc_link_item(doc: Doc, note: str = "") -> html.Li:
    return html.Li(
        [
            dcc.Link(doc.title, href=href(doc.url)),
            html.Span(f" — {note or doc.description}", className="text-muted small"),
        ],
        className="mb-1",
    )


def model_card(model: Model, corpus: Corpus) -> dbc.Card:
    meta = model.meta
    rows = [
        ("Owner", meta.get("owner", "—")),
        ("Status", meta.get("status", "—")),
        ("Validation", meta.get("validation_status", "—")),
        ("Tier", meta.get("materiality_tier", "—")),
    ]
    artifacts = []
    for role in ("Whitepaper", "User Guide", "Monitoring Plan"):
        if role in model.artifacts:
            artifacts.append(
                dbc.Badge(role, color="success", className="me-1", pill=True,
                          href=href(f"{model.url}?tab={role}")))
    for role, doc_id in model.artifacts.items():
        if role not in ("Whitepaper", "User Guide", "Monitoring Plan"):
            artifacts.append(
                dbc.Badge(role, color="secondary", className="me-1", pill=True,
                          href=href(f"{model.url}?tab={role}")))
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5(dcc.Link(model.name, href=href(model.url), className="doc-card-title")),
                html.P(meta.get("description", ""), className="text-muted small mb-2"),
                html.Table(
                    [html.Tr([html.Td(k, className="text-muted pe-3 small"),
                              html.Td(v, className="small")]) for k, v in rows],
                    className="mb-2",
                ),
                html.Div(artifacts),
            ]
        ),
        className="doc-card model-card h-100",
    )


def section_blocks(doc: Doc) -> list:
    """Render a doc's sections as anchored blocks (`#<slug>` deep links work)."""
    blocks = []
    for sec in doc.sections:
        children = []
        if sec.heading and not (sec.level == 1 and sec.heading.strip() == doc.title.strip()):
            tag = {1: html.H2, 2: html.H3, 3: html.H4, 4: html.H5}.get(sec.level, html.H4)
            children.append(
                tag(
                    [sec.heading, html.A("¶", href=f"#{sec.anchor}", className="anchor-link")],
                    className="section-heading",
                )
            )
        if sec.text:
            children.append(render_markdown(sec.text))
        if children:
            blocks.append(html.Div(children, id=sec.anchor or f"top-{doc.id.replace('/', '-')}",
                                   className="doc-section"))
    return blocks


def sidebar_panel(title: str, children: list, empty_hint: str = "") -> html.Div:
    if not children and not empty_hint:
        return html.Div()
    return html.Div(
        [
            html.H6(title, className="sidebar-title"),
            html.Div(children) if children else html.P(empty_hint, className="text-muted small"),
        ],
        className="sidebar-panel",
    )


def toc_panel(doc: Doc) -> html.Div:
    items = [
        html.Li(
            html.A(sec.heading, href=f"#{sec.anchor}", className="toc-link"),
            className=f"toc-l{sec.level}",
        )
        for sec in doc.sections
        if sec.heading and not (sec.level == 1 and sec.heading.strip() == doc.title.strip())
    ]
    return sidebar_panel("On this page", [html.Ul(items, className="toc-list")] if items else [])


def related_panel(corpus: Corpus, related: list[tuple[str, float]]) -> html.Div:
    items = []
    for rel_id, _score in related:
        rel = corpus.docs.get(rel_id)
        if rel:
            items.append(
                html.Li(
                    [dcc.Link(rel.title, href=href(rel.url)),
                     html.Span(f" · {channel_meta(rel.channel)['label']}",
                               className="text-muted small")],
                    className="mb-1",
                )
            )
    return sidebar_panel("Related", [html.Ul(items, className="plain-list")] if items else [])


def backlinks_panel(corpus: Corpus, doc: Doc) -> html.Div:
    items = []
    for src_id in sorted(doc.backlinks):
        src = corpus.docs.get(src_id)
        if src:
            items.append(html.Li(dcc.Link(src.title, href=href(src.url)), className="mb-1"))
    return sidebar_panel(
        "Linked from", [html.Ul(items, className="plain-list")] if items else [],
        empty_hint="Nothing links here yet.",
    )
