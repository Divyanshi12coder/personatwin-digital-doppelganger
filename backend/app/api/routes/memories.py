"""Memory Inspector — one transparent view over every memory store.

* GET /memories            list everything (or semantic search with ?q=)
* /memories/conversation   manage opt-in conversation memories
* POST /memories/reindex   re-embed everything (after switching embedding provider)
* GET /memories/tags       the user's tags with usage counts
"""

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import DB, CurrentUser
from app.models import (
    ConversationMemory,
    ExperienceMemory,
    KnowledgeChunk,
    KnowledgeDocument,
    Tag,
    User,
    conversation_memory_tags,
    experience_tags,
    knowledge_document_tags,
)
from app.schemas.memory import ConversationMemoryOut, ConversationMemoryUpdate, MemoryItem, MemoryListOut
from app.services.embeddings import EmbeddingError
from app.services.indexing import index_conversation_memory, reindex_user
from app.services.persona import OPTIONS
from app.services.profile import get_or_create_personality
from app.services.retrieval import retrieve
from app.services.tags import resolve_tags

router = APIRouter(prefix="/memories", tags=["memories"])

TypeFilter = Literal["knowledge", "experience", "conversation", "preference"]


def _snippet(text: str, n: int = 220) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"


def _preference_items(db: Session, user: User) -> list[MemoryItem]:
    p = get_or_create_personality(db, user)
    items: list[tuple[str, str, str]] = []
    for key in ("communication_style", "tone", "teaching_approach", "decision_style", "encouragement_style", "response_length"):
        value = getattr(p, key)
        items.append((key, key.replace("_", " ").capitalize(), f"{value.replace('_', ' ')} — {OPTIONS[key].get(value, '')}"))
    if p.values:
        items.append(("values", "Core values", ", ".join(p.values)))
    for key, label in (
        ("philosophy_encouragement", "How I encourage people"),
        ("philosophy_mistakes", "How I handle mistakes"),
        ("philosophy_decisions", "How I approach difficult decisions"),
        ("philosophy_teaching", "How I teach"),
        ("boundaries", "Boundaries"),
    ):
        if getattr(p, key).strip():
            items.append((key, label, getattr(p, key)))
    return [
        MemoryItem(
            id=f"preference:{key}",
            ref_id=None,
            type="preference",
            title=label,
            category="persona",
            snippet=_snippet(text),
            tags=[],
            source="Personality profile",
            date=p.updated_at,
        )
        for key, label, text in items
    ]


def _counts(db: Session, user: User, preferences: int) -> dict[str, int]:
    def count(model: type) -> int:
        return int(db.scalar(select(func.count()).select_from(model).where(model.user_id == user.id)) or 0)  # type: ignore[attr-defined]

    return {
        "knowledge": count(KnowledgeDocument),
        "experience": count(ExperienceMemory),
        "conversation": count(ConversationMemory),
        "preference": preferences,
    }


@router.get("", response_model=MemoryListOut)
def list_memories(
    user: CurrentUser,
    db: DB,
    q: Annotated[str | None, Query(max_length=300)] = None,
    type: TypeFilter | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> MemoryListOut:
    preferences = _preference_items(db, user)
    counts = _counts(db, user, len(preferences))
    items: list[MemoryItem] = []
    query = q.strip() if q else ""

    if query:
        store_types = {type} if type and type != "preference" else {"knowledge", "experience", "conversation"}
        if type != "preference":
            try:
                result = retrieve(db, user.id, query, top_k=min(limit, 20), min_relevance=0.0, types=store_types)
            except EmbeddingError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Semantic search is temporarily unavailable (embedding provider unreachable).",
                ) from exc
            for m in result.all:
                prefix = {"knowledge": "knowledge", "experience": "experience", "conversation": "conversation"}[m.source_type]
                items.append(
                    MemoryItem(
                        id=f"{prefix}:{m.source_id}",
                        ref_id=m.source_id,
                        type=prefix,  # type: ignore[arg-type]
                        title=m.title,
                        category=m.category,
                        snippet=m.snippet,
                        tags=m.tags,
                        source=str(m.details.get("source") or ("Episodic memory" if prefix == "experience" else "Conversation")),
                        date=m.created_at,
                        relevance=round(m.score, 4),
                    )
                )
        if type in (None, "preference"):
            needle = query.lower()
            items.extend(p for p in preferences if needle in p.title.lower() or needle in p.snippet.lower())
        items.sort(key=lambda i: i.relevance if i.relevance is not None else 0.5, reverse=True)
        db.commit()
        return MemoryListOut(items=items[:limit], counts=counts, query=query)

    if type in (None, "knowledge"):
        docs = db.scalars(select(KnowledgeDocument).where(KnowledgeDocument.user_id == user.id)).all()
        unindexed = {
            int(d)
            for (d,) in db.execute(
                select(KnowledgeChunk.document_id)
                .where(KnowledgeChunk.user_id == user.id, KnowledgeChunk.embedding.is_(None))
                .distinct()
            )
        }
        items.extend(
            MemoryItem(
                id=f"knowledge:{d.id}",
                ref_id=d.id,
                type="knowledge",
                title=d.title,
                category=d.category,
                snippet=_snippet(d.content),
                tags=[t.name for t in d.tags],
                source=d.source or d.source_type,
                date=d.created_at,
                indexed=d.id not in unindexed,
            )
            for d in docs
        )
    if type in (None, "experience"):
        exps = db.scalars(select(ExperienceMemory).where(ExperienceMemory.user_id == user.id)).all()
        items.extend(
            MemoryItem(
                id=f"experience:{e.id}",
                ref_id=e.id,
                type="experience",
                title=e.title,
                category=e.experience_type,
                snippet=_snippet(e.lesson_learned or e.what_happened or e.situation),
                tags=[t.name for t in e.tags],
                source=e.context or "Episodic memory",
                date=e.created_at,
                indexed=e.embedding is not None,
            )
            for e in exps
        )
    if type in (None, "conversation"):
        mems = db.scalars(select(ConversationMemory).where(ConversationMemory.user_id == user.id)).all()
        items.extend(
            MemoryItem(
                id=f"conversation:{m.id}",
                ref_id=m.id,
                type="conversation",
                title=m.title,
                category=m.topic,
                snippet=_snippet(m.content),
                tags=[t.name for t in m.tags],
                source="Saved from a mentor conversation",
                date=m.created_at,
                indexed=m.embedding is not None,
            )
            for m in mems
        )
    items.sort(key=lambda i: i.date.timestamp() if i.date else 0, reverse=True)
    if type in (None, "preference"):
        items.extend(preferences)
    db.commit()
    return MemoryListOut(items=items[:limit], counts=counts)


@router.get("/tags")
def list_tags(user: CurrentUser, db: DB) -> list[dict[str, object]]:
    usage: dict[str, int] = {}
    for table, col in (
        (knowledge_document_tags, knowledge_document_tags.c.tag_id),
        (experience_tags, experience_tags.c.tag_id),
        (conversation_memory_tags, conversation_memory_tags.c.tag_id),
    ):
        for name, n in db.execute(
            select(Tag.name, func.count()).join(table, col == Tag.id).where(Tag.user_id == user.id).group_by(Tag.name)
        ):
            usage[name] = usage.get(name, 0) + int(n)
    return [{"name": k, "count": v} for k, v in sorted(usage.items(), key=lambda kv: (-kv[1], kv[0]))]


@router.post("/reindex")
def reindex(user: CurrentUser, db: DB) -> dict[str, int]:
    return reindex_user(db, user.id)


# ---------------------------------------------------------------- conversation memories


def _conv_out(m: ConversationMemory) -> ConversationMemoryOut:
    return ConversationMemoryOut(
        id=m.id,
        title=m.title,
        content=m.content,
        topic=m.topic,
        conversation_id=m.conversation_id,
        indexed=m.embedding is not None,
        tags=[t.name for t in m.tags],
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _owned_memory(db: Session, user: User, mem_id: int) -> ConversationMemory:
    mem = db.scalar(select(ConversationMemory).where(ConversationMemory.id == mem_id, ConversationMemory.user_id == user.id))
    if mem is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    return mem


@router.get("/conversation", response_model=list[ConversationMemoryOut])
def list_conversation_memories(user: CurrentUser, db: DB) -> list[ConversationMemoryOut]:
    rows = db.scalars(
        select(ConversationMemory).where(ConversationMemory.user_id == user.id).order_by(ConversationMemory.created_at.desc())
    ).all()
    return [_conv_out(m) for m in rows]


@router.get("/conversation/{mem_id}", response_model=ConversationMemoryOut)
def get_conversation_memory(mem_id: int, user: CurrentUser, db: DB) -> ConversationMemoryOut:
    return _conv_out(_owned_memory(db, user, mem_id))


@router.patch("/conversation/{mem_id}", response_model=ConversationMemoryOut)
def update_conversation_memory(
    mem_id: int, body: ConversationMemoryUpdate, user: CurrentUser, db: DB
) -> ConversationMemoryOut:
    mem = _owned_memory(db, user, mem_id)
    if body.title is not None:
        mem.title = body.title.strip()
    if body.content is not None:
        mem.content = body.content.strip()
    if body.tags is not None:
        mem.tags = resolve_tags(db, user.id, body.tags)
    index_conversation_memory(mem)
    db.commit()
    db.refresh(mem)
    return _conv_out(mem)


@router.delete("/conversation/{mem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation_memory(mem_id: int, user: CurrentUser, db: DB) -> Response:
    db.delete(_owned_memory(db, user, mem_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
