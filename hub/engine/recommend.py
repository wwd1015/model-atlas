"""Related-content recommendations — the "second brain" connective tissue.

Hand-rolled TF-IDF cosine similarity (docs are small; no sklearn needed)
blended with the explicit wiki-link graph: a direct link or backlink is a
strong signal that two concepts belong together, so it gets a flat boost
on top of the lexical similarity.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from hub.engine.loader import Corpus

_TOKEN_RE = re.compile(r"[a-z0-9_]+")
_STOP = frozenset(
    """a an and are as at be by for from has have if in into is it its of on or
    that the this to was we were will with you your not no can each which when
    what how their they than then there these those our out over under between
    do does done use used using should must may all any per via more other""".split()
)

_LINK_BOOST = 0.2
_TAG_BOOST = 0.05  # per shared tag, capped at 0.15


def _tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOP and len(t) > 2]


class Recommender:
    def __init__(self, corpus: Corpus):
        self.corpus = corpus
        docs = corpus.docs
        n = max(len(docs), 1)
        tf: dict[str, Counter] = {}
        df: Counter = Counter()
        for doc_id, doc in docs.items():
            # Title and tags weigh more than body prose.
            toks = _tokenize(doc.body) + _tokenize(doc.title) * 3 + _tokenize(" ".join(doc.tags)) * 3
            counts = Counter(toks)
            tf[doc_id] = counts
            df.update(counts.keys())
        self._vecs: dict[str, dict[str, float]] = {}
        for doc_id, counts in tf.items():
            vec = {
                term: (1 + math.log(c)) * math.log(n / (1 + df[term]))
                for term, c in counts.items()
            }
            norm = math.sqrt(sum(w * w for w in vec.values())) or 1.0
            self._vecs[doc_id] = {t: w / norm for t, w in vec.items()}

    def _cosine(self, a: str, b: str) -> float:
        va, vb = self._vecs.get(a, {}), self._vecs.get(b, {})
        if len(vb) < len(va):
            va, vb = vb, va
        return sum(w * vb.get(t, 0.0) for t, w in va.items())

    def related(self, doc_id: str, k: int = 5) -> list[tuple[str, float]]:
        """Top-k related doc ids with scores, excluding the doc itself."""
        doc = self.corpus.docs.get(doc_id)
        if doc is None:
            return []
        neighbors = doc.links_out | doc.backlinks
        scored = []
        for other_id, other in self.corpus.docs.items():
            if other_id == doc_id:
                continue
            score = self._cosine(doc_id, other_id)
            if other_id in neighbors:
                score += _LINK_BOOST
            score += min(len(set(doc.tags) & set(other.tags)) * _TAG_BOOST, 0.15)
            if score > 0.02:
                scored.append((other_id, score))
        scored.sort(key=lambda x: -x[1])
        return scored[:k]

    def recommend(self, history: list[str], k: int = 6) -> list[tuple[str, float]]:
        """Recommendations from recently-viewed docs (most recent weighs most)."""
        seen = set(history)
        agg: dict[str, float] = {}
        for i, doc_id in enumerate(reversed(history[-5:])):
            decay = 1.0 / (1 + i)
            for other_id, score in self.related(doc_id, k=10):
                if other_id not in seen:
                    agg[other_id] = agg.get(other_id, 0.0) + score * decay
        ranked = sorted(agg.items(), key=lambda x: -x[1])
        return ranked[:k]
