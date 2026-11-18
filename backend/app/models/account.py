import enum
import uuid
from typing import List, Optional
from sqlalchemy import String, Integer, Boolean, Enum as SQLEnum, Uuid, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class AccountStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    BANNED = "BANNED"


class Account(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "accounts"

    supabase_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        unique=True,
        index=True,
        nullable=False,
    )
    email_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    is_age_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    birth_year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    invite_quota: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )
    status: Mapped[AccountStatus] = mapped_column(
        SQLEnum(AccountStatus, native_enum=False, length=20),
        default=AccountStatus.ACTIVE,
        nullable=False,
    )

    # Decoupled relationships
    personas: Mapped[List["Persona"]] = relationship(
        "Persona",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    invitations_sent: Mapped[List["Invitation"]] = relationship(
        "Invitation",
        foreign_keys="Invitation.inviter_account_id",
        back_populates="inviter_account",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("invite_quota >= 0", name="chk_account_invite_quota_non_negative"),
    )
