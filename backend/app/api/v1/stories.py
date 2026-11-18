import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_persona, get_optional_persona
from backend.app.models.persona import Persona
from backend.app.schemas.stories_events import (
    StoryCreateRequest,
    StoryResponse,
    StoriesFeedResponse,
    StoryCommentCreateRequest,
    StoryCommentResponse,
)
from backend.app.services.story_service import StoryService

router = APIRouter(prefix="/stories", tags=["Stories"])


@router.get(
    "",
    response_model=StoriesFeedResponse,
    summary="List active 24h stories",
)
async def get_stories(
    category: Optional[str] = Query(None, description="Category filter"),
    campus: Optional[str] = Query(None, description="Campus filter"),
    cursor: Optional[str] = Query(None, description="Keyset cursor"),
    limit: int = Query(20, ge=1, le=50, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_persona: Optional[Persona] = Depends(get_optional_persona),
):
    """Retrieve 24-hour active ephemeral stories board."""
    return await StoryService.get_stories_feed(
        db=db,
        current_persona=current_persona,
        category=category,
        campus=campus,
        cursor=cursor,
        limit=limit,
    )


@router.post(
    "",
    response_model=StoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish an anonymous story",
)
async def create_story(
    body: StoryCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Publish a 24h anonymous story with optional comments and campus visibility."""
    return await StoryService.create_story(
        db=db,
        current_persona=current_persona,
        data=body,
    )


@router.post(
    "/{story_id}/reactions",
    summary="React to an anonymous story",
)
async def react_to_story(
    story_id: uuid.UUID,
    reaction_type: str = Query("UPVOTE", description="Reaction type"),
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Toggle an anonymous reaction on a story."""
    return await StoryService.react_to_story(
        db=db,
        current_persona=current_persona,
        story_id=story_id,
        reaction_type=reaction_type,
    )


@router.get(
    "/{story_id}/comments",
    response_model=List[StoryCommentResponse],
    summary="List story comments",
)
async def get_story_comments(
    story_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_persona: Optional[Persona] = Depends(get_optional_persona),
):
    """List comments on an active story."""
    return await StoryService.get_story_comments(
        db=db,
        current_persona=current_persona,
        story_id=story_id,
    )


@router.post(
    "/{story_id}/comments",
    response_model=StoryCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment to story",
)
async def add_story_comment(
    story_id: uuid.UUID,
    body: StoryCommentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Add an anonymous comment to a story (if comments are enabled by author)."""
    return await StoryService.add_story_comment(
        db=db,
        current_persona=current_persona,
        story_id=story_id,
        content=body.content,
    )


@router.delete(
    "/{story_id}",
    summary="Delete own story",
)
async def delete_story(
    story_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Author-only deletion of an active story."""
    return await StoryService.delete_story(
        db=db,
        current_persona=current_persona,
        story_id=story_id,
    )
