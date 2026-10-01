import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tag import Tag

MAX_TAGS = 12
MAX_TAG_LEN = 40


def normalize_tags(names: list[str]) -> list[str]:
    seen: list[str] = []
    for raw in names:
        name = re.sub(r"\s+", " ", raw.strip().lower().lstrip("#"))[:MAX_TAG_LEN]
        if name and name not in seen:
            seen.append(name)
    return seen[:MAX_TAGS]


def resolve_tags(db: Session, user_id: int, names: list[str]) -> list[Tag]:
    """Return Tag rows owned by ``user_id`` for the given names, creating missing ones."""
    wanted = normalize_tags(names)
    if not wanted:
        return []
    existing = {t.name: t for t in db.scalars(select(Tag).where(Tag.user_id == user_id, Tag.name.in_(wanted)))}
    result: list[Tag] = []
    for name in wanted:
        tag = existing.get(name)
        if tag is None:
            tag = Tag(user_id=user_id, name=name)
            db.add(tag)
        result.append(tag)
    return result
