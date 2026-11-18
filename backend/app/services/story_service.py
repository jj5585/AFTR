import re
import uuid
from datetime import timedelta
from typing import Optional, List, Set, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy import select, or_, and_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.persona import Persona, CampusAffiliation
from backend.app.models.social import Story, StoryComment, Reaction
from backend.app.models.base import utc_now, ensure_utc
from backend.app.core.pagination import encode_cursor, decode_cursor
from backend.app.schemas.social import PersonaPublicResponse
from backend.app.schemas.stories_events import (
    StoryCreateRequest,
    StoryResponse,
    StoriesFeedResponse,
    StoryCommentCreateRequest,
    StoryCommentResponse,
)
from backend.app.services.moderation_engine import ContentModerationEngine
from backend.app.services.social_service import SocialService


class StoryService:
    @staticmethod
    async def get_declared_campus(db: AsyncSession, persona_id: uuid.UUID) -> Optional[str]:
        """Fetch primary declared campus for a persona."""
        stmt = (
            select(CampusAffiliation.campus_name)
            .where(CampusAffiliation.persona_id == persona_id)
            .order_by(CampusAffiliation.is_primary.desc())
            .limit(1)
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def create_story(
        db: AsyncSession,
        current_persona: Persona,
        data: StoryCreateRequest,
    ) -> StoryResponse:
        """
        Create a 24-hour ephemeral anonymous story.
        Runs content moderation checks before persistence.
        """
        # Pre-publication moderation check
        mod_result = ContentModerationEngine.evaluate_text(data.content)
        if not mod_result.is_allowed:
            flag_str = ", ".join(mod_result.flagged_reasons) or mod_result.rejection_message or "Policy violation"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Story content flagged by Privacy Shield: {flag_str}. Real identities, contact info, and severe policy violations are not permitted.",
            )

        now = utc_now()
        expires = now + timedelta(hours=24)

        campus = data.campus_name
        if not campus and data.visibility == "CAMPUS":
            campus = await StoryService.get_declared_campus(db, current_persona.id)

        story = Story(
            persona_id=current_persona.id,
            content=data.content,
            category=data.category.lower(),
            allow_comments=data.allow_comments,
            visibility=data.visibility.upper(),
            campus_name=campus,
            moderation_status="APPROVED",
            is_deleted=False,
            expires_at=expires,
        )
        db.add(story)
        await db.commit()
        await db.refresh(story)

        author_campus = await StoryService.get_declared_campus(db, current_persona.id)

        return StoryResponse(
            id=story.id,
            persona=PersonaPublicResponse(
                id=current_persona.id,
                display_name=current_persona.display_name,
                avatar_seed=current_persona.avatar_seed,
                declared_campus=author_campus,
                is_active=current_persona.is_active,
            ),
            content=story.content,
            category=story.category,
            allow_comments=story.allow_comments,
            visibility=story.visibility,
            campus_name=story.campus_name,
            reactions_count=0,
            user_has_reacted=False,
            comments_count=0,
            is_own=True,
            expires_at=story.expires_at,
            created_at=story.created_at,
        )

    @staticmethod
    async def get_stories_feed(
        db: AsyncSession,
        current_persona: Optional[Persona] = None,
        category: Optional[str] = None,
        campus: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> StoriesFeedResponse:
        """
        List active, non-expired, non-deleted stories.
        Enforces bilateral blocking and optional campus/category filtering.
        """
        now = utc_now()
        current_persona_id = current_persona.id if current_persona else None
        blocked_ids: Set[uuid.UUID] = await SocialService.get_blocked_persona_ids(db, current_persona_id)

        conditions = [
            Story.is_deleted == False,
            Story.expires_at > now,
            Story.moderation_status == "APPROVED",
        ]

        if blocked_ids:
            conditions.append(Story.persona_id.not_in(blocked_ids))

        if category and category.lower() != "all":
            conditions.append(Story.category == category.lower())

        if campus and campus.lower() != "all":
            conditions.append(
                or_(
                    Story.visibility == "PUBLIC",
                    and_(
                        Story.visibility == "CAMPUS",
                        Story.campus_name.ilike(f"%{campus}%"),
                    ),
                )
            )

        if cursor:
            cursor_data = decode_cursor(cursor)
            if cursor_data:
                dt, item_id = cursor_data
                conditions.append(
                    or_(
                        Story.created_at < dt,
                        and_(Story.created_at == dt, Story.id < item_id),
                    )
                )

        stmt = (
            select(Story)
            .options(selectinload(Story.persona))
            .where(*conditions)
            .order_by(Story.created_at.desc(), Story.id.desc())
            .limit(limit + 1)
        )
        stories = list((await db.execute(stmt)).scalars().all())

        has_more = len(stories) > limit
        if has_more:
            stories = stories[:limit]

        story_ids = [s.id for s in stories]

        # Aggregate reaction counts
        reactions_map: Dict[uuid.UUID, int] = {}
        user_reactions_set: Set[uuid.UUID] = set()

        if story_ids:
            react_stmt = (
                select(Reaction.target_id, func.count(Reaction.id))
                .where(Reaction.target_type == "STORY", Reaction.target_id.in_(story_ids))
                .group_by(Reaction.target_id)
            )
            for tid, count in (await db.execute(react_stmt)).all():
                reactions_map[tid] = count

            if current_persona_id:
                user_react_stmt = select(Reaction.target_id).where(
                    Reaction.target_type == "STORY",
                    Reaction.target_id.in_(story_ids),
                    Reaction.persona_id == current_persona_id,
                )
                user_reactions_set = set((await db.execute(user_react_stmt)).scalars().all())

        # Aggregate comment counts
        comments_map: Dict[uuid.UUID, int] = {}
        if story_ids:
            comm_stmt = (
                select(StoryComment.story_id, func.count(StoryComment.id))
                .where(StoryComment.story_id.in_(story_ids), StoryComment.is_deleted == False)
                .group_by(StoryComment.story_id)
            )
            for sid, count in (await db.execute(comm_stmt)).all():
                comments_map[sid] = count

        items: List[StoryResponse] = []
        for s in stories:
            author = s.persona
            author_campus = await StoryService.get_declared_campus(db, author.id) if author else None

            items.append(
                StoryResponse(
                    id=s.id,
                    persona=PersonaPublicResponse(
                        id=author.id if author else s.persona_id,
                        display_name=author.display_name if author else "Anonymous",
                        avatar_seed=author.avatar_seed if author else "seed",
                        declared_campus=author_campus,
                        is_active=author.is_active if author else False,
                    ),
                    content=s.content,
                    category=s.category,
                    allow_comments=s.allow_comments,
                    visibility=s.visibility,
                    campus_name=s.campus_name,
                    reactions_count=reactions_map.get(s.id, 0),
                    user_has_reacted=(s.id in user_reactions_set),
                    comments_count=comments_map.get(s.id, 0),
                    is_own=(current_persona_id == s.persona_id),
                    expires_at=s.expires_at,
                    created_at=s.created_at,
                )
            )

        next_cursor = None
        if has_more and stories:
            last = stories[-1]
            next_cursor = encode_cursor(last.created_at, last.id)

        return StoriesFeedResponse(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    @staticmethod
    async def react_to_story(
        db: AsyncSession,
        current_persona: Persona,
        story_id: uuid.UUID,
        reaction_type: str = "UPVOTE",
    ) -> Dict[str, Any]:
        """Toggle an anonymous reaction on a story."""
        story = await db.get(Story, story_id)
        if not story or story.is_deleted or ensure_utc(story.expires_at) <= utc_now():
            raise HTTPException(status_code=404, detail="Story not found or expired.")

        stmt = select(Reaction).where(
            Reaction.persona_id == current_persona.id,
            Reaction.target_type == "STORY",
            Reaction.target_id == story_id,
            Reaction.reaction_type == reaction_type,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            await db.delete(existing)
            await db.commit()
            action = "REMOVED"
        else:
            rx = Reaction(
                persona_id=current_persona.id,
                target_type="STORY",
                target_id=story_id,
                reaction_type=reaction_type,
            )
            db.add(rx)
            await db.commit()
            action = "ADDED"

        # Count total reactions
        cnt_stmt = select(func.count(Reaction.id)).where(
            Reaction.target_type == "STORY", Reaction.target_id == story_id
        )
        total = (await db.execute(cnt_stmt)).scalar() or 0

        return {"action": action, "reactions_count": total, "story_id": str(story_id)}

    @staticmethod
    async def add_story_comment(
        db: AsyncSession,
        current_persona: Persona,
        story_id: uuid.UUID,
        content: str,
    ) -> StoryCommentResponse:
        """Add an optional comment to an active story."""
        story = await db.get(Story, story_id)
        if not story or story.is_deleted or ensure_utc(story.expires_at) <= utc_now():
            raise HTTPException(status_code=404, detail="Story not found or expired.")

        if not story.allow_comments:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Comments are disabled by the author for this story.",
            )

        mod_result = ContentModerationEngine.evaluate_text(content)
        if not mod_result.is_allowed:
            flag_str = ", ".join(mod_result.flagged_reasons) or mod_result.rejection_message or "Policy violation"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Comment flagged by Privacy Shield: {flag_str}.",
            )

        comment = StoryComment(
            story_id=story_id,
            persona_id=current_persona.id,
            content=content,
            is_deleted=False,
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)

        author_campus = await StoryService.get_declared_campus(db, current_persona.id)

        return StoryCommentResponse(
            id=comment.id,
            story_id=comment.story_id,
            persona=PersonaPublicResponse(
                id=current_persona.id,
                display_name=current_persona.display_name,
                avatar_seed=current_persona.avatar_seed,
                declared_campus=author_campus,
                is_active=current_persona.is_active,
            ),
            content=comment.content,
            is_own=True,
            created_at=comment.created_at,
        )

    @staticmethod
    async def get_story_comments(
        db: AsyncSession,
        current_persona: Optional[Persona],
        story_id: uuid.UUID,
    ) -> List[StoryCommentResponse]:
        """Fetch comments for an active story."""
        story = await db.get(Story, story_id)
        if not story or story.is_deleted or ensure_utc(story.expires_at) <= utc_now():
            raise HTTPException(status_code=404, detail="Story not found or expired.")

        curr_id = current_persona.id if current_persona else None
        blocked_ids = await SocialService.get_blocked_persona_ids(db, curr_id)

        stmt = (
            select(StoryComment)
            .options(selectinload(StoryComment.persona))
            .where(
                StoryComment.story_id == story_id,
                StoryComment.is_deleted == False,
                StoryComment.persona_id.not_in(blocked_ids) if blocked_ids else True,
            )
            .order_by(StoryComment.created_at.asc())
        )
        comments = list((await db.execute(stmt)).scalars().all())

        results: List[StoryCommentResponse] = []
        for c in comments:
            p = c.persona
            campus = await StoryService.get_declared_campus(db, p.id) if p else None
            results.append(
                StoryCommentResponse(
                    id=c.id,
                    story_id=c.story_id,
                    persona=PersonaPublicResponse(
                        id=p.id if p else c.persona_id,
                        display_name=p.display_name if p else "Anonymous",
                        avatar_seed=p.avatar_seed if p else "seed",
                        declared_campus=campus,
                        is_active=p.is_active if p else False,
                    ),
                    content=c.content,
                    is_own=(curr_id == c.persona_id),
                    created_at=c.created_at,
                )
            )
        return results

    @staticmethod
    async def delete_story(
        db: AsyncSession,
        current_persona: Persona,
        story_id: uuid.UUID,
    ) -> Dict[str, str]:
        """Author-only story deletion."""
        story = await db.get(Story, story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found.")

        if story.persona_id != current_persona.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own stories.",
            )

        story.is_deleted = True
        await db.commit()
        return {"status": "DELETED", "story_id": str(story_id)}
