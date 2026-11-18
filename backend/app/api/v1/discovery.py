import uuid
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_persona
from backend.app.models.persona import Persona
from backend.app.schemas.discovery import (
    InterestListResponse,
    DiscoveryPreferencesUpdateRequest,
    DiscoveryPreferencesResponse,
    DiscoveryFeedResponse,
    ConnectionRequestCreate,
    ConnectionRequestResponse,
    ConnectionRequestsListResponse,
    MatchResponse,
    MatchesListResponse,
)
from backend.app.services.discovery_service import DiscoveryService

discovery_router = APIRouter(prefix="/discovery", tags=["Discovery"])
connections_router = APIRouter(prefix="/connections", tags=["Connections"])


# ==========================================
# Discovery Endpoints
# ==========================================

@discovery_router.get(
    "/interests",
    response_model=InterestListResponse,
    summary="Get campus interest taxonomy",
)
async def get_interests(
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Retrieve all available adult campus interest tags."""
    interests = await DiscoveryService.get_or_seed_interests(db)
    return InterestListResponse(interests=interests)


@discovery_router.get(
    "/preferences",
    response_model=DiscoveryPreferencesResponse,
    summary="Get own discovery preferences",
)
async def get_my_preferences(
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Retrieve caller's discovery settings, intentions, and selected interests."""
    return await DiscoveryService.get_my_preferences(db, current_persona)


@discovery_router.put(
    "/preferences",
    response_model=DiscoveryPreferencesResponse,
    summary="Update own discovery preferences",
)
async def update_my_preferences(
    body: DiscoveryPreferencesUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Update caller's opt-in status, relationship intentions, age preferences, and interests."""
    return await DiscoveryService.update_preferences(db, current_persona, body)


@discovery_router.get(
    "/feed",
    response_model=DiscoveryFeedResponse,
    summary="Get anonymous discovery cards",
)
async def get_discovery_feed(
    cursor: Optional[str] = Query(None, description="Cursor for keyset pagination"),
    limit: int = Query(15, ge=1, le=50, description="Items per page"),
    campus: Optional[str] = Query(None, description="Filter by self-declared campus"),
    intention: Optional[str] = Query(None, description="Filter by relationship intention"),
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """
    Fetch anonymous discovery cards matching preferences and filters.
    Requires caller to be discoverable. Enforces bilateral block isolation and zero identity leakage.
    """
    return await DiscoveryService.get_discovery_feed(
        db=db,
        current_persona=current_persona,
        cursor=cursor,
        limit=limit,
        campus_filter=campus,
        intention_filter=intention,
    )


# ==========================================
# Connection Endpoints
# ==========================================

@connections_router.post(
    "/request",
    response_model=ConnectionRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send anonymous connection request",
)
async def send_connection_request(
    body: ConnectionRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Send an anonymous connection request with optional polite intro note."""
    return await DiscoveryService.send_connection_request(
        db=db,
        current_persona=current_persona,
        recipient_persona_id=body.recipient_persona_id,
        note=body.note,
    )


@connections_router.get(
    "/requests",
    response_model=ConnectionRequestsListResponse,
    summary="List pending connection requests",
)
async def list_connection_requests(
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """List incoming and outgoing pending connection requests."""
    return await DiscoveryService.get_connection_requests(db, current_persona)


@connections_router.post(
    "/requests/{request_id}/accept",
    response_model=Dict[str, Any],
    summary="Accept incoming connection request",
)
async def accept_connection_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """
    Accept an incoming connection request.
    Marks request as ACCEPTED, creates a Match, and unlocks a private Conversation.
    """
    req_res, match_res = await DiscoveryService.accept_connection_request(
        db=db,
        current_persona=current_persona,
        request_id=request_id,
    )
    return {
        "request": req_res.model_dump(),
        "match": match_res.model_dump(),
    }


@connections_router.post(
    "/requests/{request_id}/reject",
    response_model=ConnectionRequestResponse,
    summary="Reject incoming connection request",
)
async def reject_connection_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Reject an incoming connection request."""
    return await DiscoveryService.reject_connection_request(
        db=db,
        current_persona=current_persona,
        request_id=request_id,
    )


@connections_router.post(
    "/requests/{request_id}/withdraw",
    response_model=ConnectionRequestResponse,
    summary="Withdraw outgoing connection request",
)
async def withdraw_connection_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Withdraw an outgoing pending connection request."""
    return await DiscoveryService.withdraw_connection_request(
        db=db,
        current_persona=current_persona,
        request_id=request_id,
    )


@connections_router.get(
    "/matches",
    response_model=MatchesListResponse,
    summary="List mutual matches",
)
async def list_matches(
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """List all mutual accepted matches for the caller."""
    return await DiscoveryService.get_matches(db, current_persona)
