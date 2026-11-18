import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import (
    generate_secure_invitation_token,
    hash_token,
    hash_recipient_email,
    create_claim_ticket,
    verify_claim_ticket,
    get_current_account,
)
from backend.app.core.rate_limiter import invitation_rate_limiter
from backend.app.models.account import Account
from backend.app.models.base import ensure_utc
from backend.app.models.persona import Persona, CampusAffiliation
from backend.app.models.invitation import Invitation, InvitationStatus
from backend.app.models.moderation import AuditLog
from backend.app.services.age_assurance import AgeAssuranceEngine
from backend.app.schemas.invitation import (
    InvitationCreateRequest,
    InvitationResponse,
    InvitationValidateRequest,
    InvitationValidateResponse,
    InvitationClaimRequest,
    InvitationClaimResponse,
    InvitationRedeemRequest,
    InvitationRedeemResponse,
    InvitationQuotaResponse,
)

router = APIRouter(prefix="/invitations", tags=["Invitations"])


@router.post("", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    req: InvitationCreateRequest,
    current_account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    """
    Issue a single-use, 72-hour bounded invitation to an intended recipient.
    Strictly enforced quota: Exactly 3 invitations per eligible member.
    """
    if current_account.invite_quota <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation quota exhausted: You have no remaining invitation slots.",
        )

    # Recipient email binding
    recipient_email = req.recipient_email.lower().strip()
    recipient_hash = hash_recipient_email(recipient_email)

    # Prevent inviting oneself
    if recipient_hash == current_account.email_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot issue an invitation to your own registered email address.",
        )

    # Generate high-entropy 32-byte cryptographically secure token
    raw_token = generate_secure_invitation_token()
    token_hashed = hash_token(raw_token)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=settings.INVITATION_EXPIRATION_HOURS)

    # Deduct quota atomically
    current_account.invite_quota -= 1

    invitation = Invitation(
        inviter_account_id=current_account.id,
        token_hash=token_hashed,
        recipient_hash=recipient_hash,
        status=InvitationStatus.PENDING,
        created_at=now,
        expires_at=expires_at,
    )
    db.add(invitation)

    # Security Audit Log
    audit = AuditLog(
        actor_id=current_account.id,
        actor_type="ACCOUNT",
        action="INVITATION_ISSUED",
        target_type="INVITATION",
        details_json=f'{{"recipient_hash": "{recipient_hash[:12]}...", "expires_at": "{expires_at.isoformat()}"}}',
        created_at=now,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(invitation)

    invite_url = f"http://localhost:3000/invite/{raw_token}"

    return InvitationResponse(
        id=invitation.id,
        token=raw_token,
        invite_url=invite_url,
        status=invitation.status.value,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
        used_at=invitation.used_at,
        revoked_at=invitation.revoked_at,
    )


@router.get("", response_model=List[InvitationResponse])
async def list_user_invitations(
    current_account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    """
    List all invitations issued by the current user.
    Plaintext tokens are never stored or returned after creation.
    """
    result = await db.execute(
        select(Invitation)
        .where(Invitation.inviter_account_id == current_account.id)
        .order_by(Invitation.created_at.desc())
    )
    invitations = result.scalars().all()

    # Update any passively expired invitations
    now = datetime.now(timezone.utc)
    for inv in invitations:
        if inv.status == InvitationStatus.PENDING and ensure_utc(inv.expires_at) <= now:
            inv.status = InvitationStatus.EXPIRED

    return [
        InvitationResponse(
            id=inv.id,
            status=inv.status.value,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
            used_at=inv.used_at,
            revoked_at=inv.revoked_at,
        )
        for inv in invitations
    ]


@router.get("/quota", response_model=InvitationQuotaResponse)
async def get_invitation_quota(
    current_account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve invitation quota metrics for the current member."""
    issued_count_res = await db.execute(
        select(func.count(Invitation.id)).where(
            Invitation.inviter_account_id == current_account.id
        )
    )
    issued_count = issued_count_res.scalar() or 0

    redeemed_count_res = await db.execute(
        select(func.count(Invitation.id)).where(
            Invitation.inviter_account_id == current_account.id,
            Invitation.status == InvitationStatus.USED,
        )
    )
    redeemed_count = redeemed_count_res.scalar() or 0

    return InvitationQuotaResponse(
        total_quota=3,
        remaining_quota=current_account.invite_quota,
        issued_count=issued_count,
        redeemed_count=redeemed_count,
    )


@router.post("/validate", response_model=InvitationValidateResponse, dependencies=[Depends(invitation_rate_limiter)])
async def validate_invitation(
    req: InvitationValidateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Public gate validation: Verify token existence and state without revealing recipient PII.
    """
    token_hashed = hash_token(req.token)

    result = await db.execute(
        select(Invitation).where(Invitation.token_hash == token_hashed)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        return InvitationValidateResponse(
            status="NOT_FOUND",
            is_valid=False,
            message="This invitation code was not found. Please check your link.",
        )

    now = datetime.now(timezone.utc)

    if invitation.status == InvitationStatus.USED:
        return InvitationValidateResponse(
            status="ALREADY_REDEEMED",
            is_valid=False,
            expires_at=invitation.expires_at,
            message="This single-use invitation has already been claimed and redeemed.",
        )

    if invitation.status == InvitationStatus.REVOKED:
        return InvitationValidateResponse(
            status="REVOKED",
            is_valid=False,
            expires_at=invitation.expires_at,
            message="This invitation was revoked by the sender.",
        )

    if invitation.status == InvitationStatus.EXPIRED or ensure_utc(invitation.expires_at) <= now:
        if invitation.status != InvitationStatus.EXPIRED:
            invitation.status = InvitationStatus.EXPIRED
            await db.commit()
        return InvitationValidateResponse(
            status="EXPIRED",
            is_valid=False,
            expires_at=invitation.expires_at,
            message="This invitation has expired. Invitations are strictly valid for 72 hours.",
        )

    return InvitationValidateResponse(
        status="VALID",
        is_valid=True,
        expires_at=invitation.expires_at,
        message="Invitation is valid. Please verify your intended email address to continue.",
    )


@router.post("/claim", response_model=InvitationClaimResponse)
async def claim_invitation(
    req: InvitationClaimRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify recipient email binding.
    Issues a short-lived signed claim ticket upon successful match.
    """
    token_hashed = hash_token(req.token)
    recipient_email = req.recipient_email.lower().strip()
    recipient_hash = hash_recipient_email(recipient_email)

    result = await db.execute(
        select(Invitation).where(Invitation.token_hash == token_hashed)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation token not found.",
        )

    now = datetime.now(timezone.utc)

    if invitation.status == InvitationStatus.USED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has already been redeemed.",
        )

    if invitation.status == InvitationStatus.REVOKED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation was revoked by the sender.",
        )

    if invitation.status == InvitationStatus.EXPIRED or ensure_utc(invitation.expires_at) <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has expired (72-hour TTL exceeded).",
        )

    # Recipient Binding Verification
    if invitation.recipient_hash != recipient_hash:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recipient verification failed: This invitation is bound to a different email address.",
        )

    # Issue signed claim ticket (30 min expiry)
    claim_ticket = create_claim_ticket(token_hashed, recipient_email)

    return InvitationClaimResponse(
        success=True,
        claim_ticket=claim_ticket,
        recipient_email=recipient_email,
        message="Recipient email successfully verified. Proceed to age assurance and persona creation.",
    )


@router.post("/redeem", response_model=InvitationRedeemResponse)
async def redeem_invitation(
    req: InvitationRedeemRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Final Onboarding Gateway:
    1. Validates claim ticket & recipient email.
    2. Validates legitimate Age Assurance proof (18+ verified).
    3. Validates community policy acceptance.
    4. Executes atomic invitation redemption.
    5. Initializes Account (quota=3) and anonymous Persona.
    """
    if not req.accepted_policy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the AFTR community rules and adult content policies.",
        )

    # 1. Verify claim ticket
    claim_payload = verify_claim_ticket(req.claim_ticket)
    token_hash = claim_payload["token_hash"]
    email = claim_payload["email"]

    # 2. Verify legitimate Age Assurance proof
    try:
        age_payload = AgeAssuranceEngine.validate_proof_token(
            proof_token=req.age_proof_token,
            expected_email=email,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Age assurance verification failed: {str(e)}",
        )

    birth_year = age_payload.get("birth_year")

    # 3. Check for existing account with this Supabase user ID
    existing_account = (
        await db.execute(
            select(Account).where(Account.supabase_user_id == req.supabase_user_id)
        )
    ).scalar_one_or_none()

    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account is already registered for this user ID.",
        )

    # 4. Atomic Invitation State Transition
    now = datetime.now(timezone.utc)
    invitation_res = await db.execute(
        select(Invitation).where(Invitation.token_hash == token_hash)
    )
    invitation = invitation_res.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation record not found.",
        )

    if invitation.status != InvitationStatus.PENDING or ensure_utc(invitation.expires_at) <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invitation cannot be redeemed: Status is {invitation.status.value}.",
        )

    # 5. Create new Account (Identity Domain)
    new_account = Account(
        supabase_user_id=req.supabase_user_id,
        email_hash=hash_recipient_email(email),
        is_age_verified=True,
        birth_year=birth_year,
        invite_quota=3,  # Initial 3 invitations for each eligible member
    )
    db.add(new_account)
    await db.flush()

    # Transition invitation to USED atomically
    invitation.status = InvitationStatus.USED
    invitation.used_by_account_id = new_account.id
    invitation.used_at = now
    invitation.updated_at = now

    # 6. Create initial anonymous Persona (Social Domain)
    new_persona = Persona(
        account_id=new_account.id,
        display_name=req.display_name.strip(),
        avatar_seed=req.avatar_seed.strip(),
        bio=req.bio.strip() if req.bio else None,
        is_active=True,
    )
    db.add(new_persona)
    await db.flush()

    # 7. Optional self-declared campus affiliation
    if req.declared_campus and req.declared_campus.strip():
        campus = CampusAffiliation(
            persona_id=new_persona.id,
            campus_name=req.declared_campus.strip(),
            is_primary=True,
        )
        db.add(campus)

    # 8. Immutable audit log
    audit = AuditLog(
        actor_id=new_account.id,
        actor_type="ACCOUNT",
        action="INVITATION_REDEEMED_ONBOARDING_COMPLETED",
        target_type="INVITATION",
        target_id=invitation.id,
        details_json=f'{{"persona_id": "{new_persona.id}", "birth_year": {birth_year}}}',
        created_at=now,
    )
    db.add(audit)

    await db.commit()

    return InvitationRedeemResponse(
        success=True,
        account_id=new_account.id,
        persona_id=new_persona.id,
        display_name=new_persona.display_name,
        avatar_seed=new_persona.avatar_seed,
        declared_campus=req.declared_campus.strip() if req.declared_campus else None,
        invite_quota=new_account.invite_quota,
        message="Welcome to AFTR. Your anonymous persona has been established.",
    )


@router.delete("/{invitation_id}", status_code=status.HTTP_200_OK)
async def revoke_invitation(
    invitation_id: uuid.UUID,
    current_account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke an unredeemed invitation issued by the user.
    Once revoked, the invitation can never be claimed or redeemed.
    Per policy, revoked invitations do not replenish quota.
    """
    result = await db.execute(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.inviter_account_id == current_account.id,
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or you are not the issuing member.",
        )

    if invitation.status == InvitationStatus.USED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke an invitation that has already been redeemed.",
        )

    if invitation.status == InvitationStatus.REVOKED:
        return {"message": "Invitation is already revoked."}

    now = datetime.now(timezone.utc)
    invitation.status = InvitationStatus.REVOKED
    invitation.revoked_at = now
    invitation.updated_at = now

    audit = AuditLog(
        actor_id=current_account.id,
        actor_type="ACCOUNT",
        action="INVITATION_REVOKED",
        target_type="INVITATION",
        target_id=invitation.id,
        created_at=now,
    )
    db.add(audit)

    await db.commit()

    return {"message": "Invitation successfully revoked."}
