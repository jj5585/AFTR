import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_persona, get_optional_persona
from backend.app.models.persona import Persona
from backend.app.schemas.stories_events import (
    EventCreateRequest,
    EventUpdateRequest,
    EventResponse,
    EventsListResponse,
    EventRSVPRequest,
)
from backend.app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events"])


@router.get(
    "",
    response_model=EventsListResponse,
    summary="List public group events",
)
async def get_events(
    campus: Optional[str] = Query(None, description="Optional campus filter"),
    cursor: Optional[str] = Query(None, description="Keyset cursor"),
    limit: int = Query(20, ge=1, le=50, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_persona: Optional[Persona] = Depends(get_optional_persona),
):
    """List upcoming and active public group events."""
    return await EventService.get_events(
        db=db,
        current_persona=current_persona,
        campus=campus,
        cursor=cursor,
        limit=limit,
    )


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a public group event",
)
async def create_event(
    body: EventCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """
    Create a public group event:
    - Enforces named public venue (strictly NO private home addresses or live GPS)
    - Enforces future date/time
    - Sets organizer as GOING
    """
    return await EventService.create_event(
        db=db,
        current_persona=current_persona,
        data=body,
    )


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Get event details",
)
async def get_event_detail(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_persona: Optional[Persona] = Depends(get_optional_persona),
):
    """Get single event details with organizer status and attendance counters."""
    return await EventService.get_event_detail(
        db=db,
        current_persona=current_persona,
        event_id=event_id,
    )


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
    summary="Update event details (organizer only)",
)
async def update_event(
    event_id: uuid.UUID,
    body: EventUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Organizer controls: Update event title, description, public venue, or time."""
    return await EventService.update_event(
        db=db,
        current_persona=current_persona,
        event_id=event_id,
        data=body,
    )


@router.post(
    "/{event_id}/cancel",
    response_model=EventResponse,
    summary="Cancel event (organizer only)",
)
async def cancel_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Organizer controls: Cancel event."""
    return await EventService.cancel_event(
        db=db,
        current_persona=current_persona,
        event_id=event_id,
    )


@router.post(
    "/{event_id}/rsvp",
    response_model=EventResponse,
    summary="RSVP to event",
)
async def rsvp_event(
    event_id: uuid.UUID,
    body: EventRSVPRequest,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """RSVP to event (enforces attendance capacity)."""
    return await EventService.rsvp_event(
        db=db,
        current_persona=current_persona,
        event_id=event_id,
        status_str=body.status,
    )


@router.delete(
    "/{event_id}/rsvp",
    response_model=EventResponse,
    summary="Withdraw attendance RSVP",
)
async def withdraw_rsvp(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Attendance withdrawal: Remove RSVP from event."""
    return await EventService.withdraw_rsvp(
        db=db,
        current_persona=current_persona,
        event_id=event_id,
    )
