import enum
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, Text, Boolean, Float, DateTime, Enum as SQLEnum,
    ForeignKey, Uuid, UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class ConnectionRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    WITHDRAWN = "WITHDRAWN"


class ConnectionRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "connection_requests"

    sender_persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    recipient_persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[ConnectionRequestStatus] = mapped_column(
        SQLEnum(ConnectionRequestStatus, native_enum=False, length=20),
        default=ConnectionRequestStatus.PENDING,
        index=True,
        nullable=False,
    )
    note: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    sender_persona: Mapped["Persona"] = relationship(
        "Persona",
        foreign_keys=[sender_persona_id],
    )
    recipient_persona: Mapped["Persona"] = relationship(
        "Persona",
        foreign_keys=[recipient_persona_id],
    )

    __table_args__ = (
        UniqueConstraint("sender_persona_id", "recipient_persona_id", name="uq_sender_recipient_connection"),
        CheckConstraint("sender_persona_id <> recipient_persona_id", name="chk_no_self_connection_request"),
    )


class Match(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "matches"

    persona_a_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    persona_b_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    compatibility_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    persona_a: Mapped["Persona"] = relationship(
        "Persona",
        foreign_keys=[persona_a_id],
    )
    persona_b: Mapped["Persona"] = relationship(
        "Persona",
        foreign_keys=[persona_b_id],
    )

    __table_args__ = (
        UniqueConstraint("persona_a_id", "persona_b_id", name="uq_canonical_match_pair"),
        CheckConstraint("persona_a_id <> persona_b_id", name="chk_no_self_match"),
    )


class Conversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversations"

    connection_request_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("connection_requests.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )
    match_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("matches.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    blocked_by_persona_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="SET NULL"),
        nullable=True,
    )

    participants: Mapped[List["ConversationParticipant"]] = relationship(
        "ConversationParticipant",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class ConversationParticipant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversation_participants"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    conversation_pseudonym: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    last_read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="participants",
    )
    persona: Mapped["Persona"] = relationship(
        "Persona",
        foreign_keys=[persona_id],
    )

    __table_args__ = (
        UniqueConstraint("conversation_id", "persona_id", name="uq_conversation_participant"),
    )


class Message(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sender_persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
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
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_encrypted: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )
    sender_persona: Mapped["Persona"] = relationship(
        "Persona",
        foreign_keys=[sender_persona_id],
    )

    __table_args__ = (
        Index("ix_messages_created_at", "created_at"),
        Index("ix_messages_conv_created", "conversation_id", "created_at"),
    )
