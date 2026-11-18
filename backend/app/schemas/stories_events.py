import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from backend.app.schemas.social import PersonaPublicResponse


# ==========================================
# Story Schemas
# ==========================================

class StoryCreateRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=3,
        max_length=1500,
        description="24h ephemeral story text",
    )
    category: str = Field(
        default="night-thoughts",
        max_length=50,
        description="Category: night-thoughts, campus-life, confessions, dating, creative",
    )
    allow_comments: bool = Field(default=True, description="Allow other personas to leave comments")
    visibility: str = Field(default="PUBLIC", description="PUBLIC or CAMPUS")
    campus_name: Optional[str] = Field(None, max_length=120, description="Optional declared campus")


class StoryCommentCreateRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Story comment text",
    )


class StoryCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    story_id: uuid.UUID
    persona: PersonaPublicResponse
    content: str
    is_own: bool = False
    created_at: datetime


class StoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    persona: PersonaPublicResponse
    content: str
    category: str
    allow_comments: bool
    visibility: str
    campus_name: Optional[str] = None
    reactions_count: int = 0
    user_has_reacted: bool = False
    comments_count: int = 0
    is_own: bool = False
    expires_at: datetime
    created_at: datetime


class StoriesFeedResponse(BaseModel):
    items: List[StoryResponse]
    next_cursor: Optional[str] = None
    has_more: bool = False


# ==========================================
# Event Schemas
# ==========================================

class EventCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=100, description="Event title")
    description: str = Field(..., min_length=10, max_length=3000, description="Event description")
    location_name: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Named public venue, strictly NO private home addresses or live GPS coordinates",
    )
    event_time: datetime = Field(..., description="Date and time of event (must be in the future)")
    max_attendees: Optional[int] = Field(
        None, ge=2, le=500, description="Maximum attendance capacity (optional)"
    )
    campus_name: Optional[str] = Field(None, max_length=120, description="Optional self-declared campus")


class EventUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=3000)
    location_name: Optional[str] = Field(None, min_length=3, max_length=150)
    event_time: Optional[datetime] = None
    max_attendees: Optional[int] = Field(None, ge=2, le=500)


class EventRSVPRequest(BaseModel):
    status: str = Field(default="GOING", description="GOING, INTERESTED, or DECLINED")


class EventAttendeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    persona: PersonaPublicResponse
    status: str
    created_at: datetime


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    creator_persona: PersonaPublicResponse
    title: str
    description: str
    location_name: str
    event_time: datetime
    campus_name: Optional[str] = None
    max_attendees: Optional[int] = None
    attendees_count: int = 0
    interested_count: int = 0
    user_rsvp_status: Optional[str] = None
    is_cancelled: bool = False
    is_organizer: bool = False
    created_at: datetime


class EventsListResponse(BaseModel):
    items: List[EventResponse]
    next_cursor: Optional[str] = None
    has_more: bool = False
