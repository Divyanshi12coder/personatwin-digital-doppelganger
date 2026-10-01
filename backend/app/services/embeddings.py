"""Embedding providers.

Both providers return L2-normalised vectors of exactly ``EMBEDDING_DIM`` floats so
they fit the pgvector column created by the migration.

* ``LocalHashingEmbedder`` (default) — a deterministic, dependency-free embedder:
  stemmed unigrams + bigrams + character n-grams + a small concept lexicon, feature-
  hashed into 384 signed buckets. It is lexical rather than deeply semantic, but it is
  real, fast, offline, and gives sensible nearest-neighbour behaviour for RAG demos.
* ``OpenAIEmbedder`` — calls the OpenAI embeddings API with ``dimensions=384``.

If you switch providers, re-index existing memories (Settings -> Memory -> Re-index)
because vectors from different models are not comparable.
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
from collections import Counter
from functools import lru_cache
from typing import Protocol

import httpx

from app.core.config import EMBEDDING_DIM, get_settings

logger = logging.getLogger(__name__)


class EmbeddingError(RuntimeError):
    pass


class Embedder(Protocol):
    name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


STOPWORDS = frozenset(
    """a about above after again against all am an and any are as at be because been before being below
    between both but by can could did do does doing down during each few for from further had has have having
    he her here hers herself him himself his how i if in into is it its itself just me more most my myself no
    nor not now of off on once only or other our ours ourselves out over own same she should so some such than
    that the their theirs them themselves then there these they this those through to too under until up very
    was we were what when where which while who whom why will with would you your yours yourself yourselves
    im ive id dont doesnt didnt cant wont isnt also get got really much many thing things way something""".split()
)

# Concept lexicon: lightweight semantic expansion so that, e.g., "switch careers"
# and "changed jobs" share features even without overlapping words.
CONCEPTS: dict[str, tuple[str, ...]] = {
    "career": ("career", "job", "role", "profession", "work", "employer", "position", "promotion", "hire", "hiring", "resign", "quit", "industry", "occupation"),
    "change": ("switch", "change", "transition", "pivot", "move", "leave", "shift", "start", "new"),
    "learning": ("learn", "study", "course", "skill", "practice", "read", "book", "lesson", "understand", "education", "class", "school", "student"),
    "decision": ("decide", "decision", "choose", "choice", "option", "tradeoff", "dilemma", "weigh", "uncertain", "risk"),
    "fear": ("afraid", "fear", "anxious", "anxiety", "worried", "nervous", "scared", "doubt", "stress", "overwhelmed", "struggle", "struggling"),
    "failure": ("fail", "failure", "mistake", "error", "setback", "lost", "lose", "wrong", "rejected", "rejection"),
    "success": ("success", "win", "won", "achieve", "accomplish", "launch", "shipped", "promoted", "proud"),
    "productivity": ("productivity", "focus", "time", "procrastinate", "procrastination", "habit", "routine", "schedule", "deadline", "priority", "prioritize", "busy"),
    "goal": ("goal", "plan", "objective", "target", "milestone", "ambition", "vision", "aim"),
    "leadership": ("lead", "leader", "leadership", "manage", "manager", "team", "delegate", "mentor", "coach", "feedback"),
    "money": ("money", "salary", "pay", "finance", "financial", "savings", "income", "cost", "budget"),
    "relationships": ("colleague", "boss", "peer", "friend", "network", "networking", "conflict", "communication", "communicate"),
    "creativity": ("creative", "design", "write", "writing", "idea", "art", "build", "craft", "portfolio"),
    "growth": ("grow", "growth", "improve", "develop", "development", "progress", "confidence", "mindset", "resilience"),
    "problem": ("problem", "issue", "bug", "debug", "solve", "solution", "stuck", "blocker", "challenge"),
}
_WORD_TO_CONCEPT = {w: c for c, words in CONCEPTS.items() for w in words}

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
_SUFFIXES = ("ization", "ations", "ation", "ments", "ment", "ness", "ings", "ing", "ies", "ied", "ers", "er", "ed", "es", "ly", "s")


def stem(word: str) -> str:
    for suf in _SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            base = word[: -len(suf)]
            return base + "y" if suf in ("ies", "ied") else base
    return word


def tokenize(text: str) -> list[str]:
    words = [w.replace("'", "") for w in _TOKEN_RE.findall(text.lower())]
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def _bucket(feature: str) -> tuple[int, float]:
    digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
    value = int.from_bytes(digest, "big")
    return value % EMBEDDING_DIM, (1.0 if (value >> 63) & 1 else -1.0)


def l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


class LocalHashingEmbedder:
    name = "local-hashing-v1"

    def _features(self, text: str) -> Counter[str]:
        words = tokenize(text)
        stems = [stem(w) for w in words]
        feats: Counter[str] = Counter()
        for w, s in zip(words, stems):
            feats[f"u:{s}"] += 1.0
            concept = _WORD_TO_CONCEPT.get(w) or _WORD_TO_CONCEPT.get(s)
            if concept:
                feats[f"c:{concept}"] += 0.8
            padded = f"<{s}>"
            for i in range(len(padded) - 3):
                feats[f"g:{padded[i:i + 4]}"] += 0.25
        for a, b in zip(stems, stems[1:]):
            feats[f"b:{a}_{b}"] += 0.6
        return feats

    def embed_one(self, text: str) -> list[float]:
        vec = [0.0] * EMBEDDING_DIM
        for feature, count in self._features(text).items():
            idx, sign = _bucket(feature)
            vec[idx] += sign * (1.0 + math.log(count)) if count >= 1 else sign * count
        return l2_normalize(vec)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_one(t) for t in texts]


class OpenAIEmbedder:
    def __init__(self, api_key: str, model: str, base_url: str = "") -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.name = f"openai:{model}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        out: list[list[float]] = []
        try:
            with httpx.Client(timeout=30.0) as client:
                for start in range(0, len(texts), 64):
                    batch = [t[:8000] or " " for t in texts[start : start + 64]]
                    resp = client.post(
                        f"{self.base_url}/embeddings",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json={"model": self.model, "input": batch, "dimensions": EMBEDDING_DIM},
                    )
                    resp.raise_for_status()
                    data = sorted(resp.json()["data"], key=lambda d: d["index"])
                    out.extend(l2_normalize([float(x) for x in d["embedding"]]) for d in data)
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            logger.warning("Embedding request failed: %s", exc)
            raise EmbeddingError("The embedding provider is unavailable") from exc
        for v in out:
            if len(v) != EMBEDDING_DIM:
                raise EmbeddingError(f"Embedding provider returned {len(v)} dims, expected {EMBEDDING_DIM}")
        return out


@lru_cache
def get_embedder() -> Embedder:
    settings = get_settings()
    if settings.EMBEDDING_PROVIDER == "openai":
        key = settings.EMBEDDING_API_KEY or (settings.AI_API_KEY if settings.AI_PROVIDER == "openai" else "")
        if key:
            return OpenAIEmbedder(key, settings.EMBEDDING_MODEL, settings.EMBEDDING_BASE_URL)
        logger.warning("EMBEDDING_PROVIDER=openai but no key configured; using local embeddings")
    return LocalHashingEmbedder()


def embed_texts(texts: list[str]) -> list[list[float]]:
    return get_embedder().embed(texts)


def embed_query(text: str) -> list[float]:
    return get_embedder().embed([text])[0]


def cosine(a: list[float], b: list[float]) -> float:
    # Vectors are L2-normalised, so the dot product is the cosine similarity.
    return sum(x * y for x, y in zip(a, b))
