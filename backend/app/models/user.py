from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.conversation import Conversation, ConversationMemory
    from app.models.experience import ExperienceMemory
    from app.models.knowledge import KnowledgeDocument
    from app.models.mentor import MentorProfile, PersonalityProfile, UserSettings
    from app.models.tag import Tag


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Bumped on logout / password change -> revokes all outstanding JWTs.
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    mentor_profile: Mapped["MentorProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )
    personality: Mapped["PersonalityProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )
    settings: Mapped["UserSettings | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )
    knowledge_documents: Mapped[list["KnowledgeDocument"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    experiences: Mapped[list["ExperienceMemory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    conversation_memories: Mapped[list["ConversationMemory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    tags: Mapped[list["Tag"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
