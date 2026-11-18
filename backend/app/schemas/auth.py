import uuid
from datetime import date, datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field


class AgeVerifyInitiateRequest(BaseModel):
    email: EmailStr


class AgeVerifySubmitRequest(BaseModel):
    email: EmailStr
    birth_date: date
    evidence_type: str = "GOVERNMENT_ID_VERIFICATION"
    provider_session_token: Optional[str] = None


class PersonaSummary(BaseModel):
    id: uuid.UUID
    display_name: str
    avatar_seed: str
    declared_campus: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime


class AuthMeResponse(BaseModel):
    account_id: uuid.UUID
    is_age_verified: bool
    invite_quota: int
    status: str
    persona: Optional[PersonaSummary] = None


class PasswordRecoveryRequest(BaseModel):
    email: EmailStr


class PasswordRecoveryResponse(BaseModel):
    message: str
