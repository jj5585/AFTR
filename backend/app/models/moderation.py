import enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Text, Integer, DateTime, Enum as SQLEnum,
    ForeignKey, Uuid, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, utc_now


class ReportStatus(str, enum.Enum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    ACTIONED = "ACTIONED"
    DISMISSED = "DISMISSED"


class ModerationActionType(str, enum.Enum):
    WARNING = "WARNING"
    POST_REMOVED = "POST_REMOVED"
    SHADOWBAN = "SHADOWBAN"
    PERSONA_SUSPENDED = "PERSONA_SUSPENDED"
    ACCOUNT_BANNED = "ACCOUNT_BANNED"


class AppealStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Block(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "blocks"

    blocker_persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    blocked_persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("blocker_persona_id", "blocked_persona_id", name="uq_persona_block"),
        CheckConstraint("blocker_persona_id <> blocked_persona_id", name="chk_no_self_block"),
    )


class Report(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reports"

    reporter_persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )  # 'POST', 'COMMENT', 'PERSONA', 'MESSAGE', 'EVENT'
    target_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        index=True,
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus, native_enum=False, length=20),
        default=ReportStatus.PENDING,
        index=True,
        nullable=False,
    )


class ModerationAction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "moderation_actions"

    target_type: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        index=True,
        nullable=False,
    )
    action_type: Mapped[ModerationActionType] = mapped_column(
        SQLEnum(ModerationActionType, native_enum=False, length=30),
        index=True,
        nullable=False,
    )
    moderator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    strike_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )


class Appeal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "appeals"

    moderation_action_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("moderation_actions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    appellant_persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[AppealStatus] = mapped_column(
        SQLEnum(AppealStatus, native_enum=False, length=20),
        default=AppealStatus.PENDING,
        index=True,
        nullable=False,
    )
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class AuditLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "audit_logs"

    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        index=True,
        nullable=True,
    )
    actor_type: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )  # 'ACCOUNT', 'PERSONA', 'SYSTEM', 'MODERATOR'
    action: Mapped[str] = mapped_column(
        String(60),
        index=True,
        nullable=False,
    )
    target_type: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )
    target_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
    )
    ip_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )  # Salted SHA-256 for abuse mitigation, never raw IP
    details_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False,
    )
