import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class InvitationCreateRequest(BaseModel):
    recipient_email: EmailStr = Field(..., description="Intended recipient's email for cryptographic binding.")


class InvitationResponse(BaseModel):
    id: uuid.UUID
    token: Optional[str] = None
    invite_url: Optional[str] = None
    status: str
    expires_at: datetime
    created_at: datetime
    used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


class InvitationValidateRequest(BaseModel):
    token: str = Field(..., min_length=10, description="Raw invitation token string.")


class InvitationValidateResponse(BaseModel):
    status: str
    is_valid: bool
    expires_at: Optional[datetime] = None
    message: str


class InvitationClaimRequest(BaseModel):
    token: str = Field(..., min_length=10)
    recipient_email: EmailStr = Field(..., description="Email address that must match the invitation binding.")


class InvitationClaimResponse(BaseModel):
    success: bool
    claim_ticket: str
    recipient_email: str
    message: str


class InvitationRedeemRequest(BaseModel):
    claim_ticket: str = Field(..., description="Signed invitation claim ticket obtained from /claim.")
    age_proof_token: str = Field(..., description="Cryptographic proof token from AgeAssuranceEngine verifying 18+.")
    supabase_user_id: uuid.UUID = Field(..., description="Supabase Auth UUID after user signs up.")
    display_name: str = Field(..., min_length=3, max_length=50)
    avatar_seed: str = Field(..., min_length=3, max_length=100)
    declared_campus: Optional[str] = Field(None, max_length=120, description="Optional self-declared campus.")
    bio: Optional[str] = Field(None, max_length=280)
    accepted_policy: bool = Field(..., description="Must accept AFTR adult community policies.")


class InvitationRedeemResponse(BaseModel):
    success: bool
    account_id: uuid.UUID
    persona_id: uuid.UUID
    display_name: str
    avatar_seed: str
    declared_campus: Optional[str] = None
    invite_quota: int
    message: str


class InvitationQuotaResponse(BaseModel):
    total_quota: int = 3
    remaining_quota: int
    issued_count: int
    redeemed_count: int
