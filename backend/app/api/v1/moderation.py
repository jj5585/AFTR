import uuid
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
from backend.app.services.social_service import SocialService

router = APIRouter(tags=["Moderation, Blocks & Reports"])


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
