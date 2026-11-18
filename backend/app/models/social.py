import enum
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, Integer, DateTime, Enum as SQLEnum, ForeignKey, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class PostType(str, enum.Enum):
    CONFESSION = "CONFESSION"
    DISCUSSION = "DISCUSSION"
    GENERAL = "GENERAL"


class Post(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "posts"

    persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    post_type: Mapped[PostType] = mapped_column(
        SQLEnum(PostType, native_enum=False, length=20),
        default=PostType.CONFESSION,
        index=True,
        nullable=False,
    )
    tag: Mapped[str] = mapped_column(
        String(50),
        default="general",
        index=True,
        nullable=False,
    )
    is_sensitive: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    allow_comments: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    moderation_status: Mapped[str] = mapped_column(
        String(20),
        default="PUBLISHED",
        index=True,
        nullable=False,
    )
    campus_name: Mapped[Optional[str]] = mapped_column(
        String(120),
        index=True,
        nullable=True,
    )

    # Relationships
    persona: Mapped["Persona"] = relationship(
        "Persona",
        back_populates="posts",
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan",
    )


class Comment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "comments"

    post_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    post: Mapped["Post"] = relationship(
        "Post",
        back_populates="comments",
    )
    persona: Mapped["Persona"] = relationship(
        "Persona",
        back_populates="comments",
    )
    parent: Mapped[Optional["Comment"]] = relationship(
        "Comment",
        remote_side="Comment.id",
        back_populates="replies",
    )
    replies: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan",
    )


class Reaction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reactions"

    persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(
        String(20),
        index=True,
        nullable=False,
    )  # 'POST', 'COMMENT'
    target_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        index=True,
        nullable=False,
    )
    reaction_type: Mapped[str] = mapped_column(
        String(20),
        default="UPVOTE",
        nullable=False,
    )

    persona: Mapped["Persona"] = relationship(
        "Persona",
        back_populates="reactions",
    )

    __table_args__ = (
        UniqueConstraint("persona_id", "target_type", "target_id", "reaction_type", name="uq_persona_reaction_target"),
    )


class Story(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "stories"

    persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )

    persona: Mapped["Persona"] = relationship(
        "Persona",
        back_populates="stories",
    )
