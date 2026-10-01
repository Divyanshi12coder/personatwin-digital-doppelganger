"""Episodic memory: specific, structured experiences the user actually lived."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import EMBEDDING_DIM
from app.db.base import Base, TimestampMixin
from app.db.types import EmbeddingVector
from app.models.tag import Tag, experience_tags

if TYPE_CHECKING:
    from app.models.user import User


class ExperienceMemory(TimestampMixin, Base):
    __tablename__ = "experience_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # lesson|career|failure|success|decision|teaching|memorable|advice
    experience_type: Mapped[str] = mapped_column(String(24), default="lesson", index=True, nullable=False)
    situation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    what_happened: Mapped[str] = mapped_column(Text, default="", nullable=False)
    lesson_learned: Mapped[str] = mapped_column(Text, default="", nullable=False)
    do_differently: Mapped[str] = mapped_column(Text, default="", nullable=False)
    context: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    occurred_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=3, nullable=False)  # 1..5
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector(EMBEDDING_DIM), nullable=True)

    user: Mapped["User"] = relationship(back_populates="experiences")
    tags: Mapped[list[Tag]] = relationship(secondary=experience_tags, lazy="selectin")

    def embedding_text(self) -> str:
        parts = [
            self.title,
            f"Situation: {self.situation}",
            f"What happened: {self.what_happened}",
            f"Lesson: {self.lesson_learned}",
            f"Would do differently: {self.do_differently}",
            f"Context: {self.context}",
            "Tags: " + ", ".join(t.name for t in self.tags),
        ]
        return "\n".join(p for p in parts if p.split(":", 1)[-1].strip())
