"""Write-path of the memory system: chunk + embed + store.

Embedding failures (e.g. an unreachable remote provider) never lose user data:
the memory is saved without a vector, shows up as "not indexed" in Memory
health, and can be re-indexed later.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import ConversationMemory, ExperienceMemory, KnowledgeChunk, KnowledgeDocument
from app.services.chunking import chunk_text
from app.services.embeddings import EmbeddingError, embed_texts

logger = logging.getLogger(__name__)


def _safe_embed(texts: list[str]) -> list[list[float] | None]:
    try:
        return list(embed_texts(texts))
    except EmbeddingError as exc:
        logger.warning("Embedding failed, storing memory without vectors: %s", exc)
        return [None] * len(texts)


def index_document(db: Session, doc: KnowledgeDocument) -> None:
    settings = get_settings()
    if doc.chunks:
        doc.chunks.clear()  # delete-orphan cascade removes the old chunks
        db.flush()
    pieces = chunk_text(doc.content, settings.CHUNK_SIZE_CHARS, settings.CHUNK_OVERLAP_CHARS)
    # The title and category are prepended so short chunks still carry their topic.
    header = f"{doc.title} ({doc.category})"
    vectors = _safe_embed([f"{header}\n{p}" for p in pieces])
    doc.chunks = [
        KnowledgeChunk(user_id=doc.user_id, chunk_index=i, content=p, embedding=v)
        for i, (p, v) in enumerate(zip(pieces, vectors))
    ]
    doc.char_count = len(doc.content)


def index_experience(exp: ExperienceMemory) -> None:
    exp.embedding = _safe_embed([exp.embedding_text()])[0]


def index_conversation_memory(mem: ConversationMemory) -> None:
    mem.embedding = _safe_embed([f"{mem.title}\n{mem.content}"])[0]


def reindex_user(db: Session, user_id: int) -> dict[str, int]:
    docs = db.scalars(select(KnowledgeDocument).where(KnowledgeDocument.user_id == user_id)).all()
    for doc in docs:
        index_document(db, doc)
    exps = db.scalars(select(ExperienceMemory).where(ExperienceMemory.user_id == user_id)).all()
    for exp in exps:
        index_experience(exp)
    mems = db.scalars(select(ConversationMemory).where(ConversationMemory.user_id == user_id)).all()
    for mem in mems:
        index_conversation_memory(mem)
    db.commit()
    return {"knowledge_documents": len(docs), "experiences": len(exps), "conversation_memories": len(mems)}
