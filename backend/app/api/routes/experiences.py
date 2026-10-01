"""Experiences — episodic memory CRUD."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import DB, CurrentUser
from app.models import ExperienceMemory, Tag, User, experience_tags
from app.schemas.memory import ExperienceCreate, ExperienceOut, ExperienceUpdate
from app.services.indexing import index_experience
from app.services.tags import normalize_tags, resolve_tags

router = APIRouter(prefix="/experiences", tags=["experiences"])

TEXT_FIELDS = ("title", "situation", "what_happened", "lesson_learned", "do_differently", "context")


def to_out(exp: ExperienceMemory) -> ExperienceOut:
    return ExperienceOut(
        id=exp.id,
        title=exp.title,
        experience_type=exp.experience_type,
        situation=exp.situation,
        what_happened=exp.what_happened,
        lesson_learned=exp.lesson_learned,
        do_differently=exp.do_differently,
        context=exp.context,
        occurred_on=exp.occurred_on,
        importance=exp.importance,
        indexed=exp.embedding is not None,
        tags=[t.name for t in exp.tags],
        created_at=exp.created_at,
        updated_at=exp.updated_at,
    )


def get_owned_experience(db: Session, user: User, exp_id: int) -> ExperienceMemory:
    exp = db.scalar(select(ExperienceMemory).where(ExperienceMemory.id == exp_id, ExperienceMemory.user_id == user.id))
    if exp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experience not found")
    return exp


@router.get("", response_model=list[ExperienceOut])
def list_experiences(
    user: CurrentUser,
    db: DB,
    q: Annotated[str | None, Query(max_length=200)] = None,
    experience_type: str | None = None,
    tag: str | None = None,
) -> list[ExperienceOut]:
    stmt = select(ExperienceMemory).where(ExperienceMemory.user_id == user.id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(*(getattr(ExperienceMemory, f).ilike(like) for f in TEXT_FIELDS))
        )
    if experience_type:
        stmt = stmt.where(ExperienceMemory.experience_type == experience_type)
    if tag:
        tag_name = (normalize_tags([tag]) or [""])[0]
        stmt = stmt.where(
            ExperienceMemory.id.in_(
                select(experience_tags.c.experience_id)
                .join(Tag, Tag.id == experience_tags.c.tag_id)
                .where(Tag.user_id == user.id, Tag.name == tag_name)
            )
        )
    rows = db.scalars(stmt.order_by(ExperienceMemory.updated_at.desc())).all()
    return [to_out(e) for e in rows]


@router.post("", response_model=ExperienceOut, status_code=status.HTTP_201_CREATED)
def create_experience(body: ExperienceCreate, user: CurrentUser, db: DB) -> ExperienceOut:
    data = body.model_dump(exclude={"tags"})
    if not any(data[f].strip() for f in ("situation", "what_happened", "lesson_learned")):
        raise HTTPException(
            status_code=422,
            detail="Describe the situation, what happened, or what you learned",
        )
    exp = ExperienceMemory(user_id=user.id, **{k: v.strip() if isinstance(v, str) else v for k, v in data.items()})
    exp.tags = resolve_tags(db, user.id, body.tags)
    index_experience(exp)
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return to_out(exp)


@router.get("/{exp_id}", response_model=ExperienceOut)
def get_experience(exp_id: int, user: CurrentUser, db: DB) -> ExperienceOut:
    return to_out(get_owned_experience(db, user, exp_id))


@router.patch("/{exp_id}", response_model=ExperienceOut)
def update_experience(exp_id: int, body: ExperienceUpdate, user: CurrentUser, db: DB) -> ExperienceOut:
    exp = get_owned_experience(db, user, exp_id)
    changes = body.model_dump(exclude_unset=True, exclude={"tags"})
    for field, value in changes.items():
        if field == "occurred_on":
            exp.occurred_on = value
            continue
        if value is None:
            continue
        if field == "title" and not str(value).strip():
            raise HTTPException(status_code=422, detail="Title must not be blank")
        setattr(exp, field, value.strip() if isinstance(value, str) else value)
    if body.tags is not None:
        exp.tags = resolve_tags(db, user.id, body.tags)
    index_experience(exp)
    db.commit()
    db.refresh(exp)
    return to_out(exp)


@router.delete("/{exp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experience(exp_id: int, user: CurrentUser, db: DB) -> Response:
    exp = get_owned_experience(db, user, exp_id)
    db.delete(exp)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
