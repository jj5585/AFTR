import uuid
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict


class PersonaPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str
    avatar_seed: str
    declared_campus: Optional[str] = None
    is_active: bool = True


class PostCreateRequest(BaseModel):
    content: str = Field(..., min_length=5, max_length=2000, description="Confession or discussion text")
    tag: str = Field(default="confessions", max_length=50, description="Category tag")
    post_type: str = Field(default="CONFESSION", description="CONFESSION, DISCUSSION, GENERAL")
    is_sensitive: bool = Field(default=False, description="Flag for sensitive or adult discussion")
    allow_comments: bool = Field(default=True, description="Whether other personas can comment")
    campus_name: Optional[str] = Field(default=None, max_length=120, description="Optional self-declared campus")


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    persona: PersonaPublicResponse
    content: str
    post_type: str
    tag: str
    is_sensitive: bool
    allow_comments: bool
    view_count: int
    campus_name: Optional[str] = None
    upvotes_count: int = 0
    comments_count: int = 0
    reactions: Dict[str, int] = Field(default_factory=lambda: {"upvotes": 0, "flames": 0, "hearts": 0, "insightful": 0})
    user_reaction: Optional[str] = None
    is_own: bool = False
    created_at: datetime


class CommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000, description="Comment text")
    parent_id: Optional[uuid.UUID] = Field(default=None, description="Parent comment ID for threaded replies")


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    post_id: uuid.UUID
    persona: PersonaPublicResponse
    parent_id: Optional[uuid.UUID] = None
    content: str
    is_op: bool = False
    is_own: bool = False
    replies_count: int = 0
    created_at: datetime


class ReactionRequest(BaseModel):
    reaction_type: str = Field(default="UPVOTE", description="UPVOTE, FLAME, HEART, INSIGHTFUL")


class ReactionResponse(BaseModel):
    action: str  # "ADDED", "REMOVED", "UPDATED"
    reaction_type: Optional[str] = None
    reactions_summary: Dict[str, int]


class BlockRequest(BaseModel):
    blocked_persona_id: uuid.UUID
    reason: Optional[str] = Field(default=None, max_length=255)


class BlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    blocker_persona_id: uuid.UUID
    blocked_persona_id: uuid.UUID
    blocked_persona_name: Optional[str] = None
    created_at: datetime


class ReportCreateRequest(BaseModel):
    target_type: str = Field(..., description="POST, COMMENT, PERSONA, EVENT")
    target_id: uuid.UUID
    reason: str = Field(..., min_length=3, max_length=500)


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    status: str
    created_at: datetime
