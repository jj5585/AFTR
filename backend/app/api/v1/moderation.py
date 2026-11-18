import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_persona
from backend.app.models.persona import Persona
from backend.app.schemas.social import (
    BlockRequest,
    BlockResponse,
    ReportCreateRequest,
    ReportResponse,
)
from backend.app.schemas.trust_and_safety import (
    BlockedPersonaItem,
    AppealCreateRequest,
    AppealResponse,
    CommunityStandardsResponse,
    CommunityStandardRule,
)
from backend.app.services.social_service import SocialService
from backend.app.services.trust_and_safety_service import TrustAndSafetyService

router = APIRouter(tags=["Moderation, Blocks & Reports"])


@router.get(
    "/blocks",
    response_model=List[BlockedPersonaItem],
    summary="List caller's blocked personas",
)
async def list_blocked_personas(
    current_persona: Persona = Depends(get_current_persona),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve list of personas blocked by the caller for user safety settings."""
    return await TrustAndSafetyService.list_my_blocks(db, current_persona)


@router.post(
    "/blocks",
    response_model=BlockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Block persona",
)
async def block_persona(
    data: BlockRequest,
    current_persona: Persona = Depends(get_current_persona),
    db: AsyncSession = Depends(get_db),
):
    """
    Universally block an anonymous persona.
    Prevents them from appearing in feeds, sending requests, or commenting.
    Enforces anti-self block rule.
    """
    return await SocialService.block_persona(
        db, current_persona, data.blocked_persona_id, data.reason
    )


@router.delete(
    "/blocks/{persona_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unblock persona",
)
async def unblock_persona(
    persona_id: uuid.UUID,
    current_persona: Persona = Depends(get_current_persona),
    db: AsyncSession = Depends(get_db),
):
    """Remove a persona from the caller's block list."""
    await SocialService.unblock_persona(db, current_persona, persona_id)
    return None


@router.post(
    "/reports",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report content or persona",
)
async def create_report(
    data: ReportCreateRequest,
    current_persona: Persona = Depends(get_current_persona),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a confidential report for human/automated moderation review.
    Zero personal identity is leaked to the reported party.
    """
    return await SocialService.create_report(
        db, current_persona, data.target_type, data.target_id, data.reason
    )


@router.post(
    "/appeals",
    response_model=AppealResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit appeal against moderation action",
)
async def submit_appeal(
    data: AppealCreateRequest,
    current_persona: Persona = Depends(get_current_persona),
    db: AsyncSession = Depends(get_db),
):
    """
    User safety: Submit an appeal explaining why a moderation action should be overturned.
    """
    return await TrustAndSafetyService.create_appeal(
        db, current_persona, data.moderation_action_id, data.reason
    )


@router.get(
    "/appeals/me",
    response_model=List[AppealResponse],
    summary="List caller's submitted appeals",
)
async def list_my_appeals(
    current_persona: Persona = Depends(get_current_persona),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all appeals submitted by the caller with their statuses."""
    return await TrustAndSafetyService.list_my_appeals(db, current_persona)


@router.get(
    "/safety/standards",
    response_model=CommunityStandardsResponse,
    summary="Public community standards & trust rules",
)
async def get_community_standards():
    """Transparent community standards and policy enforcement boundaries."""
    return CommunityStandardsResponse(
        version="2.0",
        last_updated="2026-11-18",
        rules=[
            CommunityStandardRule(
                category="Privacy & Identity",
                title="Zero Doxxing & Anonymity Protection",
                description="Sharing personal contact information, real names, student IDs, phone numbers, email addresses, or dorm room identifiers is strictly prohibited.",
                enforcement="Immediate automated blocking by Privacy Shield, content removal, and potential account termination.",
            ),
            CommunityStandardRule(
                category="Adult Consent",
                title="Mutual Consent-Based Connections",
                description="Private 1-on-1 conversations and messaging require verified bilateral acceptance of a connection request. Unsolicited contact is architecturally impossible.",
                enforcement="Connection requests rejected or withdrawn immediately close potential communication channels.",
            ),
            CommunityStandardRule(
                category="Safety & Well-Being",
                title="Prohibition of Violence, Threats & Harassment",
                description="Targeted harassment, slurs, cyberbullying, lethal threats, weapons, and suicide or self-harm encouragement have zero tolerance on AFTR.",
                enforcement="Content takedown, permanent persona suspension, and immediate account banning.",
            ),
            CommunityStandardRule(
                category="Sexual Safety",
                title="Non-Consensual Imagery & Minor Safety",
                description="All AFTR members must be verified adults (18+). Non-consensual sexual content, revenge porn, voyeuristic imagery, sextortion, and commercial sex solicitation are illegal and strictly banned.",
                enforcement="Immediate permanent ban, content purging, and referral to relevant legal authorities where legally mandated.",
            ),
            CommunityStandardRule(
                category="Platform Integrity",
                title="Commercial Spam & Scam Prohibition",
                description="Cryptocurrency pumps, bot solicitations, cashapp links, telegram handle spamming, and deceptive external redirects are prohibited.",
                enforcement="Automated heuristic filtering and account restrictions.",
            ),
        ],
    )

