import uuid
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, ForeignKey, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Persona(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "personas"

    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )
    avatar_seed: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_discoverable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
        nullable=False,
    )
    relationship_intention: Mapped[Optional[str]] = mapped_column(
        String(50),
        index=True,
        nullable=True,
    )
    min_age_preference: Mapped[int] = mapped_column(
        default=18,
        nullable=False,
    )
    max_age_preference: Mapped[int] = mapped_column(
        default=99,
        nullable=False,
    )
    dating_preferences_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="personas",
    )
    campus_affiliations: Mapped[List["CampusAffiliation"]] = relationship(
        "CampusAffiliation",
        back_populates="persona",
        cascade="all, delete-orphan",
    )
    interests: Mapped[List["PersonaInterest"]] = relationship(
        "PersonaInterest",
        back_populates="persona",
        cascade="all, delete-orphan",
    )
    posts: Mapped[List["Post"]] = relationship(
        "Post",
        back_populates="persona",
        cascade="all, delete-orphan",
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="persona",
        cascade="all, delete-orphan",
    )
    reactions: Mapped[List["Reaction"]] = relationship(
        "Reaction",
        back_populates="persona",
        cascade="all, delete-orphan",
    )
    stories: Mapped[List["Story"]] = relationship(
        "Story",
        back_populates="persona",
        cascade="all, delete-orphan",
    )


class CampusAffiliation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "campus_affiliations"

    persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    campus_name: Mapped[str] = mapped_column(
        String(120),
        index=True,
        nullable=False,
    )
    campus_code: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    persona: Mapped["Persona"] = relationship(
        "Persona",
        back_populates="campus_affiliations",
    )


class Interest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "interests"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    is_adult: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    persona_associations: Mapped[List["PersonaInterest"]] = relationship(
        "PersonaInterest",
        back_populates="interest",
        cascade="all, delete-orphan",
    )


class PersonaInterest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "persona_interests"

    persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    interest_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interests.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    persona: Mapped["Persona"] = relationship(
        "Persona",
        back_populates="interests",
    )
    interest: Mapped["Interest"] = relationship(
        "Interest",
        back_populates="persona_associations",
    )

    __table_args__ = (
        UniqueConstraint("persona_id", "interest_id", name="uq_persona_interest"),
    )
