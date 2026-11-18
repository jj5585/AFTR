import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import (
    require_moderator,
    require_security_admin,
    verify_admin_mfa_stepup,
)
from backend.app.models.account import Account
from backend.app.schemas.trust_and_safety import (
    AdminOverviewResponse,
    ReportListResponse,
    ReportAdminItem,
    ReportResolveRequest,
    ModerationQueueResponse,
    ModerationDecisionRequest,
    UserRestrictionRequest,
    ModerationActionResponse,
    AppealListResponse,
    AppealResponse,
    AppealReviewRequest,
    AdminInvitationListResponse,
    AdminAccountListResponse,
    AuditLogListResponse,
    MfaSetupResponse,
    MfaVerifyRequest,
)
from backend.app.services.trust_and_safety_service import TrustAndSafetyService

router = APIRouter(prefix="/admin", tags=["Trust, Safety & Administration"])


# --- 1. Overview ---

@router.get(
    "/overview",
    response_model=AdminOverviewResponse,
    summary="Safety and moderation metrics overview",
)
async def get_safety_overview(
    admin: Account = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate trust, safety, and moderation metrics."""
    return await TrustAndSafetyService.get_overview(db)


# --- 2. Reports ---

@router.get(
    "/reports",
    response_model=ReportListResponse,
    summary="List flagged user reports",
)
async def list_reports(
    status: Optional[str] = Query("PENDING", description="Filter by status: PENDING, REVIEWED, ACTIONED, DISMISSED, ALL"),
    target_type: Optional[str] = Query(None, description="Filter by target: POST, COMMENT, PERSONA, EVENT, STORY, ALL"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: Account = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """List submitted user reports for human review."""
    return await TrustAndSafetyService.list_reports(
        db, status_filter=status, target_type=target_type, limit=limit, offset=offset
    )


@router.post(
    "/reports/{report_id}/resolve",
    response_model=ReportAdminItem,
    summary="Resolve report with action or dismissal",
)
async def resolve_report(
    report_id: uuid.UUID,
    data: ReportResolveRequest,
    admin: Account = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """Resolve report: DISMISS, TAKEDOWN, or ACTION_TAKEN."""
    return await TrustAndSafetyService.resolve_report(
        db, report_id, data.action, data.notes, admin
    )


# --- 3. Content Moderation Review Queue ---

@router.get(
    "/moderation/queue",
    response_model=ModerationQueueResponse,
    summary="Review queue for held or reported content",
)
async def get_moderation_queue(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: Account = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """
    Items with status PENDING_REVIEW held prior to public publication.
    Enforces rule: 'Do not publish content that requires human review before its status has been resolved.'
    """
    return await TrustAndSafetyService.get_moderation_queue(db, limit=limit, offset=offset)


@router.post(
    "/moderation/{target_type}/{target_id}/decision",
    summary="Approve or take down queued content",
)
async def make_moderation_decision(
    target_type: str,
    target_id: uuid.UUID,
    data: ModerationDecisionRequest,
    admin: Account = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """
    Approve or Take Down queued content.
    - APPROVE: transitions status to PUBLISHED, entering public feeds.
    - TAKEDOWN: transitions status to REJECTED, soft-deletes content, and issues moderation action.
    """
    return await TrustAndSafetyService.make_moderation_decision(
        db, target_type, target_id, data.action, data.reason, admin
    )


# --- 4. User Restrictions ---

@router.post(
    "/restrictions",
    response_model=ModerationActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply restriction: WARNING, SHADOWBAN, PERSONA_SUSPENDED, or ACCOUNT_BANNED",
)
async def apply_user_restriction(
    data: UserRestrictionRequest,
    admin: Account = Depends(require_moderator),
    x_admin_mfa: Optional[str] = Header(None, alias="X-Admin-MFA"),
    db: AsyncSession = Depends(get_db),
):
    """
    Apply a disciplinary restriction to a user or persona.
    ACCOUNT_BANNED strictly requires SECURITY_ADMIN role and MFA step-up verification if MFA is enabled.
    """
    if data.action_type.upper() == "ACCOUNT_BANNED":
        if admin.role != "SECURITY_ADMIN":
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security Administrator role required to execute account bans.",
            )
        verify_admin_mfa_stepup(admin, x_admin_mfa)

    return await TrustAndSafetyService.apply_user_restriction(db, data, admin)


# --- 5. Appeals ---

@router.get(
    "/appeals",
    response_model=AppealListResponse,
    summary="List user appeals against moderation actions",
)
async def list_appeals(
    status: Optional[str] = Query("PENDING", description="Filter by status: PENDING, APPROVED, REJECTED, ALL"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: Account = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """List appeals submitted by users."""
    return await TrustAndSafetyService.list_appeals(
        db, status_filter=status, limit=limit, offset=offset
    )


@router.post(
    "/appeals/{appeal_id}/review",
    response_model=AppealResponse,
    summary="Review appeal: APPROVE (overturns action) or REJECT",
)
async def review_appeal(
    appeal_id: uuid.UUID,
    data: AppealReviewRequest,
    admin: Account = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """
    Decide on an appeal:
    - APPROVE: Overturns the penalty and restores content or persona.
    - REJECT: Upholds the penalty.
    """
    return await TrustAndSafetyService.review_appeal(
        db, appeal_id, data.decision, data.resolution_notes, admin
    )


# --- 6. Invitation Management (Security Administrator only) ---

@router.get(
    "/invitations",
    response_model=AdminInvitationListResponse,
    summary="Inspect platform invitations (Security Admin)",
)
async def list_invitations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: Account = Depends(require_security_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Security Administrator view of platform invitations.
    Email hints are cryptographically masked (e.g. d***e@example.com) to prevent surveillance.
    """
    return await TrustAndSafetyService.list_admin_invitations(db, limit=limit, offset=offset)


@router.post(
    "/invitations/{invitation_id}/revoke",
    summary="Revoke invitation (Security Admin)",
)
async def revoke_invitation(
    invitation_id: uuid.UUID,
    admin: Account = Depends(require_security_admin),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an unredeemed invitation for security or abuse prevention."""
    return await TrustAndSafetyService.admin_revoke_invitation(db, invitation_id, admin)


# --- 7. Account Standing (Security Administrator only, Zero Identity Leakage) ---

@router.get(
    "/accounts",
    response_model=AdminAccountListResponse,
    summary="Inspect account standing and compliance (Security Admin)",
)
async def list_accounts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: Account = Depends(require_security_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Security Administrator view of account health and strike counts.
    STRICT ZERO IDENTITY LEAKAGE: Never returns raw emails, email hashes, or Supabase UUIDs.
    """
    return await TrustAndSafetyService.list_admin_accounts(db, limit=limit, offset=offset)


# --- 8. Immutable Audit Logs (Security Administrator only) ---

@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="Inspect immutable security audit journal (Security Admin)",
)
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action keyword"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: Account = Depends(require_security_admin),
    db: AsyncSession = Depends(get_db),
):
    """Query immutable security audit log journal."""
    return await TrustAndSafetyService.list_audit_logs(
        db, action_filter=action, limit=limit, offset=offset
    )


# --- 9. Multi-Factor Authentication (MFA) ---

@router.post(
    "/mfa/setup",
    response_model=MfaSetupResponse,
    summary="Initiate RFC 6238 TOTP MFA setup for administrator",
)
async def setup_mfa(
    admin: Account = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """Generate secret for Google Authenticator / 1Password."""
    return await TrustAndSafetyService.setup_admin_mfa(db, admin)


@router.post(
    "/mfa/verify",
    summary="Verify code and activate MFA for administrator",
)
async def verify_mfa(
    data: MfaVerifyRequest,
    admin: Account = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """Confirm 6-digit TOTP code and enable MFA protection."""
    return await TrustAndSafetyService.verify_and_enable_mfa(db, admin, data.code)
