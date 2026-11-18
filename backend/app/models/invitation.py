import enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Enum as SQLEnum, ForeignKey, Uuid, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class InvitationStatus(str, enum.Enum):
    PENDING = "PENDING"
    USED = "USED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class Invitation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "invitations"

    inviter_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    recipient_hash: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )
    status: Mapped[InvitationStatus] = mapped_column(
        SQLEnum(InvitationStatus, native_enum=False, length=20),
        default=InvitationStatus.PENDING,
        index=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )
    used_by_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    inviter_account: Mapped["Account"] = relationship(
        "Account",
        foreign_keys=[inviter_account_id],
        back_populates="invitations_sent",
    )
    used_by_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[used_by_account_id],
    )

    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="chk_invitation_expiry_future"),
        CheckConstraint(
            "(status <> 'USED') OR (used_by_account_id IS NOT NULL AND used_at IS NOT NULL)",
            name="chk_invitation_used_integrity",
        ),
        CheckConstraint(
            "(status <> 'REVOKED') OR (revoked_at IS NOT NULL)",
            name="chk_invitation_revoked_integrity",
        ),
        CheckConstraint(
            "(used_by_account_id IS NULL) OR (used_by_account_id <> inviter_account_id)",
            name="chk_no_self_invitation",
        ),
    )
