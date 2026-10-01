"""Conversations (short-term memory) and conversation memories (opt-in long-term notes)."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import EMBEDDING_DIM
from app.db.base import Base, TimestampMixin, utcnow
from app.db.types import EmbeddingVector
from app.models.tag import Tag, conversation_memory_tags

if TYPE_CHECKING:
    from app.models.user import User


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), default="New conversation", nullable=False)
    topic: Mapped[str] = mapped_column(String(32), default="general", nullable=False)

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.id",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user|assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(32), default="general", index=True, nullable=False)
    feedback: Mapped[str | None] = mapped_column(String(8), nullable=True)  # up|down
    grounding: Mapped[str | None] = mapped_column(String(16), nullable=True)  # grounded|partial|ungrounded
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Small structured record of the pipeline run (step timings + counts). Never the raw prompt.
    trace: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    sources: Mapped[list["MessageSource"]] = relationship(
        back_populates="message", cascade="all, delete-orphan", passive_deletes=True, order_by="MessageSource.id"
    )


class MessageSource(Base):
    """Snapshot of a memory that grounded an assistant message (survives memory deletion)."""

    __tablename__ = "message_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(8), nullable=False)  # K1, E2, C1
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)  # knowledge|experience|conversation
    source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    cited: Mapped[bool] = mapped_column(default=False, nullable=False)

    message: Mapped[Message] = relationship(back_populates="sources")


class ConversationMemory(TimestampMixin, Base):
    """A conversation exchange the user explicitly chose to remember.

    These are clearly labelled as *past mentor conversations* (partly AI-generated),
    never as the user's own lived experiences.
    """

    __tablename__ = "conversation_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    conversation_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(32), default="general", nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector(EMBEDDING_DIM), nullable=True)

    user: Mapped["User"] = relationship(back_populates="conversation_memories")
    tags: Mapped[list[Tag]] = relationship(secondary=conversation_memory_tags, lazy="selectin")
