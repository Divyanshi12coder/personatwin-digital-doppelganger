"""Persona memory: who the mentor is and how it communicates.

This is configuration the user writes, not a psychological assessment.
Short lists (expertise, values, phrases) are JSON arrays of strings; every
scalar trait has its own column so it can be validated and queried.
"""

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class MentorProfile(TimestampMixin, Base):
    __tablename__ = "mentor_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    mentor_name: Mapped[str] = mapped_column(String(80), nullable=False)
    bio: Mapped[str] = mapped_column(Text, default="", nullable=False)
    expertise_areas: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    mentoring_domains: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="mentor_profile")


class PersonalityProfile(TimestampMixin, Base):
    __tablename__ = "personality_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    communication_style: Mapped[str] = mapped_column(String(32), default="warm", nullable=False)
    tone: Mapped[str] = mapped_column(String(32), default="encouraging", nullable=False)
    teaching_approach: Mapped[str] = mapped_column(String(32), default="examples_first", nullable=False)
    decision_style: Mapped[str] = mapped_column(String(32), default="analytical", nullable=False)
    encouragement_style: Mapped[str] = mapped_column(String(32), default="celebrate_progress", nullable=False)
    response_length: Mapped[str] = mapped_column(String(16), default="balanced", nullable=False)

    # 0..100 sliders
    formality: Mapped[int] = mapped_column(Integer, default=40, nullable=False)
    directness: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    warmth: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    humor: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    values: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    signature_phrases: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    # Mentoring philosophy (free text, written by the user)
    philosophy_encouragement: Mapped[str] = mapped_column(Text, default="", nullable=False)
    philosophy_mistakes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    philosophy_decisions: Mapped[str] = mapped_column(Text, default="", nullable=False)
    philosophy_teaching: Mapped[str] = mapped_column(Text, default="", nullable=False)
    boundaries: Mapped[str] = mapped_column(Text, default="", nullable=False)

    user: Mapped["User"] = relationship(back_populates="personality")


class UserSettings(TimestampMixin, Base):
    """Memory + AI behaviour controls the user owns."""

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    save_conversations: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_conversation_memory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_remember: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    retrieval_top_k: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    min_relevance: Mapped[float] = mapped_column(Float, default=0.12, nullable=False)
    creativity: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    show_sources: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="settings")
