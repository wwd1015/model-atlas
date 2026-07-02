"""Full-text search over the Atlas corpus.

Primary backend: SQLite FTS5 (stdlib — nothing to install), one row per
document section, BM25-ranked with title/heading boosts. If the local
SQLite build lacks FTS5 (rare), a small pure-Python token-overlap scorer
keeps the hub functional.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from hub.engine.loader import Corpus

_MARK_L, _MARK_R = "\x02", "\x03"
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")

# Question furniture — dropped from queries when content words remain, so
# "How do we handle NPI data?" searches as "handle NPI data".
_QUERY_STOP = frozenset(
    """a an and are be by can could did do does for from had has have how i in
    is it me my of on or our should that the there they this to was we what
    when where which who whom why will with would you your""".split()
)


@dataclass
class Hit:
    doc_id: str
    title: str
    channel: str
    dtype: str
    anchor: str
    heading: str
    snippet: str      # markdown, query terms wrapped in **bold**
    score: float

    @property
    def url(self) -> str:
        return f"/doc/{self.doc_id}#{self.anchor}" if self.anchor else f"/doc/{self.doc_id}"


def _tokens(query: str) -> list[str]:
    toks = _TOKEN_RE.findall(query.lower())
    content = [t for t in toks if t not in _QUERY_STOP]
    return content or toks


class SearchEngine:
    def __init__(self, corpus: Corpus):
        self.corpus = corpus
        self._rows = self._collect_rows(corpus)
        self._conn: sqlite3.Connection | None = None
        try:
            self._conn = self._build_fts(self._rows)
        except sqlite3.OperationalError:
            self._conn = None  # FTS5 unavailable → pure-Python fallback

    @staticmethod
    def _collect_rows(corpus: Corpus) -> list[dict]:
        rows = []
        for doc in corpus.docs.values():
            for sec in doc.sections:
                body = sec.text.strip()
                if not body and not sec.heading:
                    continue
                rows.append(
                    {
                        "doc_id": doc.id,
                        "title": doc.title,
                        "channel": doc.channel,
                        "dtype": doc.dtype,
                        "anchor": sec.anchor,
                        "heading": sec.heading,
                        "body": body,
                        "tags": " ".join(doc.tags),
                    }
                )
        return rows

    @staticmethod
    def _build_fts(rows: list[dict]) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.execute(
            """CREATE VIRTUAL TABLE sections USING fts5(
                   title, heading, body, tags,
                   doc_id UNINDEXED, channel UNINDEXED, dtype UNINDEXED, anchor UNINDEXED,
                   tokenize='porter unicode61'
               )"""
        )
        conn.executemany(
            "INSERT INTO sections (title, heading, body, tags, doc_id, channel, dtype, anchor) "
            "VALUES (:title, :heading, :body, :tags, :doc_id, :channel, :dtype, :anchor)",
            rows,
        )
        conn.commit()
        return conn

    # -- public API ---------------------------------------------------------

    def search(
        self,
        query: str,
        channels: list[str] | None = None,
        limit: int = 20,
    ) -> list[Hit]:
        toks = _tokens(query)
        if not toks:
            return []
        if self._conn is not None:
            hits = self._fts_search(toks, mode="AND", channels=channels, limit=limit)
            if not hits and len(toks) > 1:
                hits = self._fts_search(toks, mode="OR", channels=channels, limit=limit)
            return hits
        return self._fallback_search(toks, channels=channels, limit=limit)

    # -- FTS5 path ----------------------------------------------------------

    def _fts_search(self, toks: list[str], mode: str, channels, limit: int) -> list[Hit]:
        joiner = " " if mode == "AND" else " OR "
        match = joiner.join(f'"{t}"' for t in toks)
        where, params = "sections MATCH ?", [match]
        if channels:
            where += f" AND channel IN ({','.join('?' * len(channels))})"
            params += list(channels)
        sql = f"""
            SELECT doc_id, title, channel, dtype, anchor, heading,
                   snippet(sections, 2, ?, ?, ' … ', 18) AS snip,
                   bm25(sections, 4.0, 3.0, 1.0, 2.0) AS rank
            FROM sections WHERE {where}
            ORDER BY rank LIMIT ?
        """
        try:
            rows = self._conn.execute(sql, [_MARK_L, _MARK_R, *params, limit]).fetchall()
        except sqlite3.OperationalError:
            return []
        hits = []
        for doc_id, title, channel, dtype, anchor, heading, snip, rank in rows:
            snip = self._markdown_safe(snip).replace(_MARK_L, "**").replace(_MARK_R, "**")
            hits.append(Hit(doc_id, title, channel, dtype, anchor, heading, snip, -float(rank)))
        return hits

    # -- fallback path ------------------------------------------------------

    def _fallback_search(self, toks: list[str], channels, limit: int) -> list[Hit]:
        scored = []
        for row in self._rows:
            if channels and row["channel"] not in channels:
                continue
            hay = f"{row['title']} {row['heading']} {row['tags']} {row['body']}".lower()
            score = sum(3.0 if t in row["title"].lower() else 1.0 for t in toks if t in hay)
            if score > 0:
                scored.append((score, row))
        scored.sort(key=lambda x: -x[0])
        hits = []
        for score, row in scored[:limit]:
            snippet = self._make_snippet(row["body"], toks)
            hits.append(
                Hit(row["doc_id"], row["title"], row["channel"], row["dtype"],
                    row["anchor"], row["heading"], snippet, score)
            )
        return hits

    @staticmethod
    def _make_snippet(body: str, toks: list[str], width: int = 180) -> str:
        low = body.lower()
        pos = min((low.find(t) for t in toks if low.find(t) >= 0), default=0)
        start = max(0, pos - width // 3)
        chunk = body[start: start + width].strip()
        for t in sorted(set(toks), key=len, reverse=True):
            chunk = re.sub(f"({re.escape(t)})", r"**\1**", chunk, flags=re.IGNORECASE)
        return ("… " if start else "") + chunk + " …"

    @staticmethod
    def _markdown_safe(text: str) -> str:
        """Flatten snippet text so it renders inline (no headings/blocks inside a result row)."""
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
        text = text.replace("*", "").replace("`", "")  # emphasis comes only from the query marks
        return re.sub(r"\s+", " ", text).strip()
