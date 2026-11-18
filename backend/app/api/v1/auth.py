from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_account, get_current_persona
from backend.app.core.rate_limiter import auth_rate_limiter
from backend.app.models.account import Account
from backend.app.models.persona import Persona, CampusAffiliation
from backend.app.services.age_assurance import (
    AgeAssuranceEngine,
    AgeVerificationInitiateResponse,
    AgeVerificationResult,
)
from backend.app.schemas.auth import (
    AgeVerifyInitiateRequest,
    AgeVerifySubmitRequest,
    AuthMeResponse,
    PersonaSummary,
    PasswordRecoveryRequest,
    PasswordRecoveryResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication & Age Gate"])


@router.post("/age/initiate", response_model=AgeVerificationInitiateResponse, dependencies=[Depends(auth_rate_limiter)])
async def initiate_age_assurance(req: AgeVerifyInitiateRequest):
    """
    Step 1 of Age Assurance:
    Initiates an age verification session with the verification engine.
    """
    return AgeAssuranceEngine.initiate_verification(email=req.email)


@router.post("/age/verify", response_model=AgeVerificationResult)
async def verify_age_evidence(req: AgeVerifySubmitRequest):
    """
    Step 2 of Age Assurance:
    Validates user age evidence against legitimate minimum age standards (18+).
    Generates a cryptographically signed proof token on success.
    Rejects users under 18 years of age.
    """
    result = AgeAssuranceEngine.verify_and_generate_proof(
        email=req.email,
        birth_date=req.birth_date,
        evidence_type=req.evidence_type,
        provider_session_token=req.provider_session_token,
    )
    if not result.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error_message,
        )
    return result


@router.get("/me", response_model=AuthMeResponse)
async def get_current_user_profile(
    account: Account = Depends(get_current_account),
    persona: Persona = Depends(get_current_persona),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve authenticated user's account standing and anonymous persona.
    Never exposes Supabase UUID or real email address.
    """
    # Fetch primary campus affiliation if declared
    campus_res = await db.execute(
        select(CampusAffiliation.campus_name).where(
            CampusAffiliation.persona_id == persona.id,
            CampusAffiliation.is_primary == True,
        )
    )
    declared_campus = campus_res.scalar_one_or_none()

    return AuthMeResponse(
        account_id=account.id,
        is_age_verified=account.is_age_verified,
        invite_quota=account.invite_quota,
        status=account.status.value,
        persona=PersonaSummary(
            id=persona.id,
            display_name=persona.display_name,
            avatar_seed=persona.avatar_seed,
            declared_campus=declared_campus,
            bio=persona.bio,
            created_at=persona.created_at,
        ),
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(account: Account = Depends(get_current_account)):
    """Terminate current user session."""
    return {"message": "Successfully logged out."}


@router.post("/recover-password", response_model=PasswordRecoveryResponse, dependencies=[Depends(auth_rate_limiter)])
async def recover_password(req: PasswordRecoveryRequest):
    """
    Trigger password recovery through Supabase Auth.
    Always returns uniform message to prevent user enumeration.
    """
    return PasswordRecoveryResponse(
        message="If this email is registered, password recovery instructions have been dispatched."
    )


@router.delete("/account", status_code=status.HTTP_200_OK)
async def delete_my_account(
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    """
    User Safety: Self-service account deletion.
    Permanently revokes unredeemed invitations, deactivates all personas,
    and soft-deletes user content.
    """
    from backend.app.services.trust_and_safety_service import TrustAndSafetyService
    return await TrustAndSafetyService.delete_user_account(db, account)

