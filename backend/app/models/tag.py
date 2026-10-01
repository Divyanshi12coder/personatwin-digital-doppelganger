from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Tag(Base):
    """A user-scoped label shared by knowledge, experiences and conversation memories."""

    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_tags_user_id_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(40), nullable=False)

    user: Mapped["User"] = relationship(back_populates="tags")


knowledge_document_tags = Table(
    "knowledge_document_tags",
    Base.metadata,
    Column("document_id", ForeignKey("knowledge_documents.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

experience_tags = Table(
    "experience_tags",
    Base.metadata,
    Column("experience_id", ForeignKey("experience_memories.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

conversation_memory_tags = Table(
    "conversation_memory_tags",
    Base.metadata,
    Column("memory_id", ForeignKey("conversation_memories.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)
