"""Knowledge Vault — long-term semantic memory CRUD + import."""

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import DB, CurrentUser
from app.core.config import get_settings
from app.models import KnowledgeChunk, KnowledgeDocument, Tag, User, knowledge_document_tags
from app.schemas.memory import KnowledgeCreate, KnowledgeListOut, KnowledgeOut, KnowledgeUpdate, KnowledgeUrlImport
from app.services.importers import ImportError_, extract_file_text, fetch_url_text
from app.services.indexing import index_document
from app.services.persona import KNOWLEDGE_CATEGORIES
from app.services.tags import normalize_tags, resolve_tags

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _chunk_stats(db: Session, doc_ids: list[int]) -> dict[int, tuple[int, int]]:
    if not doc_ids:
        return {}
    rows = db.execute(
        select(KnowledgeChunk.document_id, func.count(), func.count(KnowledgeChunk.embedding))
        .where(KnowledgeChunk.document_id.in_(doc_ids))
        .group_by(KnowledgeChunk.document_id)
    ).all()
    return {int(d): (int(total), int(embedded)) for d, total, embedded in rows}


def to_out(doc: KnowledgeDocument, stats: tuple[int, int]) -> KnowledgeOut:
    total, embedded = stats
    return KnowledgeOut(
        id=doc.id,
        title=doc.title,
        content=doc.content,
        category=doc.category,
        source_type=doc.source_type,
        source=doc.source,
        char_count=doc.char_count,
        chunk_count=total,
        indexed=total > 0 and embedded == total,
        tags=[t.name for t in doc.tags],
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def get_owned_document(db: Session, user: User, doc_id: int) -> KnowledgeDocument:
    doc = db.scalar(select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id, KnowledgeDocument.user_id == user.id))
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found")
    return doc


def _create(
    db: Session, user: User, *, title: str, content: str, category: str, source_type: str, source: str, tags: list[str]
) -> KnowledgeOut:
    doc = KnowledgeDocument(
        user_id=user.id,
        title=title.strip()[:200],
        content=content.strip(),
        category=category,
        source_type=source_type,
        source=source[:500],
    )
    doc.tags = resolve_tags(db, user.id, tags)
    db.add(doc)
    db.flush()
    index_document(db, doc)
    db.commit()
    db.refresh(doc)
    return to_out(doc, _chunk_stats(db, [doc.id]).get(doc.id, (0, 0)))


@router.get("", response_model=KnowledgeListOut)
def list_knowledge(
    user: CurrentUser,
    db: DB,
    q: Annotated[str | None, Query(max_length=200)] = None,
    category: str | None = None,
    tag: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> KnowledgeListOut:
    stmt = select(KnowledgeDocument).where(KnowledgeDocument.user_id == user.id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(KnowledgeDocument.title.ilike(like), KnowledgeDocument.content.ilike(like)))
    if category:
        stmt = stmt.where(KnowledgeDocument.category == category)
    if tag:
        tag_name = (normalize_tags([tag]) or [""])[0]
        stmt = stmt.where(
            KnowledgeDocument.id.in_(
                select(knowledge_document_tags.c.document_id)
                .join(Tag, Tag.id == knowledge_document_tags.c.tag_id)
                .where(Tag.user_id == user.id, Tag.name == tag_name)
            )
        )
    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    docs = db.scalars(stmt.order_by(KnowledgeDocument.updated_at.desc()).limit(limit).offset(offset)).all()
    stats = _chunk_stats(db, [d.id for d in docs])
    return KnowledgeListOut(items=[to_out(d, stats.get(d.id, (0, 0))) for d in docs], total=total)


@router.post("", response_model=KnowledgeOut, status_code=status.HTTP_201_CREATED)
def create_knowledge(body: KnowledgeCreate, user: CurrentUser, db: DB) -> KnowledgeOut:
    return _create(
        db,
        user,
        title=body.title,
        content=body.content,
        category=body.category,
        source_type=body.source_type,
        source=body.source or "manual entry",
        tags=body.tags,
    )


@router.post("/upload", response_model=KnowledgeOut, status_code=status.HTTP_201_CREATED)
async def upload_knowledge(
    user: CurrentUser,
    db: DB,
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form(max_length=200)] = None,
    category: Annotated[str, Form()] = "general",
    tags: Annotated[str, Form(max_length=500)] = "",
) -> KnowledgeOut:
    if category not in KNOWLEDGE_CATEGORIES:
        raise HTTPException(status_code=422, detail="Unknown category")
    limit = get_settings().MAX_UPLOAD_BYTES
    data = await file.read(limit + 1)
    filename = (file.filename or "upload.txt").replace("\\", "/").rsplit("/", 1)[-1]
    try:
        text = extract_file_text(filename, data)
    except ImportError_ as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _create(
        db,
        user,
        title=(title or filename.rsplit(".", 1)[0]).strip() or "Untitled document",
        content=text,
        category=category,
        source_type="document",
        source=filename,
        tags=[t for t in tags.split(",") if t.strip()],
    )


@router.post("/url", response_model=KnowledgeOut, status_code=status.HTTP_201_CREATED)
def import_url(body: KnowledgeUrlImport, user: CurrentUser, db: DB) -> KnowledgeOut:
    url = str(body.url)
    try:
        page_title, text = fetch_url_text(url)
    except ImportError_ as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _create(
        db,
        user,
        title=body.title or page_title or url,
        content=text,
        category=body.category,
        source_type="url",
        source=url,
        tags=body.tags,
    )


@router.get("/{doc_id}", response_model=KnowledgeOut)
def get_knowledge(doc_id: int, user: CurrentUser, db: DB) -> KnowledgeOut:
    doc = get_owned_document(db, user, doc_id)
    return to_out(doc, _chunk_stats(db, [doc.id]).get(doc.id, (0, 0)))


@router.patch("/{doc_id}", response_model=KnowledgeOut)
def update_knowledge(doc_id: int, body: KnowledgeUpdate, user: CurrentUser, db: DB) -> KnowledgeOut:
    doc = get_owned_document(db, user, doc_id)
    changes = body.model_dump(exclude_unset=True)
    reindex = False
    for field in ("title", "content", "category", "source"):
        if changes.get(field) is not None:
            value = changes[field].strip() if isinstance(changes[field], str) else changes[field]
            if field in ("title", "content") and not value:
                raise HTTPException(status_code=422, detail=f"{field} must not be blank")
            if getattr(doc, field) != value:
                setattr(doc, field, value)
                reindex = reindex or field in ("title", "content", "category")
    if body.tags is not None:
        doc.tags = resolve_tags(db, user.id, body.tags)
    if reindex:
        index_document(db, doc)
    db.commit()
    db.refresh(doc)
    return to_out(doc, _chunk_stats(db, [doc.id]).get(doc.id, (0, 0)))


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge(doc_id: int, user: CurrentUser, db: DB) -> Response:
    doc = get_owned_document(db, user, doc_id)
    db.delete(doc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
