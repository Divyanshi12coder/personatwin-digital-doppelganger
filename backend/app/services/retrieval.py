"""Long-term memory retrieval (the "R" in RAG).

Three stores are searched, always filtered by ``user_id`` first:

* knowledge chunks      -> long-term semantic memory
* experience memories   -> episodic memory
* conversation memories -> opt-in notes from past mentor conversations

On PostgreSQL the similarity search runs inside the database using pgvector's
cosine-distance operator (``<=>``) backed by an HNSW index. On SQLite (tests /
quick local runs) the same ranking is computed in Python. Results are re-scored
with a small lexical-overlap bonus (hybrid retrieval), filtered by the user's
minimum-relevance threshold, and finally by a *relative* cutoff: anything scoring
below a fraction of the best match is dropped, which keeps loosely-related
memories out of the prompt when a strong match exists.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, Select, bindparam, select
from sqlalchemy.orm import Session

from app.core.config import EMBEDDING_DIM
from app.models import ConversationMemory, ExperienceMemory, KnowledgeChunk, KnowledgeDocument
from app.services.embeddings import cosine, embed_query, stem, tokenize

SOURCE_KNOWLEDGE = "knowledge"
SOURCE_EXPERIENCE = "experience"
SOURCE_CONVERSATION = "conversation"


@dataclass
class RetrievedMemory:
    source_type: str
    source_id: int
    title: str
    content: str
    score: float
    category: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    chunk_id: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def snippet(self) -> str:
        text = " ".join(self.content.split())
        return text if len(text) <= 280 else text[:277].rsplit(" ", 1)[0] + "…"


@dataclass
class RetrievalResult:
    knowledge: list[RetrievedMemory]
    experiences: list[RetrievedMemory]
    conversations: list[RetrievedMemory]
    timings_ms: dict[str, int]

    @property
    def all(self) -> list[RetrievedMemory]:
        return self.knowledge + self.experiences + self.conversations

    @property
    def is_empty(self) -> bool:
        return not (self.knowledge or self.experiences or self.conversations)


def _is_postgres(db: Session) -> bool:
    return db.get_bind().dialect.name == "postgresql"


def _lexical_bonus(query_stems: set[str], text: str) -> float:
    if not query_stems:
        return 0.0
    text_stems = {stem(w) for w in tokenize(text)}
    overlap = len(query_stems & text_stems) / len(query_stems)
    return 0.12 * overlap


def _ranked(
    db: Session,
    stmt: Select[Any],
    embedding_col: Any,
    qvec: list[float],
    limit: int,
) -> list[tuple[Any, float]]:
    """Return ``(row, cosine_similarity)`` pairs, best first."""
    if _is_postgres(db):
        qparam = bindparam("qvec", value=qvec, type_=Vector(EMBEDDING_DIM))
        distance = embedding_col.op("<=>", return_type=Float)(qparam).label("distance")
        rows = db.execute(stmt.add_columns(distance).where(embedding_col.is_not(None)).order_by("distance").limit(limit))
        return [(row[0], 1.0 - float(row[-1])) for row in rows]
    candidates = db.scalars(stmt.where(embedding_col.is_not(None))).all()
    attr = embedding_col.key
    scored = [(c, cosine(qvec, getattr(c, attr))) for c in candidates if getattr(c, attr)]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:limit]


def search_knowledge(
    db: Session,
    user_id: int,
    qvec: list[float],
    query_stems: set[str],
    limit: int,
    category: str | None = None,
) -> list[RetrievedMemory]:
    stmt = (
        select(KnowledgeChunk)
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
        .where(KnowledgeChunk.user_id == user_id, KnowledgeDocument.user_id == user_id)
    )
    if category:
        stmt = stmt.where(KnowledgeDocument.category == category)
    best_per_doc: dict[int, RetrievedMemory] = {}
    for chunk, sim in _ranked(db, stmt, KnowledgeChunk.embedding, qvec, limit * 4):
        doc = chunk.document
        score = sim + _lexical_bonus(query_stems, f"{doc.title} {chunk.content}")
        current = best_per_doc.get(doc.id)
        if current is None or score > current.score:
            best_per_doc[doc.id] = RetrievedMemory(
                source_type=SOURCE_KNOWLEDGE,
                source_id=doc.id,
                chunk_id=chunk.id,
                title=doc.title,
                content=chunk.content,
                score=score,
                category=doc.category,
                tags=[t.name for t in doc.tags],
                created_at=doc.created_at,
                details={"source": doc.source, "source_type": doc.source_type},
            )
    return sorted(best_per_doc.values(), key=lambda m: m.score, reverse=True)[:limit]


def search_experiences(
    db: Session, user_id: int, qvec: list[float], query_stems: set[str], limit: int
) -> list[RetrievedMemory]:
    stmt = select(ExperienceMemory).where(ExperienceMemory.user_id == user_id)
    out: list[RetrievedMemory] = []
    for exp, sim in _ranked(db, stmt, ExperienceMemory.embedding, qvec, limit * 3):
        text = exp.embedding_text()
        # Importance (1-5) nudges ranking slightly; relevance still dominates.
        score = sim + _lexical_bonus(query_stems, text) + 0.015 * (exp.importance - 3)
        out.append(
            RetrievedMemory(
                source_type=SOURCE_EXPERIENCE,
                source_id=exp.id,
                title=exp.title,
                content=text,
                score=score,
                category=exp.experience_type,
                tags=[t.name for t in exp.tags],
                created_at=exp.created_at,
                details={
                    "situation": exp.situation,
                    "what_happened": exp.what_happened,
                    "lesson_learned": exp.lesson_learned,
                    "do_differently": exp.do_differently,
                    "context": exp.context,
                    "occurred_on": exp.occurred_on.isoformat() if exp.occurred_on else None,
                    "importance": exp.importance,
                },
            )
        )
    out.sort(key=lambda m: m.score, reverse=True)
    return out[:limit]


def search_conversation_memories(
    db: Session, user_id: int, qvec: list[float], query_stems: set[str], limit: int
) -> list[RetrievedMemory]:
    stmt = select(ConversationMemory).where(ConversationMemory.user_id == user_id)
    out: list[RetrievedMemory] = []
    for mem, sim in _ranked(db, stmt, ConversationMemory.embedding, qvec, limit * 3):
        # Past conversations are partly AI-generated, so they rank below first-hand memories.
        score = 0.9 * (sim + _lexical_bonus(query_stems, mem.content))
        out.append(
            RetrievedMemory(
                source_type=SOURCE_CONVERSATION,
                source_id=mem.id,
                title=mem.title,
                content=mem.content,
                score=score,
                category=mem.topic,
                tags=[t.name for t in mem.tags],
                created_at=mem.created_at,
            )
        )
    out.sort(key=lambda m: m.score, reverse=True)
    return out[:limit]


def retrieve(
    db: Session,
    user_id: int,
    query: str,
    top_k: int = 6,
    min_relevance: float = 0.12,
    include_conversations: bool = True,
    types: set[str] | None = None,
    category: str | None = None,
    relative_cutoff: float = 0.0,
) -> RetrievalResult:
    types = types or {SOURCE_KNOWLEDGE, SOURCE_EXPERIENCE, SOURCE_CONVERSATION}
    timings: dict[str, int] = {}

    t0 = time.perf_counter()
    qvec = embed_query(query)
    query_stems = {stem(w) for w in tokenize(query)}
    timings["embed"] = int((time.perf_counter() - t0) * 1000)

    def run(name: str, fn: Any, *args: Any) -> list[RetrievedMemory]:
        start = time.perf_counter()
        found = [m for m in fn(*args) if m.score >= min_relevance]
        timings[name] = int((time.perf_counter() - start) * 1000)
        return found

    knowledge = (
        run("knowledge", search_knowledge, db, user_id, qvec, query_stems, top_k, category)
        if SOURCE_KNOWLEDGE in types
        else []
    )
    experiences = (
        run("experiences", search_experiences, db, user_id, qvec, query_stems, max(2, (top_k + 1) // 2))
        if SOURCE_EXPERIENCE in types
        else []
    )
    conversations = (
        run("conversations", search_conversation_memories, db, user_id, qvec, query_stems, 2)
        if include_conversations and SOURCE_CONVERSATION in types
        else []
    )
    if relative_cutoff > 0:
        best = max((m.score for m in knowledge + experiences + conversations), default=0.0)
        floor = best * relative_cutoff
        knowledge = [m for m in knowledge if m.score >= floor]
        experiences = [m for m in experiences if m.score >= floor]
        conversations = [m for m in conversations if m.score >= floor]
    return RetrievalResult(knowledge, experiences, conversations, timings)
