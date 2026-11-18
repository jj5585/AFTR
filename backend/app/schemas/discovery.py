import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from backend.app.schemas.social import PersonaPublicResponse


class InterestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    is_adult: bool = True


class InterestListResponse(BaseModel):
    interests: List[InterestResponse]


class DiscoveryPreferencesUpdateRequest(BaseModel):
    is_discoverable: Optional[bool] = None
    relationship_intention: Optional[str] = Field(None, max_length=50)
    min_age_preference: Optional[int] = Field(None, ge=18, le=100)
    max_age_preference: Optional[int] = Field(None, ge=18, le=100)
    dating_preferences: Optional[Dict[str, Any]] = None
    interest_ids: Optional[List[uuid.UUID]] = None


class DiscoveryPreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_discoverable: bool
    relationship_intention: Optional[str] = None
    min_age_preference: int = 18
    max_age_preference: int = 99
    dating_preferences: Optional[Dict[str, Any]] = None
    interests: List[InterestResponse] = []


class DiscoveryCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    persona: PersonaPublicResponse
    compatibility_score: float
    mutual_interests: List[str] = []
    relationship_intention: Optional[str] = None
    connection_status: str = "NONE"  # NONE, PENDING_SENT, PENDING_RECEIVED, ACCEPTED, REJECTED, WITHDRAWN
    connection_request_id: Optional[uuid.UUID] = None


class DiscoveryFeedResponse(BaseModel):
    items: List[DiscoveryCardResponse]
    next_cursor: Optional[str] = None
    has_more: bool = False


class ConnectionRequestCreate(BaseModel):
    recipient_persona_id: uuid.UUID
    note: Optional[str] = Field(None, max_length=255)


class ConnectionRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender_persona: PersonaPublicResponse
    recipient_persona: PersonaPublicResponse
    note: Optional[str] = None
    status: str
    created_at: datetime


class ConnectionRequestsListResponse(BaseModel):
    incoming: List[ConnectionRequestResponse]
    outgoing: List[ConnectionRequestResponse]


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    matched_persona: PersonaPublicResponse
    compatibility_score: float
    conversation_id: Optional[uuid.UUID] = None
    created_at: datetime


class MatchesListResponse(BaseModel):
    matches: List[MatchResponse]
