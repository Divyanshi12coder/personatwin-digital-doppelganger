from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.schemas.common import ORMModel, TagList
from app.services.persona import EXPERIENCE_TYPES, KNOWLEDGE_CATEGORIES


def _check_category(v: str) -> str:
    if v not in KNOWLEDGE_CATEGORIES:
        raise ValueError(f"must be one of: {', '.join(KNOWLEDGE_CATEGORIES)}")
    return v


# ------------------------------------------------------------- knowledge


class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=200_000)
    category: str = "general"
    source_type: Literal["text", "note"] = "text"
    source: str = Field(default="", max_length=500)
    tags: TagList

    check_category = field_validator("category")(_check_category)

    @field_validator("title", "content")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class KnowledgeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=200_000)
    category: str | None = None
    source: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = Field(default=None, max_length=24)

    @field_validator("category")
    @classmethod
    def check_cat(cls, v: str | None) -> str | None:
        return None if v is None else _check_category(v)


class KnowledgeUrlImport(BaseModel):
    url: HttpUrl
    title: str | None = Field(default=None, max_length=200)
    category: str = "general"
    tags: TagList

    check_category = field_validator("category")(_check_category)


class KnowledgeOut(ORMModel):
    id: int
    title: str
    content: str
    category: str
    source_type: str
    source: str
    char_count: int
    chunk_count: int
    indexed: bool
    tags: list[str]
    created_at: datetime
    updated_at: datetime


class KnowledgeListOut(BaseModel):
    items: list[KnowledgeOut]
    total: int


# ------------------------------------------------------------- experiences


def _check_type(v: str) -> str:
    if v not in EXPERIENCE_TYPES:
        raise ValueError(f"must be one of: {', '.join(EXPERIENCE_TYPES)}")
    return v


class ExperienceBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    experience_type: str = "lesson"
    situation: str = Field(default="", max_length=5000)
    what_happened: str = Field(default="", max_length=5000)
    lesson_learned: str = Field(default="", max_length=5000)
    do_differently: str = Field(default="", max_length=5000)
    context: str = Field(default="", max_length=200)
    occurred_on: date | None = None
    importance: int = Field(default=3, ge=1, le=5)
    tags: TagList

    check_experience_type = field_validator("experience_type")(_check_type)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @field_validator("occurred_on")
    @classmethod
    def not_future(cls, v: date | None) -> date | None:
        if v and v > date.today():
            raise ValueError("cannot be in the future")
        return v


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    experience_type: str | None = None
    situation: str | None = Field(default=None, max_length=5000)
    what_happened: str | None = Field(default=None, max_length=5000)
    lesson_learned: str | None = Field(default=None, max_length=5000)
    do_differently: str | None = Field(default=None, max_length=5000)
    context: str | None = Field(default=None, max_length=200)
    occurred_on: date | None = None
    importance: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] | None = Field(default=None, max_length=24)

    @field_validator("experience_type")
    @classmethod
    def check_type(cls, v: str | None) -> str | None:
        return None if v is None else _check_type(v)

    @field_validator("occurred_on")
    @classmethod
    def not_future(cls, v: date | None) -> date | None:
        if v and v > date.today():
            raise ValueError("cannot be in the future")
        return v


class ExperienceOut(ORMModel):
    id: int
    title: str
    experience_type: str
    situation: str
    what_happened: str
    lesson_learned: str
    do_differently: str
    context: str
    occurred_on: date | None
    importance: int
    indexed: bool
    tags: list[str]
    created_at: datetime
    updated_at: datetime


# ------------------------------------------------------------- conversation memories


class ConversationMemoryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=10000)
    tags: list[str] | None = Field(default=None, max_length=24)


class ConversationMemoryOut(ORMModel):
    id: int
    title: str
    content: str
    topic: str
    conversation_id: int | None
    indexed: bool
    tags: list[str]
    created_at: datetime
    updated_at: datetime


# ------------------------------------------------------------- unified inspector

MemoryType = Literal["knowledge", "experience", "conversation", "preference"]


class MemoryItem(BaseModel):
    id: str  # "<type>:<id>" — unique across stores
    ref_id: int | None
    type: MemoryType
    title: str
    category: str
    snippet: str
    tags: list[str]
    source: str
    date: datetime | None
    relevance: float | None = None
    indexed: bool = True


class MemoryListOut(BaseModel):
    items: list[MemoryItem]
    counts: dict[str, int]
    query: str | None = None
