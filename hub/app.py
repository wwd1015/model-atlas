"""Atlas — the knowledge hub app.

Run locally:      python -m hub.app        → http://127.0.0.1:8050
Posit Connect:    rsconnect deploy dash . --entrypoint hub.app:app
Any WSGI host:    gunicorn hub.app:server

No API keys, no hosted-model calls: search and copilot run fully offline.
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

# Allow `python hub/app.py` as well as `python -m hub.app`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import dash_bootstrap_components as dbc
from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update

from hub import config
from hub.engine.state import get_engine
from hub.ui import components as ui
from hub.ui import views

app = Dash(
    __name__,
    title=config.APP_TITLE,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
)
server = app.server  # WSGI entrypoint (gunicorn / Posit Connect)

ui.set_prefix(app.config.requests_pathname_prefix)

_engine = get_engine()


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

def _navbar() -> dbc.Navbar:
    nav_items = [
        dbc.NavItem(dbc.NavLink(ui.channel_meta(c)["label"], href=ui.href(f"/channel/{c}")))
        for c in _engine.corpus.channels()
    ]
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand("🗺️ Atlas", href=ui.href("/"), className="fw-bold"),
                dbc.Nav(nav_items, navbar=True, className="me-auto"),
                dbc.Input(
                    id={"role": "atlas-go", "loc": "nav"},
                    placeholder="Search…  ⏎",
                    type="search",
                    size="sm",
                    className="nav-search me-2",
                    debounce=True,
                ),
                dbc.Button("💬 Copilot", id="copilot-toggle", color="light", size="sm"),
            ],
            fluid=True,
        ),
        color="dark",
        dark=True,
        className="atlas-navbar",
        sticky="top",
    )


def _copilot_canvas() -> dbc.Offcanvas:
    mode = _engine.copilot.mode
    mode_badge = dbc.Badge(
        ("⚡ " if _engine.copilot.adapter else "📎 ") + mode,
        color="success" if _engine.copilot.adapter else "secondary",
        className="mb-2 copilot-mode-badge",
    )
    return dbc.Offcanvas(
        [
            mode_badge,
            dcc.Loading(
                [
                    html.Div(id="copilot-messages", className="copilot-messages"),
                    html.Div(id="copilot-status"),
                ],
                type="dot",
                color="#1a5276",
                parent_className="copilot-loading",
            ),
            html.Div(id="copilot-suggestions", className="copilot-suggestions"),
            dbc.InputGroup(
                [
                    dbc.Input(id="copilot-input", placeholder="Ask Atlas anything…",
                              type="text", debounce=True),
                    dbc.Button("Ask", id="copilot-send", color="primary"),
                ],
                className="copilot-inputgroup",
            ),
            html.P(
                "Grounded answers only — every claim links to its source section.",
                className="text-muted small mt-2 mb-0",
            ),
        ],
        id="copilot-canvas",
        title="Atlas Copilot",
        placement="end",
        backdrop=False,
        scrollable=True,
        className="copilot-canvas",
    )


def _footer() -> html.Footer:
    okf_v = _engine.corpus.bundle_meta.get("okf_version", "0.1")
    return html.Footer(
        html.Div(
            f"Atlas · OKF bundle v{okf_v} · {len(_engine.corpus.docs)} concepts · "
            f"copilot: {_engine.copilot.mode} · runs locally or on Posit Connect · no API keys",
            className="text-muted small text-center py-3",
        )
    )


app.layout = html.Div(
    [
        # "callback-nav": URL writes from callbacks (navbar/home search) must
        # trigger client-side navigation — refresh=False updates the address
        # bar without re-firing the router, leaving the old page in place.
        dcc.Location(id="url", refresh="callback-nav"),
        dcc.Store(id="atlas-history", storage_type="session", data=[]),
        dcc.Store(id="atlas-chat", storage_type="session", data=[]),
        html.Div(id="atlas-noop"),
        _navbar(),
        dbc.Container(html.Div(id="page-content"), fluid=False, className="page-container"),
        _copilot_canvas(),
        _footer(),
    ]
)


# --------------------------------------------------------------------------
# Routing
# --------------------------------------------------------------------------

def _route(pathname: str) -> str:
    stripped = app.strip_relative_path(pathname or "")
    return stripped or ""


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("url", "search"),
    State("atlas-history", "data"),
)
def render_page(pathname, query, history):
    engine = get_engine()
    path = _route(pathname)
    if path == "":
        return views.home(engine, history or [])
    if path.startswith("channel/"):
        return views.channel(engine, path.removeprefix("channel/"))
    if path.startswith("doc/"):
        return views.doc(engine, path.removeprefix("doc/"))
    if path.startswith("model/"):
        return views.model(engine, path.removeprefix("model/"), query or "")
    if path == "search":
        return views.search(engine, query or "")
    return views.not_found()


@app.callback(
    Output("atlas-history", "data"),
    Input("url", "pathname"),
    State("atlas-history", "data"),
)
def track_history(pathname, history):
    path = _route(pathname)
    if not path.startswith("doc/"):
        return no_update
    doc_id = path.removeprefix("doc/")
    history = [h for h in (history or []) if h != doc_id] + [doc_id]
    return history[-20:]


# Scroll to the URL hash after page render (deep links to section anchors).
app.clientside_callback(
    """
    function(href) {
        const hash = window.location.hash;
        if (hash) {
            setTimeout(function() {
                const el = document.getElementById(hash.slice(1));
                if (el) el.scrollIntoView({behavior: 'smooth', block: 'start'});
            }, 200);
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("atlas-noop", "children"),
    Input("url", "href"),
)


# --------------------------------------------------------------------------
# Search navigation (navbar + home hero) and search-page refinement.
#
# All page-specific controls use pattern-matching IDs: a plain string ID that
# is missing from the current page prevents its callback from firing at all —
# the cause of the original "search does nothing" bug.
# --------------------------------------------------------------------------

@app.callback(
    Output("url", "href", allow_duplicate=True),
    Input({"role": "atlas-go", "loc": ALL}, "n_submit"),
    State({"role": "atlas-go", "loc": ALL}, "value"),
    State({"role": "atlas-go", "loc": ALL}, "id"),
    prevent_initial_call=True,
)
def go_search(_submits, values, ids):
    trigger = ctx.triggered_id
    if not isinstance(trigger, dict) or not ctx.triggered[0]["value"]:
        return no_update  # component mount, not an Enter press
    for i, cid in enumerate(ids):
        if cid == trigger:
            value = (values[i] or "").strip()
            if value:
                return ui.href(f"/search?q={quote(value)}")
    return no_update


@app.callback(
    Output({"role": "search-results", "idx": ALL}, "children"),
    Input({"role": "search-q", "idx": ALL}, "n_submit"),
    Input({"role": "search-ch", "idx": ALL}, "value"),
    State({"role": "search-q", "idx": ALL}, "value"),
    prevent_initial_call=True,
)
def refine_search(_submits, channel_values, query_values):
    if not query_values:  # search page not mounted
        return []
    q = (query_values[0] or "").strip()
    channels = (channel_values[0] if channel_values else []) or []
    return [views.search_results(get_engine(), q, channels)]


# --------------------------------------------------------------------------
# Copilot
# --------------------------------------------------------------------------

@app.callback(
    Output("copilot-canvas", "is_open"),
    Input("copilot-toggle", "n_clicks"),
    # Doc pages carry an extra "ask about this page" button. It must be a
    # pattern-matching input: a plain ID that is absent from the current page
    # keeps the whole callback from firing — the original "copilot button does
    # nothing on the home page" bug.
    Input({"type": "copilot-open", "loc": ALL}, "n_clicks"),
    State("copilot-canvas", "is_open"),
    prevent_initial_call=True,
)
def toggle_copilot(_n1, _open_clicks, is_open):
    if isinstance(ctx.triggered_id, dict):  # "ask about this page"
        if not ctx.triggered[0]["value"]:
            return no_update  # button just mounted, not clicked
        return True
    return not is_open


@app.callback(
    Output("atlas-chat", "data"),
    Output("copilot-input", "value"),
    Output("copilot-status", "children"),
    Input("copilot-send", "n_clicks"),
    Input("copilot-input", "n_submit"),
    Input({"type": "copilot-sugg", "q": ALL}, "n_clicks"),
    State("copilot-input", "value"),
    State("atlas-chat", "data"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def copilot_ask(_clicks, _submit, _sugg_clicks, value, chat, pathname):
    trigger = ctx.triggered_id
    if isinstance(trigger, dict):  # suggestion chip
        if not ctx.triggered[0]["value"]:
            return no_update, no_update, no_update
        question = trigger["q"]
    else:
        question = (value or "").strip()
        if not question:
            return no_update, no_update, no_update

    path = _route(pathname)
    scope = path.removeprefix("doc/") if path.startswith("doc/") else None
    history = [(m["role"], m["text"]) for m in (chat or [])][-6:]

    engine = get_engine()
    try:
        answer = engine.copilot.ask(question, current_doc=scope, history=history)
        msg = {
            "role": "assistant",
            "text": answer.text,
            "citations": [{"label": c.label, "url": c.url} for c in answer.citations],
            "suggestions": answer.suggestions,
        }
    except Exception as e:  # surface failures in the chat, never silently
        msg = {
            "role": "assistant",
            "text": f"⚠️ Something went wrong answering that ({type(e).__name__}). "
                    "Try again, or use search meanwhile.",
            "citations": [],
            "suggestions": [],
        }
    chat = (chat or []) + [{"role": "user", "text": question}, msg]
    return chat[-30:], "", ""


@app.callback(
    Output("copilot-messages", "children"),
    Output("copilot-suggestions", "children"),
    Input("atlas-chat", "data"),
)
def render_chat(chat):
    # The intro bubble is always shown (not stored) — it anchors the thread
    # and keeps the mode explanation visible.
    intro = get_engine().copilot.ask("help")
    chat = [
        {
            "role": "assistant",
            "text": intro.text,
            "citations": [],
            "suggestions": intro.suggestions if not chat else [],
        }
    ] + (chat or [])
    bubbles = []
    for msg in chat:
        if msg["role"] == "user":
            bubbles.append(html.Div(msg["text"], className="chat-bubble chat-user"))
        else:
            children = [ui.render_markdown(msg["text"], className="atlas-md chat-md")]
            cites = msg.get("citations") or []
            if cites:
                children.append(
                    html.Div(
                        [html.A(f"📎 {c['label']}", href=ui.href(c["url"]),
                                className="cite-chip") for c in cites],
                        className="cite-row",
                    )
                )
            bubbles.append(html.Div(children, className="chat-bubble chat-assistant"))
    last = chat[-1] if chat else {}
    chips = [
        dbc.Button(s, id={"type": "copilot-sugg", "q": s}, size="sm",
                   color="secondary", outline=True, className="me-1 mb-1 sugg-chip")
        for s in (last.get("suggestions") or [])
    ]
    return bubbles, chips


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Run the Atlas knowledge hub")
    parser.add_argument("--port", type=int,
                        default=int(os.environ.get("ATLAS_PORT", "8050")),
                        help="port to serve on (default 8050, or $ATLAS_PORT)")
    parser.add_argument("--host", default=os.environ.get("ATLAS_HOST", "127.0.0.1"))
    parser.add_argument("--no-debug", action="store_true",
                        help="disable Dash debug/hot-reload")
    args = parser.parse_args()
    debug = not args.no_debug and os.environ.get("ATLAS_DEBUG", "1") == "1"
    app.run(debug=debug, host=args.host, port=args.port)
