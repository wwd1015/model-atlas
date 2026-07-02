"""Lazy singletons for the engine — built once per process, refreshable.

The corpus is small (markdown files), so a full rebuild is fast; the hub
rebuilds on process start and exposes `refresh()` for content updates.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

from hub.engine.copilot import Copilot, load_adapter
from hub.engine.loader import Corpus, load_corpus
from hub.engine.recommend import Recommender
from hub.engine.search import SearchEngine


@dataclass
class Engine:
    corpus: Corpus
    search: SearchEngine
    recommender: Recommender
    copilot: Copilot


_lock = threading.Lock()
_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                _engine = _build()
    return _engine


def refresh() -> Engine:
    global _engine
    with _lock:
        _engine = _build()
    return _engine


def _build() -> Engine:
    corpus = load_corpus()
    search = SearchEngine(corpus)
    recommender = Recommender(corpus)
    copilot = Copilot(corpus, search, recommender, adapter=load_adapter())
    return Engine(corpus=corpus, search=search, recommender=recommender, copilot=copilot)
