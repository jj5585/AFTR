import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class MessageCreateRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Private message text (will be encrypted at rest)",
    )


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_persona_id: uuid.UUID
    sender_pseudonym: str
    content: str
    is_mine: bool
    is_deleted: bool = False
    created_at: datetime


class MessagesPageResponse(BaseModel):
    items: List[MessageResponse]
    next_cursor: Optional[str] = None
    has_more: bool = False


class ConversationParticipantPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    persona_id: uuid.UUID
    conversation_pseudonym: str
    display_name: str
    avatar_seed: str
    declared_campus: Optional[str] = None
    is_online: bool = False


class ConversationSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    other_participant: ConversationParticipantPublic
    my_conversation_pseudonym: str
    last_message_preview: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    is_active: bool = True
    is_blocked: bool = False
    created_at: datetime


class ConversationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    participants: List[ConversationParticipantPublic]
    my_conversation_pseudonym: str
    is_active: bool = True
    is_blocked: bool = False
    created_at: datetime


class UnreadCountResponse(BaseModel):
    total_unread_messages: int
    unread_conversations_count: int
