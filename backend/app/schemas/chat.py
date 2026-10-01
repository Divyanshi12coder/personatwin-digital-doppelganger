from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=20000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: int | None = None
    # Only used when the user has turned off conversation saving (privacy mode):
    # the client then owns the short-term memory and sends it with each request.
    history: list[HistoryItem] = Field(default_factory=list, max_length=20)

    @field_validator("message")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message must not be blank")
        return v.strip()


class SourceOut(ORMModel):
    label: str
    source_type: str
    source_id: int
    title: str
    snippet: str
    score: float
    cited: bool


class MessageOut(BaseModel):
    id: int | None
    role: str
    content: str
    created_at: datetime
    topic: str = "general"
    feedback: str | None = None
    grounding: str | None = None
    provider: str | None = None
    model: str | None = None
    latency_ms: int | None = None
    sources: list[SourceOut] = Field(default_factory=list)
    trace: dict[str, Any] | None = None
    remembered: bool = False


class ChatResponse(BaseModel):
    conversation_id: int | None
    conversation_title: str | None
    persisted: bool
    user_message: MessageOut
    assistant_message: MessageOut
    remembered_memory_id: int | None = None


class FeedbackRequest(BaseModel):
    feedback: Literal["up", "down"] | None


class ConversationOut(ORMModel):
    id: int
    title: str
    topic: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: str | None = None


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
