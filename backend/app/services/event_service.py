import re
import uuid
from datetime import timedelta, datetime
from typing import Optional, List, Set, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy import select, or_, and_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.persona import Persona, CampusAffiliation
from backend.app.models.event import Event, EventAttendee, AttendeeStatus
from backend.app.models.base import utc_now
from backend.app.core.pagination import encode_cursor, decode_cursor
from backend.app.schemas.social import PersonaPublicResponse
from backend.app.schemas.stories_events import (
    EventCreateRequest,
    EventUpdateRequest,
    EventResponse,
    EventsListResponse,
    EventAttendeeResponse,
)
from backend.app.services.moderation_engine import ContentModerationEngine
from backend.app.services.social_service import SocialService

# Regex to detect GPS latitude/longitude coordinates
COORDINATES_PATTERN = re.compile(r"^-?\d{1,3}\.\d+[\s,]+-?\d{1,3}\.\d+$")

# Regex to detect private residences, apartment numbers, dorm rooms
RESIDENTIAL_PATTERN = re.compile(
    r"\b(my\s+(house|apt|apartment|dorm|room|flat|place|residence|home)|private\s+residence|bedroom|apt\.?\s*#?\d+|unit\s*#?\d+|suite\s*#?\d+|dorm\s*#?\d+|room\s*#?\d+)\b",
    re.IGNORECASE,
)


class EventService:
    @staticmethod
    def validate_public_venue(location_name: str) -> None:
        """
        Enforce safety requirement:
        - Strictly NO live GPS coordinates
        - Strictly NO private home or apartment addresses
        - Requires a recognized named public venue (e.g. student union, quad, cafe, park, hall)
        """
        trimmed = location_name.strip()
        if COORDINATES_PATTERN.match(trimmed):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Live GPS coordinates are prohibited for safety. Please provide a named public venue.",
            )

        if RESIDENTIAL_PATTERN.search(trimmed):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location must be a named public venue (e.g. library, campus quad, cafe, tavern). Private residential addresses, dorm rooms, and apartments are prohibited for community safety.",
            )

    @staticmethod
    async def get_declared_campus(db: AsyncSession, persona_id: uuid.UUID) -> Optional[str]:
        """Fetch primary declared campus for a persona."""
        stmt = (
            select(CampusAffiliation.campus_name)
            .where(CampusAffiliation.persona_id == persona_id)
            .order_by(CampusAffiliation.is_primary.desc())
            .limit(1)
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def create_event(
        db: AsyncSession,
        current_persona: Persona,
        data: EventCreateRequest,
    ) -> EventResponse:
        """
        Create a public group event:
        - Validates date is in the future
        - Validates public venue
        - Checks content moderation on title, description, and location
        - Automatically marks organizer as GOING
        """
        now = utc_now()
        if data.event_time <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event date and time must be set in the future.",
            )

        EventService.validate_public_venue(data.location_name)

        # Moderation check on all text fields
        full_text = f"{data.title}\n{data.description}\n{data.location_name}"
        mod_result = ContentModerationEngine.evaluate_text(full_text)
        if not mod_result.is_allowed:
            flag_str = ", ".join(mod_result.flagged_reasons) or mod_result.rejection_message or "Policy violation"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Event details flagged by Privacy Shield: {flag_str}.",
            )

        campus = data.campus_name or (await EventService.get_declared_campus(db, current_persona.id))

        event = Event(
            creator_persona_id=current_persona.id,
            title=data.title,
            description=data.description,
            campus_name=campus,
            location_name=data.location_name,
            event_time=data.event_time,
            max_attendees=data.max_attendees,
            is_cancelled=False,
            is_deleted=False,
        )
        db.add(event)
        await db.flush()

        # Auto-RSVP organizer as GOING
        attendee = EventAttendee(
            event_id=event.id,
            persona_id=current_persona.id,
            status=AttendeeStatus.GOING,
        )
        db.add(attendee)

        await db.commit()
        await db.refresh(event)

        author_campus = await EventService.get_declared_campus(db, current_persona.id)

        return EventResponse(
            id=event.id,
            creator_persona=PersonaPublicResponse(
                id=current_persona.id,
                display_name=current_persona.display_name,
                avatar_seed=current_persona.avatar_seed,
                declared_campus=author_campus,
                is_active=current_persona.is_active,
            ),
            title=event.title,
            description=event.description,
            location_name=event.location_name,
            event_time=event.event_time,
            campus_name=event.campus_name,
            max_attendees=event.max_attendees,
            attendees_count=1,
            interested_count=0,
            user_rsvp_status="GOING",
            is_cancelled=False,
            is_organizer=True,
            created_at=event.created_at,
        )

    @staticmethod
    async def get_events(
        db: AsyncSession,
        current_persona: Optional[Persona] = None,
        campus: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> EventsListResponse:
        """
        List upcoming and active public group events.
        Enforces bilateral blocking and optional campus filter.
        """
        now = utc_now()
        current_persona_id = current_persona.id if current_persona else None
        blocked_ids: Set[uuid.UUID] = await SocialService.get_blocked_persona_ids(db, current_persona_id)

        # Allow events that started recently (within 6 hours) or are upcoming
        time_cutoff = now - timedelta(hours=6)

        conditions = [
            Event.is_deleted == False,
            Event.event_time >= time_cutoff,
        ]

        if blocked_ids:
            conditions.append(Event.creator_persona_id.not_in(blocked_ids))

        if campus and campus.lower() != "all":
            conditions.append(Event.campus_name.ilike(f"%{campus}%"))

        if cursor:
            cursor_data = decode_cursor(cursor)
            if cursor_data:
                dt, item_id = cursor_data
                conditions.append(
                    or_(
                        Event.event_time > dt,
                        and_(Event.event_time == dt, Event.id > item_id),
                    )
                )

        stmt = (
            select(Event)
            .options(selectinload(Event.creator_persona))
            .where(*conditions)
            .order_by(Event.event_time.asc(), Event.id.asc())
            .limit(limit + 1)
        )
        events = list((await db.execute(stmt)).scalars().all())

        has_more = len(events) > limit
        if has_more:
            events = events[:limit]

        event_ids = [e.id for e in events]

        # Aggregate attendee counts
        attendee_counts: Dict[uuid.UUID, int] = {}
        interested_counts: Dict[uuid.UUID, int] = {}
        user_rsvp_map: Dict[uuid.UUID, str] = {}

        if event_ids:
            att_stmt = (
                select(EventAttendee.event_id, EventAttendee.status, func.count(EventAttendee.id))
                .where(EventAttendee.event_id.in_(event_ids))
                .group_by(EventAttendee.event_id, EventAttendee.status)
            )
            for eid, status_enum, count in (await db.execute(att_stmt)).all():
                if status_enum == AttendeeStatus.GOING:
                    attendee_counts[eid] = count
                elif status_enum == AttendeeStatus.INTERESTED:
                    interested_counts[eid] = count

            if current_persona_id:
                user_rsvp_stmt = select(EventAttendee.event_id, EventAttendee.status).where(
                    EventAttendee.event_id.in_(event_ids),
                    EventAttendee.persona_id == current_persona_id,
                )
                for eid, st in (await db.execute(user_rsvp_stmt)).all():
                    user_rsvp_map[eid] = st.value

        items: List[EventResponse] = []
        for e in events:
            creator = e.creator_persona
            creator_campus = await EventService.get_declared_campus(db, creator.id) if creator else None

            items.append(
                EventResponse(
                    id=e.id,
                    creator_persona=PersonaPublicResponse(
                        id=creator.id if creator else e.creator_persona_id,
                        display_name=creator.display_name if creator else "Anonymous Organizer",
                        avatar_seed=creator.avatar_seed if creator else "seed",
                        declared_campus=creator_campus,
                        is_active=creator.is_active if creator else False,
                    ),
                    title=e.title,
                    description=e.description,
                    location_name=e.location_name,
                    event_time=e.event_time,
                    campus_name=e.campus_name,
                    max_attendees=e.max_attendees,
                    attendees_count=attendee_counts.get(e.id, 0),
                    interested_count=interested_counts.get(e.id, 0),
                    user_rsvp_status=user_rsvp_map.get(e.id),
                    is_cancelled=e.is_cancelled,
                    is_organizer=(current_persona_id == e.creator_persona_id),
                    created_at=e.created_at,
                )
            )

        next_cursor = None
        if has_more and events:
            last = events[-1]
            next_cursor = encode_cursor(last.event_time, last.id)

        return EventsListResponse(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    @staticmethod
    async def get_event_detail(
        db: AsyncSession,
        current_persona: Optional[Persona],
        event_id: uuid.UUID,
    ) -> EventResponse:
        """Fetch single event details with organizer flags and RSVP counters."""
        event = await db.get(Event, event_id)
        if not event or event.is_deleted:
            raise HTTPException(status_code=404, detail="Event not found.")

        current_persona_id = current_persona.id if current_persona else None
        blocked_ids = await SocialService.get_blocked_persona_ids(db, current_persona_id)
        if event.creator_persona_id in blocked_ids:
            raise HTTPException(status_code=404, detail="Event not found.")

        creator = await db.get(Persona, event.creator_persona_id)
        creator_campus = await EventService.get_declared_campus(db, event.creator_persona_id)

        # Count attendees
        cnt_going_stmt = select(func.count(EventAttendee.id)).where(
            EventAttendee.event_id == event_id, EventAttendee.status == AttendeeStatus.GOING
        )
        going_count = (await db.execute(cnt_going_stmt)).scalar() or 0

        cnt_interested_stmt = select(func.count(EventAttendee.id)).where(
            EventAttendee.event_id == event_id, EventAttendee.status == AttendeeStatus.INTERESTED
        )
        interested_count = (await db.execute(cnt_interested_stmt)).scalar() or 0

        user_status = None
        if current_persona_id:
            user_st_stmt = select(EventAttendee.status).where(
                EventAttendee.event_id == event_id, EventAttendee.persona_id == current_persona_id
            )
            val = (await db.execute(user_st_stmt)).scalar_one_or_none()
            user_status = val.value if val else None

        return EventResponse(
            id=event.id,
            creator_persona=PersonaPublicResponse(
                id=creator.id if creator else event.creator_persona_id,
                display_name=creator.display_name if creator else "Anonymous Organizer",
                avatar_seed=creator.avatar_seed if creator else "seed",
                declared_campus=creator_campus,
                is_active=creator.is_active if creator else False,
            ),
            title=event.title,
            description=event.description,
            location_name=event.location_name,
            event_time=event.event_time,
            campus_name=event.campus_name,
            max_attendees=event.max_attendees,
            attendees_count=going_count,
            interested_count=interested_count,
            user_rsvp_status=user_status,
            is_cancelled=event.is_cancelled,
            is_organizer=(current_persona_id == event.creator_persona_id),
            created_at=event.created_at,
        )

    @staticmethod
    async def update_event(
        db: AsyncSession,
        current_persona: Persona,
        event_id: uuid.UUID,
        data: EventUpdateRequest,
    ) -> EventResponse:
        """Organizer controls: Update event details."""
        event = await db.get(Event, event_id)
        if not event or event.is_deleted:
            raise HTTPException(status_code=404, detail="Event not found.")

        if event.creator_persona_id != current_persona.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the event organizer can modify this event.",
            )

        if data.location_name:
            EventService.validate_public_venue(data.location_name)
            event.location_name = data.location_name

        if data.title:
            event.title = data.title

        if data.description:
            event.description = data.description

        if data.event_time:
            if data.event_time <= utc_now():
                raise HTTPException(status_code=400, detail="Event time must be in the future.")
            event.event_time = data.event_time

        if data.max_attendees is not None:
            event.max_attendees = data.max_attendees

        await db.commit()
        await db.refresh(event)

        return await EventService.get_event_detail(db, current_persona, event_id)

    @staticmethod
    async def cancel_event(
        db: AsyncSession,
        current_persona: Persona,
        event_id: uuid.UUID,
    ) -> EventResponse:
        """Organizer controls: Cancel event."""
        event = await db.get(Event, event_id)
        if not event or event.is_deleted:
            raise HTTPException(status_code=404, detail="Event not found.")

        if event.creator_persona_id != current_persona.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the event organizer can cancel this event.",
            )

        event.is_cancelled = True
        await db.commit()
        await db.refresh(event)

        return await EventService.get_event_detail(db, current_persona, event_id)

    @staticmethod
    async def rsvp_event(
        db: AsyncSession,
        current_persona: Persona,
        event_id: uuid.UUID,
        status_str: str = "GOING",
    ) -> EventResponse:
        """
        RSVP to public group event:
        - Prevents RSVP to cancelled events
        - Enforces attendance capacity
        - Supports GOING or INTERESTED
        """
        event = await db.get(Event, event_id)
        if not event or event.is_deleted:
            raise HTTPException(status_code=404, detail="Event not found.")

        if event.is_cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This event has been cancelled by the organizer.",
            )

        # Bilateral block check
        blocked_ids = await SocialService.get_blocked_persona_ids(db, current_persona.id)
        if event.creator_persona_id in blocked_ids:
            raise HTTPException(status_code=403, detail="Action not permitted.")

        status_enum = (
            AttendeeStatus.GOING if status_str.upper() == "GOING" else AttendeeStatus.INTERESTED
        )

        # Check capacity
        if status_enum == AttendeeStatus.GOING and event.max_attendees:
            cnt_stmt = select(func.count(EventAttendee.id)).where(
                EventAttendee.event_id == event_id,
                EventAttendee.status == AttendeeStatus.GOING,
                EventAttendee.persona_id != current_persona.id,
            )
            current_going = (await db.execute(cnt_stmt)).scalar() or 0
            if current_going >= event.max_attendees:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Event has reached maximum attendance capacity ({event.max_attendees}).",
                )

        stmt = select(EventAttendee).where(
            EventAttendee.event_id == event_id,
            EventAttendee.persona_id == current_persona.id,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            existing.status = status_enum
        else:
            attendee = EventAttendee(
                event_id=event_id,
                persona_id=current_persona.id,
                status=status_enum,
            )
            db.add(attendee)

        await db.commit()
        return await EventService.get_event_detail(db, current_persona, event_id)

    @staticmethod
    async def withdraw_rsvp(
        db: AsyncSession,
        current_persona: Persona,
        event_id: uuid.UUID,
    ) -> EventResponse:
        """Attendance withdrawal: Removes participant RSVP from event."""
        event = await db.get(Event, event_id)
        if not event or event.is_deleted:
            raise HTTPException(status_code=404, detail="Event not found.")

        await db.execute(
            delete(EventAttendee).where(
                EventAttendee.event_id == event_id,
                EventAttendee.persona_id == current_persona.id,
            )
        )
        await db.commit()

        return await EventService.get_event_detail(db, current_persona, event_id)
