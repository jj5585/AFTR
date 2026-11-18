import uuid
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Set
from fastapi import HTTPException, status
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.base import ensure_utc, utc_now
from backend.app.models.social import Post, Comment, Reaction, PostType
from backend.app.models.persona import Persona, CampusAffiliation
from backend.app.models.moderation import Block, Report, ReportStatus, AuditLog
from backend.app.schemas.social import (
    PostCreateRequest,
    PostResponse,
    PersonaPublicResponse,
    CommentCreateRequest,
    CommentResponse,
    ReactionResponse,
    BlockResponse,
    ReportResponse,
)
from backend.app.core.pagination import encode_cursor, decode_cursor
from backend.app.services.moderation_engine import ContentModerationEngine


class SocialService:
    @staticmethod
    async def get_blocked_persona_ids(
        db: AsyncSession, persona_id: Optional[uuid.UUID]
    ) -> Set[uuid.UUID]:
        """Return all persona IDs that are either blocked by or have blocked the given persona."""
        if not persona_id:
            return set()

        # Query blocks in both directions for complete bilateral isolation
        stmt = select(Block.blocker_persona_id, Block.blocked_persona_id).where(
            or_(
                Block.blocker_persona_id == persona_id,
                Block.blocked_persona_id == persona_id,
            )
        )
        result = await db.execute(stmt)
        blocked_ids: Set[uuid.UUID] = set()
        for blocker, blocked in result.all():
            if blocker == persona_id:
                blocked_ids.add(blocked)
            else:
                blocked_ids.add(blocker)
        return blocked_ids

    @staticmethod
    async def create_post(
        db: AsyncSession,
        current_persona: Persona,
        data: PostCreateRequest,
    ) -> PostResponse:
        """Create a new anonymous post after evaluating content through the moderation engine."""
        # 1. Content Moderation evaluation
        eval_result = ContentModerationEngine.evaluate_text(data.content)
        if not eval_result.is_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=eval_result.rejection_message or "Content violates community standards.",
            )

        # 2. Resolve post type
        try:
            post_type_enum = PostType[data.post_type.upper()]
        except KeyError:
            post_type_enum = PostType.CONFESSION

        # 3. Resolve optional campus affiliation
        campus = data.campus_name
        if not campus:
            aff_stmt = select(CampusAffiliation).where(
                and_(
                    CampusAffiliation.persona_id == current_persona.id,
                    CampusAffiliation.is_primary == True,
                )
            )
            aff_res = await db.execute(aff_stmt)
            primary_aff = aff_res.scalar_one_or_none()
            if primary_aff:
                campus = primary_aff.campus_name

        # 4. Create and persist post
        post = Post(
            persona_id=current_persona.id,
            content=data.content.strip(),
            post_type=post_type_enum,
            tag=data.tag.lower().strip(),
            is_sensitive=data.is_sensitive,
            allow_comments=data.allow_comments,
            moderation_status=eval_result.status,
            campus_name=campus,
            view_count=0,
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)

        return PostResponse(
            id=post.id,
            persona=PersonaPublicResponse(
                id=current_persona.id,
                display_name=current_persona.display_name,
                avatar_seed=current_persona.avatar_seed,
                declared_campus=post.campus_name,
                is_active=current_persona.is_active,
            ),
            content=post.content,
            post_type=post.post_type.value,
            tag=post.tag,
            is_sensitive=post.is_sensitive,
            allow_comments=post.allow_comments,
            view_count=post.view_count,
            campus_name=post.campus_name,
            upvotes_count=0,
            comments_count=0,
            reactions={"upvotes": 0, "flames": 0, "hearts": 0, "insightful": 0},
            user_reaction=None,
            is_own=True,
            created_at=ensure_utc(post.created_at),
        )

    @staticmethod
    async def get_feed(
        db: AsyncSession,
        current_persona: Optional[Persona],
        category: Optional[str] = None,
        campus: Optional[str] = None,
        sort: str = "latest",
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> Tuple[List[PostResponse], Optional[str], bool]:
        """Fetch paginated feed with cursor pagination, category/campus filtering, and bilateral block isolation."""
        limit = max(1, min(limit, 50))
        blocked_ids = await SocialService.get_blocked_persona_ids(
            db, current_persona.id if current_persona else None
        )

        # Base conditions: un-deleted and published
        conditions = [
            Post.is_deleted == False,
            Post.moderation_status == "PUBLISHED",
        ]

        if blocked_ids:
            conditions.append(Post.persona_id.not_in(blocked_ids))

        if category and category.lower() != "all":
            conditions.append(Post.tag == category.lower().strip())

        if campus and campus.strip():
            conditions.append(Post.campus_name == campus.strip())

        # Cursor condition for keyset pagination
        if cursor:
            cursor_data = decode_cursor(cursor)
            if cursor_data:
                c_dt, c_id = cursor_data
                conditions.append(
                    or_(
                        Post.created_at < c_dt,
                        and_(Post.created_at == c_dt, Post.id < c_id),
                    )
                )

        stmt = (
            select(Post)
            .options(selectinload(Post.persona))
            .where(and_(*conditions))
        )

        if sort == "trending":
            # Trending calculation: order by reaction count + comment count, then recency
            reactions_subq = (
                select(func.count(Reaction.id))
                .where(and_(Reaction.target_type == "POST", Reaction.target_id == Post.id))
                .scalar_subquery()
            )
            comments_subq = (
                select(func.count(Comment.id))
                .where(and_(Comment.post_id == Post.id, Comment.is_deleted == False))
                .scalar_subquery()
            )
            stmt = stmt.order_by(
                desc(reactions_subq * 2 + comments_subq * 3),
                desc(Post.created_at),
                desc(Post.id),
            )
        else:
            stmt = stmt.order_by(desc(Post.created_at), desc(Post.id))

        stmt = stmt.limit(limit + 1)
        result = await db.execute(stmt)
        rows = list(result.scalars().all())

        has_more = len(rows) > limit
        if has_more:
            posts = rows[:limit]
            next_cursor = encode_cursor(posts[-1].created_at, posts[-1].id)
        else:
            posts = rows
            next_cursor = None

        # Build responses with reaction summaries
        items: List[PostResponse] = []
        for post in posts:
            res = await SocialService._format_post_response(db, post, current_persona)
            items.append(res)

        return items, next_cursor, has_more

    @staticmethod
    async def get_my_posts(
        db: AsyncSession,
        current_persona: Persona,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> Tuple[List[PostResponse], Optional[str], bool]:
        """View author's own posts privately."""
        limit = max(1, min(limit, 50))
        conditions = [
            Post.persona_id == current_persona.id,
            Post.is_deleted == False,
        ]

        if cursor:
            cursor_data = decode_cursor(cursor)
            if cursor_data:
                c_dt, c_id = cursor_data
                conditions.append(
                    or_(
                        Post.created_at < c_dt,
                        and_(Post.created_at == c_dt, Post.id < c_id),
                    )
                )

        stmt = (
            select(Post)
            .options(selectinload(Post.persona))
            .where(and_(*conditions))
            .order_by(desc(Post.created_at), desc(Post.id))
            .limit(limit + 1)
        )
        result = await db.execute(stmt)
        rows = list(result.scalars().all())

        has_more = len(rows) > limit
        if has_more:
            posts = rows[:limit]
            next_cursor = encode_cursor(posts[-1].created_at, posts[-1].id)
        else:
            posts = rows
            next_cursor = None

        items = [
            await SocialService._format_post_response(db, p, current_persona)
            for p in posts
        ]
        return items, next_cursor, has_more

    @staticmethod
    async def get_post_by_id(
        db: AsyncSession,
        post_id: uuid.UUID,
        current_persona: Optional[Persona],
    ) -> PostResponse:
        """Fetch single post by ID and increment view count."""
        stmt = (
            select(Post)
            .options(selectinload(Post.persona))
            .where(and_(Post.id == post_id, Post.is_deleted == False))
        )
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found or has been removed.",
            )

        # Check block isolation
        blocked_ids = await SocialService.get_blocked_persona_ids(
            db, current_persona.id if current_persona else None
        )
        if post.persona_id in blocked_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post unavailable.",
            )

        # Increment view count
        post.view_count += 1
        await db.commit()

        return await SocialService._format_post_response(db, post, current_persona)

    @staticmethod
    async def delete_post(
        db: AsyncSession,
        post_id: uuid.UUID,
        current_persona: Persona,
    ) -> bool:
        """Soft-delete own post. Non-authors are forbidden."""
        stmt = select(Post).where(Post.id == post_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        if not post or post.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found.",
            )

        if post.persona_id != current_persona.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this post.",
            )

        post.is_deleted = True
        await db.commit()
        return True

    @staticmethod
    async def add_comment(
        db: AsyncSession,
        post_id: uuid.UUID,
        current_persona: Persona,
        data: CommentCreateRequest,
    ) -> CommentResponse:
        """Add a comment to an anonymous post."""
        # Check post
        stmt = select(Post).where(and_(Post.id == post_id, Post.is_deleted == False))
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found or has been removed.",
            )

        if not post.allow_comments:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Comments have been disabled by the author on this post.",
            )

        # Check blocking
        blocked_ids = await SocialService.get_blocked_persona_ids(db, current_persona.id)
        if post.persona_id in blocked_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot comment on this post.",
            )

        # Moderation check
        eval_result = ContentModerationEngine.evaluate_text(data.content)
        if not eval_result.is_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=eval_result.rejection_message or "Comment violates safety standards.",
            )

        # Verify parent comment if nested reply
        if data.parent_id:
            parent_stmt = select(Comment).where(
                and_(
                    Comment.id == data.parent_id,
                    Comment.post_id == post_id,
                    Comment.is_deleted == False,
                )
            )
            parent_res = await db.execute(parent_stmt)
            if not parent_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent comment not found on this post.",
                )

        comment = Comment(
            post_id=post_id,
            persona_id=current_persona.id,
            parent_id=data.parent_id,
            content=data.content.strip(),
            is_deleted=False,
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)

        return CommentResponse(
            id=comment.id,
            post_id=post_id,
            persona=PersonaPublicResponse(
                id=current_persona.id,
                display_name=current_persona.display_name,
                avatar_seed=current_persona.avatar_seed,
                is_active=current_persona.is_active,
            ),
            parent_id=comment.parent_id,
            content=comment.content,
            is_op=(current_persona.id == post.persona_id),
            is_own=True,
            replies_count=0,
            created_at=ensure_utc(comment.created_at),
        )

    @staticmethod
    async def get_comments(
        db: AsyncSession,
        post_id: uuid.UUID,
        current_persona: Optional[Persona],
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> Tuple[List[CommentResponse], Optional[str], bool]:
        """Fetch comments for a post, excluding comments from blocked personas."""
        limit = max(1, min(limit, 100))
        blocked_ids = await SocialService.get_blocked_persona_ids(
            db, current_persona.id if current_persona else None
        )

        # Get post author to determine is_op
        post_stmt = select(Post.persona_id).where(Post.id == post_id)
        post_res = await db.execute(post_stmt)
        post_author_id = post_res.scalar_one_or_none()

        conditions = [
            Comment.post_id == post_id,
            Comment.is_deleted == False,
        ]
        if blocked_ids:
            conditions.append(Comment.persona_id.not_in(blocked_ids))

        if cursor:
            cursor_data = decode_cursor(cursor)
            if cursor_data:
                c_dt, c_id = cursor_data
                conditions.append(
                    or_(
                        Comment.created_at < c_dt,
                        and_(Comment.created_at == c_dt, Comment.id < c_id),
                    )
                )

        stmt = (
            select(Comment)
            .options(selectinload(Comment.persona))
            .where(and_(*conditions))
            .order_by(Comment.created_at.asc(), Comment.id.asc())
            .limit(limit + 1)
        )
        result = await db.execute(stmt)
        rows = list(result.scalars().all())

        has_more = len(rows) > limit
        if has_more:
            comments = rows[:limit]
            next_cursor = encode_cursor(comments[-1].created_at, comments[-1].id)
        else:
            comments = rows
            next_cursor = None

        items: List[CommentResponse] = []
        for c in comments:
            # Count replies
            rep_stmt = select(func.count(Comment.id)).where(
                and_(Comment.parent_id == c.id, Comment.is_deleted == False)
            )
            rep_res = await db.execute(rep_stmt)
            replies_count = rep_res.scalar() or 0

            items.append(
                CommentResponse(
                    id=c.id,
                    post_id=c.post_id,
                    persona=PersonaPublicResponse(
                        id=c.persona.id,
                        display_name=c.persona.display_name,
                        avatar_seed=c.persona.avatar_seed,
                        is_active=c.persona.is_active,
                    ),
                    parent_id=c.parent_id,
                    content=c.content,
                    is_op=(c.persona_id == post_author_id),
                    is_own=(current_persona is not None and c.persona_id == current_persona.id),
                    replies_count=replies_count,
                    created_at=ensure_utc(c.created_at),
                )
            )

        return items, next_cursor, has_more

    @staticmethod
    async def delete_comment(
        db: AsyncSession,
        comment_id: uuid.UUID,
        current_persona: Persona,
    ) -> bool:
        """Soft-delete a comment. Non-authors are forbidden."""
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(stmt)
        comment = result.scalar_one_or_none()
        if not comment or comment.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found.",
            )

        if comment.persona_id != current_persona.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this comment.",
            )

        comment.is_deleted = True
        await db.commit()
        return True

    @staticmethod
    async def react_to_post(
        db: AsyncSession,
        post_id: uuid.UUID,
        current_persona: Persona,
        reaction_type: str,
    ) -> ReactionResponse:
        """Add, toggle off, or update an anonymous reaction to a post."""
        rx_type = reaction_type.upper().strip()
        if rx_type not in ["UPVOTE", "FLAME", "HEART", "INSIGHTFUL"]:
            rx_type = "UPVOTE"

        # Check post
        post_stmt = select(Post).where(and_(Post.id == post_id, Post.is_deleted == False))
        post_res = await db.execute(post_stmt)
        if not post_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found.",
            )

        # Check existing reaction
        stmt = select(Reaction).where(
            and_(
                Reaction.persona_id == current_persona.id,
                Reaction.target_type == "POST",
                Reaction.target_id == post_id,
            )
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()

        action = "ADDED"
        active_rx: Optional[str] = rx_type

        if existing:
            if existing.reaction_type == rx_type:
                # Toggle off (remove)
                await db.delete(existing)
                action = "REMOVED"
                active_rx = None
            else:
                # Update reaction
                existing.reaction_type = rx_type
                action = "UPDATED"
        else:
            new_rx = Reaction(
                persona_id=current_persona.id,
                target_type="POST",
                target_id=post_id,
                reaction_type=rx_type,
            )
            db.add(new_rx)

        await db.commit()

        # Compute summary
        counts = await SocialService._get_reactions_summary(db, "POST", post_id)
        return ReactionResponse(
            action=action,
            reaction_type=active_rx,
            reactions_summary=counts,
        )

    @staticmethod
    async def block_persona(
        db: AsyncSession,
        current_persona: Persona,
        target_persona_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> BlockResponse:
        """Block another anonymous persona. Universal anti-self block constraint enforced."""
        if current_persona.id == target_persona_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot block your own persona.",
            )

        # Verify target persona exists
        target_stmt = select(Persona).where(Persona.id == target_persona_id)
        target_res = await db.execute(target_stmt)
        target = target_res.scalar_one_or_none()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona not found.",
            )

        # Check existing block
        stmt = select(Block).where(
            and_(
                Block.blocker_persona_id == current_persona.id,
                Block.blocked_persona_id == target_persona_id,
            )
        )
        res = await db.execute(stmt)
        block = res.scalar_one_or_none()

        if not block:
            block = Block(
                blocker_persona_id=current_persona.id,
                blocked_persona_id=target_persona_id,
                reason=reason,
            )
            db.add(block)
            await db.commit()
            await db.refresh(block)

        return BlockResponse(
            id=block.id,
            blocker_persona_id=block.blocker_persona_id,
            blocked_persona_id=block.blocked_persona_id,
            blocked_persona_name=target.display_name,
            created_at=ensure_utc(block.created_at),
        )

    @staticmethod
    async def unblock_persona(
        db: AsyncSession,
        current_persona: Persona,
        target_persona_id: uuid.UUID,
    ) -> bool:
        """Unblock a previously blocked persona."""
        stmt = select(Block).where(
            and_(
                Block.blocker_persona_id == current_persona.id,
                Block.blocked_persona_id == target_persona_id,
            )
        )
        res = await db.execute(stmt)
        block = res.scalar_one_or_none()
        if block:
            await db.delete(block)
            await db.commit()
        return True

    @staticmethod
    async def create_report(
        db: AsyncSession,
        current_persona: Persona,
        target_type: str,
        target_id: uuid.UUID,
        reason: str,
    ) -> ReportResponse:
        """File a report against content or persona."""
        report = Report(
            reporter_persona_id=current_persona.id,
            target_type=target_type.upper().strip(),
            target_id=target_id,
            reason=reason.strip(),
            status=ReportStatus.PENDING,
        )
        db.add(report)

        # Append to audit log
        log = AuditLog(
            actor_id=current_persona.account_id,
            actor_type="ACCOUNT",
            action="REPORT_FILED",
            target_type=target_type.upper().strip(),
            target_id=target_id,
            details_json=f'{{"reason": "{reason.strip()[:100]}"}}',
        )
        db.add(log)
        await db.commit()
        await db.refresh(report)

        return ReportResponse(
            id=report.id,
            target_type=report.target_type,
            target_id=report.target_id,
            status=report.status.value,
            created_at=ensure_utc(report.created_at),
        )

    # ---------------- Helper Methods ----------------

    @staticmethod
    async def _format_post_response(
        db: AsyncSession,
        post: Post,
        current_persona: Optional[Persona],
    ) -> PostResponse:
        """Compute reaction summaries and user interaction state with zero identity leakage."""
        reactions_summary = await SocialService._get_reactions_summary(db, "POST", post.id)

        # Comments count
        c_stmt = select(func.count(Comment.id)).where(
            and_(Comment.post_id == post.id, Comment.is_deleted == False)
        )
        c_res = await db.execute(c_stmt)
        comments_count = c_res.scalar() or 0

        # Current user's reaction
        user_reaction: Optional[str] = None
        if current_persona:
            rx_stmt = select(Reaction.reaction_type).where(
                and_(
                    Reaction.persona_id == current_persona.id,
                    Reaction.target_type == "POST",
                    Reaction.target_id == post.id,
                )
            )
            rx_res = await db.execute(rx_stmt)
            user_reaction = rx_res.scalar_one_or_none()

        is_own = bool(current_persona and current_persona.id == post.persona_id)

        return PostResponse(
            id=post.id,
            persona=PersonaPublicResponse(
                id=post.persona.id,
                display_name=post.persona.display_name,
                avatar_seed=post.persona.avatar_seed,
                declared_campus=post.campus_name,
                is_active=post.persona.is_active,
            ),
            content=post.content,
            post_type=post.post_type.value,
            tag=post.tag,
            is_sensitive=post.is_sensitive,
            allow_comments=post.allow_comments,
            view_count=post.view_count,
            campus_name=post.campus_name,
            upvotes_count=reactions_summary.get("upvotes", 0),
            comments_count=comments_count,
            reactions=reactions_summary,
            user_reaction=user_reaction,
            is_own=is_own,
            created_at=ensure_utc(post.created_at),
        )

    @staticmethod
    async def _get_reactions_summary(
        db: AsyncSession, target_type: str, target_id: uuid.UUID
    ) -> Dict[str, int]:
        stmt = (
            select(Reaction.reaction_type, func.count(Reaction.id))
            .where(and_(Reaction.target_type == target_type, Reaction.target_id == target_id))
            .group_by(Reaction.reaction_type)
        )
        res = await db.execute(stmt)
        counts = {"upvotes": 0, "flames": 0, "hearts": 0, "insightful": 0}
        for rx_type, count in res.all():
            t = rx_type.lower()
            if t in ["upvote", "upvotes"]:
                counts["upvotes"] = count
            elif t in ["flame", "flames"]:
                counts["flames"] = count
            elif t in ["heart", "hearts"]:
                counts["hearts"] = count
            elif t in ["insightful"]:
                counts["insightful"] = count
        return counts
