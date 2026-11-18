import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_persona, get_optional_persona
from backend.app.models.persona import Persona
from backend.app.schemas.social import (
    PostCreateRequest,
    PostResponse,
    CommentCreateRequest,
    CommentResponse,
    ReactionRequest,
    ReactionResponse,
)
from backend.app.core.pagination import CursorPage
from backend.app.services.social_service import SocialService

router = APIRouter(prefix="/posts", tags=["Social Feed"])


@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create anonymous post",
)
async def create_post(
    data: PostCreateRequest,
    current_persona: Persona = Depends(get_current_persona),
    db: AsyncSession = Depends(get_db),
):
    """
    Publish an anonymous confession or adult discussion.
    Evaluates content through automated ContentModerationEngine before publication.
    Returns no real account identifiers.
    """
    return await SocialService.create_post(db, current_persona, data)


@router.get(
    "",
    response_model=CursorPage[PostResponse],
    summary="Fetch feed with cursor pagination",
)
async def get_feed(
    category: Optional[str] = Query(None, description="Filter by tag/category"),
    campus: Optional[str] = Query(None, description="Filter by self-declared campus"),
    sort: str = Query("latest", description="'latest' or 'trending'"),
    cursor: Optional[str] = Query(None, description="Opaque cursor token"),
    limit: int = Query(20, ge=1, le=50, description="Items per page"),
    current_persona: Optional[Persona] = Depends(get_optional_persona),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch the anonymous feed.
    - Excludes posts from personas blocked by or blocking caller.
    - Supports category and campus filtering.
    - Keys-based cursor pagination.
    """
    items, next_cursor, has_more = await SocialService.get_feed(
        db=db,
        current_persona=current_persona,
        category=category,
        campus=campus,
        sort=sort,
        cursor=cursor,
        limit=limit,
    )
    return CursorPage(items=items, next_cursor=next_cursor, has_more=has_more)


@router.get(
    "/me",
    response_model=CursorPage[PostResponse],
    summary="View own posts privately",
)
async def get_my_posts(
    cursor: Optional[str] = Query(None, description="Opaque cursor token"),
    limit: int = Query(20, ge=1, le=50),
    current_persona: Persona = Depends(get_current_persona),
    db: AsyncSession = Depends(get_db),
):
    """View caller's own authored posts privately."""
    items, next_cursor, has_more = await SocialService.get_my_posts(
        db=db,
        current_persona=current_persona,
        cursor=cursor,
        limit=limit,
    )
    return CursorPage(items=items, next_cursor=next_cursor, has_more=has_more)


@router.get(
    "/{id}",
    response_model=PostResponse,
    summary="Get post by ID",
)
async def get_post(
    id: uuid.UUID,
    current_persona: Optional[Persona] = Depends(get_optional_persona),
    db: AsyncSession = Depends(get_db),
):
    """Fetch single post by ID and increment view count."""
    return await SocialService.get_post_by_id(db, id, current_persona)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete own post",
)
async def delete_post(
    id: uuid.UUID,
    current_persona: Persona = Depends(get_current_persona),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete post.
    Enforces that only the author persona can delete their own post.
    """
    await SocialService.delete_post(db, id, current_persona)
    return None


@router.post(
    "/{id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment to post",
)
async def add_comment(
    id: uuid.UUID,
    data: CommentCreateRequest,
    current_persona: Persona = Depends(get_current_persona),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a comment to an anonymous post.
    Fails if the author has disabled comments on this post or if blocked.
    """
    return await SocialService.add_comment(db, id, current_persona, data)


@router.get(
    "/{id}/comments",
    response_model=CursorPage[CommentResponse],
    summary="Get comments for a post",
)
async def get_comments(
    id: uuid.UUID,
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    limit: int = Query(50, ge=1, le=100),
    current_persona: Optional[Persona] = Depends(get_optional_persona),
    db: AsyncSession = Depends(get_db),
):
    """Fetch threaded comments for a post, excluding comments from blocked personas."""
    items, next_cursor, has_more = await SocialService.get_comments(
        db, id, current_persona, cursor, limit
    )
    return CursorPage(items=items, next_cursor=next_cursor, has_more=has_more)


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete own comment",
)
async def delete_comment(
    comment_id: uuid.UUID,
    current_persona: Persona = Depends(get_current_persona),
    db: AsyncSession = Depends(get_db),
):
    """Delete comment. Enforces author ownership."""
    await SocialService.delete_comment(db, comment_id, current_persona)
    return None


@router.post(
    "/{id}/reactions",
    response_model=ReactionResponse,
    summary="React to post",
)
async def react_to_post(
    id: uuid.UUID,
    data: ReactionRequest,
    current_persona: Persona = Depends(get_current_persona),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle or update anonymous reaction to post.
    Supported types: UPVOTE, FLAME, HEART, INSIGHTFUL.
    """
    return await SocialService.react_to_post(db, id, current_persona, data.reaction_type)
