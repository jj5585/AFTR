import enum
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, Enum as SQLEnum,
    ForeignKey, Uuid, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class AttendeeStatus(str, enum.Enum):
    GOING = "GOING"
    INTERESTED = "INTERESTED"
    DECLINED = "DECLINED"


class Event(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "events"

    creator_persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    campus_name: Mapped[Optional[str]] = mapped_column(
        String(120),
        index=True,
        nullable=True,
    )  # Optional self-declared campus scope
    location_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )  # Named venue, strictly NO live GPS coordinates
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )
    max_attendees: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    is_cancelled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    attendees: Mapped[List["EventAttendee"]] = relationship(
        "EventAttendee",
        back_populates="event",
        cascade="all, delete-orphan",
    )


class EventAttendee(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "event_attendees"

    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[AttendeeStatus] = mapped_column(
        SQLEnum(AttendeeStatus, native_enum=False, length=20),
        default=AttendeeStatus.GOING,
        nullable=False,
    )

    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="attendees",
    )

    __table_args__ = (
        UniqueConstraint("event_id", "persona_id", name="uq_event_attendee"),
    )
