import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# Overview Metrics
class AdminOverviewResponse(BaseModel):
    pending_reports_count: int
    pending_review_queue_count: int
    pending_appeals_count: int
    total_active_accounts: int
    suspended_personas_count: int
    banned_accounts_count: int
    total_moderation_actions: int
    recent_actions: List[Dict[str, Any]] = []


# Reports
class ReportAdminItem(BaseModel):
    id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    reason: str
    status: str
    reporter_persona_name: Optional[str] = "Anonymous Member"
    reporter_persona_id: uuid.UUID
    resolved_by: Optional[uuid.UUID] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    content_excerpt: Optional[str] = None


class ReportListResponse(BaseModel):
    items: List[ReportAdminItem]
    total: int
    pending_count: int


class ReportResolveRequest(BaseModel):
    action: str = Field(..., description="DISMISS, TAKEDOWN, or ACTION_TAKEN")
    notes: Optional[str] = Field(None, max_length=500)


# Moderation Review Queue
class ModerationQueueItem(BaseModel):
    target_type: str  # "POST", "STORY", "COMMENT"
    target_id: uuid.UUID
    content: str
    category: Optional[str] = None
    campus_name: Optional[str] = None
    moderation_status: str
    author_persona_id: uuid.UUID
    author_persona_name: str
    author_avatar_seed: str
    flagged_reasons: List[str] = []
    reports_count: int = 0
    created_at: datetime


class ModerationQueueResponse(BaseModel):
    items: List[ModerationQueueItem]
    total: int


class ModerationDecisionRequest(BaseModel):
    action: str = Field(..., description="APPROVE or TAKEDOWN")
    reason: Optional[str] = Field(None, description="Explanation for decision")


# User Restrictions
class UserRestrictionRequest(BaseModel):
    target_persona_id: uuid.UUID
    action_type: str = Field(..., description="WARNING, SHADOWBAN, PERSONA_SUSPENDED, or ACCOUNT_BANNED")
    reason: str = Field(..., min_length=5, max_length=500)
    strike_count: int = Field(default=1, ge=1, le=5)


class ModerationActionResponse(BaseModel):
    id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    target_persona_id: Optional[uuid.UUID] = None
    action_type: str
    moderator_id: Optional[uuid.UUID] = None
    reason: str
    strike_count: int
    created_at: datetime


# Appeals
class AppealCreateRequest(BaseModel):
    moderation_action_id: uuid.UUID
    reason: str = Field(..., min_length=10, max_length=1000, description="Appellant statement explaining why action should be overturned")


class AppealResponse(BaseModel):
    id: uuid.UUID
    moderation_action_id: uuid.UUID
    appellant_persona_id: uuid.UUID
    reason: str
    status: str
    reviewed_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    action_details: Optional[Dict[str, Any]] = None


class AppealListResponse(BaseModel):
    items: List[AppealResponse]
    total: int
    pending_count: int


class AppealReviewRequest(BaseModel):
    decision: str = Field(..., description="APPROVE or REJECT")
    resolution_notes: Optional[str] = Field(None, max_length=500)


# Invitation Management for Admins
class AdminInvitationItem(BaseModel):
    id: uuid.UUID
    inviter_persona_name: Optional[str] = None
    recipient_email_masked: str
    status: str
    created_at: datetime
    expires_at: datetime
    redeemed_at: Optional[datetime] = None


class AdminInvitationListResponse(BaseModel):
    items: List[AdminInvitationItem]
    total: int


# Account Standing (No Identity Vault Leakage)
class AdminAccountItem(BaseModel):
    id: uuid.UUID
    status: str
    role: str
    personas_count: int
    persona_display_names: List[str] = []
    invite_quota: int
    is_age_verified: bool
    strike_count: int = 0
    created_at: datetime


class AdminAccountListResponse(BaseModel):
    items: List[AdminAccountItem]
    total: int


# Audit Logs
class AuditLogItem(BaseModel):
    id: uuid.UUID
    actor_type: str
    action: str
    target_type: Optional[str] = None
    target_id: Optional[uuid.UUID] = None
    ip_hash: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: List[AuditLogItem]
    total: int


# MFA
class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_url: str
    instruction: str


class MfaVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


# Block list for user safety
class BlockedPersonaItem(BaseModel):
    persona_id: uuid.UUID
    display_name: str
    avatar_seed: str
    reason: Optional[str] = None
    blocked_at: datetime


# Community Standards
class CommunityStandardRule(BaseModel):
    category: str
    title: str
    description: str
    enforcement: str


class CommunityStandardsResponse(BaseModel):
    version: str
    last_updated: str
    rules: List[CommunityStandardRule]
