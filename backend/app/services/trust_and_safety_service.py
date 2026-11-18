import hashlib
import json
import uuid
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any, Set
from fastapi import HTTPException, status
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import generate_mfa_secret, verify_totp, mask_email
from backend.app.models.base import utc_now, ensure_utc
from backend.app.models.account import Account, AccountStatus
from backend.app.models.persona import Persona
from backend.app.models.invitation import Invitation, InvitationStatus
from backend.app.models.social import Post, Comment, Story, StoryComment
from backend.app.models.event import Event
from backend.app.models.moderation import (
    Block,
    Report,
    ReportStatus,
    ModerationAction,
    ModerationActionType,
    Appeal,
    AppealStatus,
    AuditLog,
)
from backend.app.schemas.trust_and_safety import (
    AdminOverviewResponse,
    ReportAdminItem,
    ReportListResponse,
    ModerationQueueItem,
    ModerationQueueResponse,
    UserRestrictionRequest,
    ModerationActionResponse,
    AppealResponse,
    AppealListResponse,
    AdminInvitationItem,
    AdminInvitationListResponse,
    AdminAccountItem,
    AdminAccountListResponse,
    AuditLogItem,
    AuditLogListResponse,
    BlockedPersonaItem,
    MfaSetupResponse,
)


class TrustAndSafetyService:
    """
    Core business logic for the AFTR Trust, Safety and Moderation Platform.
    Enforces least privilege, audit logging, role separation, and zero identity leakage.
    """

    @staticmethod
    async def log_audit_event(
        db: AsyncSession,
        actor_id: Optional[uuid.UUID],
        actor_type: str,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[uuid.UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        client_ip: Optional[str] = None,
    ) -> AuditLog:
        """Create an immutable append-only audit log entry."""
        ip_hash = None
        if client_ip:
            ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()

        details_str = json.dumps(details) if details else None

        log_entry = AuditLog(
            actor_id=actor_id,
            actor_type=actor_type,
            action=action,
            target_type=target_type,
            target_id=target_id,
            ip_hash=ip_hash,
            details_json=details_str,
            created_at=utc_now(),
        )
        db.add(log_entry)
        await db.commit()
        return log_entry

    # --- 1. Overview Metrics ---

    @staticmethod
    async def get_overview(db: AsyncSession) -> AdminOverviewResponse:
        """Aggregate system safety and moderation health metrics."""
        # Pending reports
        pending_reports = (
            await db.execute(
                select(func.count(Report.id)).where(Report.status == ReportStatus.PENDING)
            )
        ).scalar() or 0

        # Pending review queue items (posts, stories, comments)
        pending_posts = (
            await db.execute(
                select(func.count(Post.id)).where(
                    and_(Post.moderation_status == "PENDING_REVIEW", Post.is_deleted == False)
                )
            )
        ).scalar() or 0

        pending_stories = (
            await db.execute(
                select(func.count(Story.id)).where(
                    and_(Story.moderation_status == "PENDING_REVIEW", Story.is_deleted == False)
                )
            )
        ).scalar() or 0

        pending_comments = (
            await db.execute(
                select(func.count(Comment.id)).where(
                    and_(Comment.moderation_status == "PENDING_REVIEW", Comment.is_deleted == False)
                )
            )
        ).scalar() or 0

        total_review_queue = pending_posts + pending_stories + pending_comments

        # Pending appeals
        pending_appeals = (
            await db.execute(
                select(func.count(Appeal.id)).where(Appeal.status == AppealStatus.PENDING)
            )
        ).scalar() or 0

        # Active accounts
        active_accounts = (
            await db.execute(
                select(func.count(Account.id)).where(Account.status == AccountStatus.ACTIVE)
            )
        ).scalar() or 0

        # Suspended personas
        suspended_personas = (
            await db.execute(
                select(func.count(Persona.id)).where(Persona.is_active == False)
            )
        ).scalar() or 0

        # Banned accounts
        banned_accounts = (
            await db.execute(
                select(func.count(Account.id)).where(Account.status == AccountStatus.BANNED)
            )
        ).scalar() or 0

        # Total moderation actions
        total_actions = (
            await db.execute(select(func.count(ModerationAction.id)))
        ).scalar() or 0

        # Recent 5 actions
        recent_stmt = (
            select(ModerationAction)
            .order_by(desc(ModerationAction.created_at))
            .limit(5)
        )
        recent_rows = (await db.execute(recent_stmt)).scalars().all()
        recent_actions = [
            {
                "id": str(a.id),
                "action_type": a.action_type.value if hasattr(a.action_type, "value") else str(a.action_type),
                "target_type": a.target_type,
                "reason": a.reason,
                "created_at": ensure_utc(a.created_at).isoformat(),
            }
            for a in recent_rows
        ]

        return AdminOverviewResponse(
            pending_reports_count=pending_reports,
            pending_review_queue_count=total_review_queue,
            pending_appeals_count=pending_appeals,
            total_active_accounts=active_accounts,
            suspended_personas_count=suspended_personas,
            banned_accounts_count=banned_accounts,
            total_moderation_actions=total_actions,
            recent_actions=recent_actions,
        )

    # --- 2. Reports Management ---

    @staticmethod
    async def list_reports(
        db: AsyncSession,
        status_filter: Optional[str] = None,
        target_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ReportListResponse:
        """List reports with filter options."""
        conditions = []
        if status_filter and status_filter.upper() != "ALL":
            try:
                conditions.append(Report.status == ReportStatus[status_filter.upper()])
            except KeyError:
                pass

        if target_type and target_type.upper() != "ALL":
            conditions.append(Report.target_type == target_type.upper())

        total = (
            await db.execute(select(func.count(Report.id)).where(*conditions))
        ).scalar() or 0

        pending_count = (
            await db.execute(
                select(func.count(Report.id)).where(Report.status == ReportStatus.PENDING)
            )
        ).scalar() or 0

        stmt = (
            select(Report)
            .where(*conditions)
            .order_by(desc(Report.created_at))
            .limit(limit)
            .offset(offset)
        )
        reports = (await db.execute(stmt)).scalars().all()

        items: List[ReportAdminItem] = []
        for r in reports:
            # Resolve reporter persona pseudonym
            p_res = await db.execute(select(Persona.display_name).where(Persona.id == r.reporter_persona_id))
            rep_name = p_res.scalar_one_or_none() or "Anonymous Member"

            # Optional content excerpt
            excerpt = None
            if r.target_type == "POST":
                p_text = (await db.execute(select(Post.content).where(Post.id == r.target_id))).scalar_one_or_none()
                if p_text:
                    excerpt = p_text[:120] + ("..." if len(p_text) > 120 else "")
            elif r.target_type == "COMMENT":
                c_text = (await db.execute(select(Comment.content).where(Comment.id == r.target_id))).scalar_one_or_none()
                if c_text:
                    excerpt = c_text[:120] + ("..." if len(c_text) > 120 else "")
            elif r.target_type == "STORY":
                s_text = (await db.execute(select(Story.content).where(Story.id == r.target_id))).scalar_one_or_none()
                if s_text:
                    excerpt = s_text[:120] + ("..." if len(s_text) > 120 else "")
            elif r.target_type == "EVENT":
                e_title = (await db.execute(select(Event.title).where(Event.id == r.target_id))).scalar_one_or_none()
                if e_title:
                    excerpt = f"Event: {e_title}"

            items.append(
                ReportAdminItem(
                    id=r.id,
                    target_type=r.target_type,
                    target_id=r.target_id,
                    reason=r.reason,
                    status=r.status.value if hasattr(r.status, "value") else str(r.status),
                    reporter_persona_name=rep_name,
                    reporter_persona_id=r.reporter_persona_id,
                    resolved_by=r.resolved_by,
                    resolution_notes=r.resolution_notes,
                    resolved_at=ensure_utc(r.resolved_at) if r.resolved_at else None,
                    created_at=ensure_utc(r.created_at),
                    content_excerpt=excerpt,
                )
            )

        return ReportListResponse(items=items, total=total, pending_count=pending_count)

    @staticmethod
    async def resolve_report(
        db: AsyncSession,
        report_id: uuid.UUID,
        action: str,
        notes: Optional[str],
        moderator: Account,
    ) -> ReportAdminItem:
        """Resolve a report: DISMISS, TAKEDOWN, or ACTION_TAKEN."""
        stmt = select(Report).where(Report.id == report_id)
        report = (await db.execute(stmt)).scalar_one_or_none()
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

        upper_action = action.upper().strip()
        now = utc_now()
        report.resolved_by = moderator.id
        report.resolved_at = now
        report.resolution_notes = notes

        if upper_action == "DISMISS":
            report.status = ReportStatus.DISMISSED
        elif upper_action in ("TAKEDOWN", "ACTION_TAKEN"):
            report.status = ReportStatus.ACTIONED
            # If takedown, soft-delete target content
            if report.target_type == "POST":
                p = (await db.execute(select(Post).where(Post.id == report.target_id))).scalar_one_or_none()
                if p:
                    p.is_deleted = True
                    p.moderation_status = "REJECTED"
            elif report.target_type == "COMMENT":
                c = (await db.execute(select(Comment).where(Comment.id == report.target_id))).scalar_one_or_none()
                if c:
                    c.is_deleted = True
                    c.moderation_status = "REJECTED"
            elif report.target_type == "STORY":
                s = (await db.execute(select(Story).where(Story.id == report.target_id))).scalar_one_or_none()
                if s:
                    s.is_deleted = True
                    s.moderation_status = "REJECTED"
            elif report.target_type == "EVENT":
                ev = (await db.execute(select(Event).where(Event.id == report.target_id))).scalar_one_or_none()
                if ev:
                    ev.is_cancelled = True
                    ev.is_deleted = True

        await db.commit()
        await db.refresh(report)

        # Audit log
        await TrustAndSafetyService.log_audit_event(
            db,
            actor_id=moderator.id,
            actor_type="MODERATOR",
            action=f"REPORT_{upper_action}",
            target_type=report.target_type,
            target_id=report.target_id,
            details={"report_id": str(report.id), "notes": notes},
        )

        p_name = (await db.execute(select(Persona.display_name).where(Persona.id == report.reporter_persona_id))).scalar_one_or_none()
        return ReportAdminItem(
            id=report.id,
            target_type=report.target_type,
            target_id=report.target_id,
            reason=report.reason,
            status=report.status.value if hasattr(report.status, "value") else str(report.status),
            reporter_persona_name=p_name or "Anonymous Member",
            reporter_persona_id=report.reporter_persona_id,
            resolved_by=report.resolved_by,
            resolution_notes=report.resolution_notes,
            resolved_at=ensure_utc(report.resolved_at),
            created_at=ensure_utc(report.created_at),
        )

    # --- 3. Content Moderation Review Queue ---

    @staticmethod
    async def get_moderation_queue(
        db: AsyncSession,
        limit: int = 30,
        offset: int = 0,
    ) -> ModerationQueueResponse:
        """
        List items that require human moderator review before publication,
        or items that have active reports pending review.
        """
        items: List[ModerationQueueItem] = []

        # 1. Posts in PENDING_REVIEW
        post_stmt = (
            select(Post)
            .options(selectinload(Post.persona))
            .where(and_(Post.moderation_status == "PENDING_REVIEW", Post.is_deleted == False))
            .order_by(desc(Post.created_at))
            .limit(limit)
        )
        pending_posts = (await db.execute(post_stmt)).scalars().all()
        for p in pending_posts:
            rep_count = (
                await db.execute(select(func.count(Report.id)).where(Report.target_id == p.id))
            ).scalar() or 0
            items.append(
                ModerationQueueItem(
                    target_type="POST",
                    target_id=p.id,
                    content=p.content,
                    category=p.tag,
                    campus_name=p.campus_name,
                    moderation_status=p.moderation_status,
                    author_persona_id=p.persona_id,
                    author_persona_name=p.persona.display_name if p.persona else "Anonymous",
                    author_avatar_seed=p.persona.avatar_seed if p.persona else "seed",
                    flagged_reasons=["Held for moderator review prior to publication"],
                    reports_count=rep_count,
                    created_at=ensure_utc(p.created_at),
                )
            )

        # 2. Stories in PENDING_REVIEW
        story_stmt = (
            select(Story)
            .options(selectinload(Story.persona))
            .where(and_(Story.moderation_status == "PENDING_REVIEW", Story.is_deleted == False))
            .order_by(desc(Story.created_at))
            .limit(limit)
        )
        pending_stories = (await db.execute(story_stmt)).scalars().all()
        for s in pending_stories:
            rep_count = (
                await db.execute(select(func.count(Report.id)).where(Report.target_id == s.id))
            ).scalar() or 0
            items.append(
                ModerationQueueItem(
                    target_type="STORY",
                    target_id=s.id,
                    content=s.content,
                    category=s.category,
                    campus_name=s.campus_name,
                    moderation_status=s.moderation_status,
                    author_persona_id=s.persona_id,
                    author_persona_name=s.persona.display_name if s.persona else "Anonymous",
                    author_avatar_seed=s.persona.avatar_seed if s.persona else "seed",
                    flagged_reasons=["Ephemeral story flagged for human review"],
                    reports_count=rep_count,
                    created_at=ensure_utc(s.created_at),
                )
            )

        # 3. Comments in PENDING_REVIEW
        comment_stmt = (
            select(Comment)
            .options(selectinload(Comment.persona))
            .where(and_(Comment.moderation_status == "PENDING_REVIEW", Comment.is_deleted == False))
            .order_by(desc(Comment.created_at))
            .limit(limit)
        )
        pending_comments = (await db.execute(comment_stmt)).scalars().all()
        for c in pending_comments:
            items.append(
                ModerationQueueItem(
                    target_type="COMMENT",
                    target_id=c.id,
                    content=c.content,
                    category="Comment",
                    campus_name=None,
                    moderation_status=c.moderation_status,
                    author_persona_id=c.persona_id,
                    author_persona_name=c.persona.display_name if c.persona else "Anonymous",
                    author_avatar_seed=c.persona.avatar_seed if c.persona else "seed",
                    flagged_reasons=["Comment queued for moderator review"],
                    reports_count=0,
                    created_at=ensure_utc(c.created_at),
                )
            )

        return ModerationQueueResponse(items=items, total=len(items))

    @staticmethod
    async def make_moderation_decision(
        db: AsyncSession,
        target_type: str,
        target_id: uuid.UUID,
        action: str,
        reason: Optional[str],
        moderator: Account,
    ) -> Dict[str, Any]:
        """
        Approve or Take Down content in review queue.
        - If APPROVE: content status transitions to PUBLISHED, entering public feeds.
        - If TAKEDOWN: content status transitions to REJECTED, soft-deleted, and moderation action logged.
        """
        upper_action = action.upper().strip()
        upper_type = target_type.upper().strip()

        author_persona_id = None

        if upper_type == "POST":
            p = (await db.execute(select(Post).where(Post.id == target_id))).scalar_one_or_none()
            if not p:
                raise HTTPException(status_code=404, detail="Post not found")
            author_persona_id = p.persona_id
            if upper_action == "APPROVE":
                p.moderation_status = "PUBLISHED"
                p.is_deleted = False
            else:
                p.moderation_status = "REJECTED"
                p.is_deleted = True

        elif upper_type == "STORY":
            s = (await db.execute(select(Story).where(Story.id == target_id))).scalar_one_or_none()
            if not s:
                raise HTTPException(status_code=404, detail="Story not found")
            author_persona_id = s.persona_id
            if upper_action == "APPROVE":
                s.moderation_status = "APPROVED"
                s.is_deleted = False
            else:
                s.moderation_status = "REJECTED"
                s.is_deleted = True

        elif upper_type == "COMMENT":
            c = (await db.execute(select(Comment).where(Comment.id == target_id))).scalar_one_or_none()
            if not c:
                raise HTTPException(status_code=404, detail="Comment not found")
            author_persona_id = c.persona_id
            if upper_action == "APPROVE":
                c.moderation_status = "PUBLISHED"
                c.is_deleted = False
            else:
                c.moderation_status = "REJECTED"
                c.is_deleted = True
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported target type: {target_type}")

        # If takedown, create ModerationAction record
        action_id = None
        if upper_action == "TAKEDOWN":
            mod_action = ModerationAction(
                target_type=upper_type,
                target_id=target_id,
                target_persona_id=author_persona_id,
                action_type=ModerationActionType.POST_REMOVED,
                moderator_id=moderator.id,
                reason=reason or "Content violates AFTR community standards",
                strike_count=1,
            )
            db.add(mod_action)
            await db.flush()
            action_id = mod_action.id

        await db.commit()

        # Log audit entry
        await TrustAndSafetyService.log_audit_event(
            db,
            actor_id=moderator.id,
            actor_type="MODERATOR",
            action=f"CONTENT_{upper_action}",
            target_type=upper_type,
            target_id=target_id,
            details={"reason": reason, "moderation_action_id": str(action_id) if action_id else None},
        )

        return {
            "target_type": upper_type,
            "target_id": str(target_id),
            "action": upper_action,
            "status": "PUBLISHED" if upper_action == "APPROVE" else "REJECTED",
            "moderation_action_id": str(action_id) if action_id else None,
        }

    # --- 4. User Restrictions (Warnings, Suspensions, Bans) ---

    @staticmethod
    async def apply_user_restriction(
        db: AsyncSession,
        req: UserRestrictionRequest,
        actor: Account,
    ) -> ModerationActionResponse:
        """
        Enforce user restrictions:
        - WARNING: Issues strike and moderation notice.
        - SHADOWBAN: Removes persona from discovery feeds.
        - PERSONA_SUSPENDED: Deactivates specific persona.
        - ACCOUNT_BANNED: Bans entire account and deactivates all personas (Requires SECURITY_ADMIN).
        """
        action_type_str = req.action_type.upper().strip()

        # Role-based restriction: ACCOUNT_BANNED requires SECURITY_ADMIN
        if action_type_str == "ACCOUNT_BANNED" and actor.role != "SECURITY_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security Administrator role required to execute account bans.",
            )

        # Lookup persona
        persona_stmt = select(Persona).where(Persona.id == req.target_persona_id)
        persona = (await db.execute(persona_stmt)).scalar_one_or_none()
        if not persona:
            raise HTTPException(status_code=404, detail="Target persona not found")

        # Lookup account
        account_stmt = select(Account).where(Account.id == persona.account_id)
        account = (await db.execute(account_stmt)).scalar_one_or_none()
        if not account:
            raise HTTPException(status_code=404, detail="Target account not found")

        try:
            mod_enum = ModerationActionType[action_type_str]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid action type: {action_type_str}")

        # Execute restriction
        if mod_enum == ModerationActionType.ACCOUNT_BANNED:
            account.status = AccountStatus.BANNED
            # Deactivate all personas
            all_personas_stmt = select(Persona).where(Persona.account_id == account.id)
            for p in (await db.execute(all_personas_stmt)).scalars().all():
                p.is_active = False
                p.is_discoverable = False

        elif mod_enum == ModerationActionType.PERSONA_SUSPENDED:
            persona.is_active = False
            persona.is_discoverable = False

        elif mod_enum == ModerationActionType.SHADOWBAN:
            persona.is_discoverable = False

        action_record = ModerationAction(
            target_type="PERSONA",
            target_id=persona.id,
            target_persona_id=persona.id,
            action_type=mod_enum,
            moderator_id=actor.id,
            reason=req.reason.strip(),
            strike_count=req.strike_count,
        )
        db.add(action_record)
        await db.commit()
        await db.refresh(action_record)

        # Audit log
        await TrustAndSafetyService.log_audit_event(
            db,
            actor_id=actor.id,
            actor_type="SECURITY_ADMIN" if actor.role == "SECURITY_ADMIN" else "MODERATOR",
            action=f"RESTRICTION_{action_type_str}",
            target_type="PERSONA",
            target_id=persona.id,
            details={"reason": req.reason, "strike_count": req.strike_count, "account_id": str(account.id)},
        )

        return ModerationActionResponse(
            id=action_record.id,
            target_type=action_record.target_type,
            target_id=action_record.target_id,
            target_persona_id=action_record.target_persona_id,
            action_type=action_record.action_type.value if hasattr(action_record.action_type, "value") else str(action_record.action_type),
            moderator_id=action_record.moderator_id,
            reason=action_record.reason,
            strike_count=action_record.strike_count,
            created_at=ensure_utc(action_record.created_at),
        )

    # --- 5. Appeals Workflow ---

    @staticmethod
    async def create_appeal(
        db: AsyncSession,
        current_persona: Persona,
        action_id: uuid.UUID,
        reason: str,
    ) -> AppealResponse:
        """User safety: Submit an appeal against an adverse moderation action."""
        action_stmt = select(ModerationAction).where(ModerationAction.id == action_id)
        action = (await db.execute(action_stmt)).scalar_one_or_none()
        if not action:
            raise HTTPException(status_code=404, detail="Moderation action not found")

        # Check existing pending appeal
        existing_stmt = select(Appeal).where(
            and_(Appeal.moderation_action_id == action_id, Appeal.status == AppealStatus.PENDING)
        )
        existing = (await db.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="An appeal is already pending for this moderation action.")

        appeal = Appeal(
            moderation_action_id=action_id,
            appellant_persona_id=current_persona.id,
            reason=reason.strip(),
            status=AppealStatus.PENDING,
        )
        db.add(appeal)
        await db.commit()
        await db.refresh(appeal)

        # Audit log
        await TrustAndSafetyService.log_audit_event(
            db,
            actor_id=current_persona.account_id,
            actor_type="PERSONA",
            action="APPEAL_SUBMITTED",
            target_type="MODERATION_ACTION",
            target_id=action_id,
            details={"appeal_id": str(appeal.id)},
        )

        return AppealResponse(
            id=appeal.id,
            moderation_action_id=appeal.moderation_action_id,
            appellant_persona_id=appeal.appellant_persona_id,
            reason=appeal.reason,
            status=appeal.status.value if hasattr(appeal.status, "value") else str(appeal.status),
            created_at=ensure_utc(appeal.created_at),
        )

    @staticmethod
    async def list_my_appeals(
        db: AsyncSession,
        current_persona: Persona,
    ) -> List[AppealResponse]:
        """User safety: View caller's submitted appeals and statuses."""
        stmt = (
            select(Appeal)
            .where(Appeal.appellant_persona_id == current_persona.id)
            .order_by(desc(Appeal.created_at))
        )
        appeals = (await db.execute(stmt)).scalars().all()
        return [
            AppealResponse(
                id=a.id,
                moderation_action_id=a.moderation_action_id,
                appellant_persona_id=a.appellant_persona_id,
                reason=a.reason,
                status=a.status.value if hasattr(a.status, "value") else str(a.status),
                reviewed_at=ensure_utc(a.reviewed_at) if a.reviewed_at else None,
                resolution_notes=a.resolution_notes,
                created_at=ensure_utc(a.created_at),
            )
            for a in appeals
        ]

    @staticmethod
    async def list_appeals(
        db: AsyncSession,
        status_filter: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> AppealListResponse:
        """Admin: View appeals submitted across the platform."""
        conditions = []
        if status_filter and status_filter.upper() != "ALL":
            try:
                conditions.append(Appeal.status == AppealStatus[status_filter.upper()])
            except KeyError:
                pass

        total = (
            await db.execute(select(func.count(Appeal.id)).where(*conditions))
        ).scalar() or 0

        pending_count = (
            await db.execute(
                select(func.count(Appeal.id)).where(Appeal.status == AppealStatus.PENDING)
            )
        ).scalar() or 0

        stmt = (
            select(Appeal)
            .where(*conditions)
            .order_by(desc(Appeal.created_at))
            .limit(limit)
            .offset(offset)
        )
        appeals = (await db.execute(stmt)).scalars().all()

        items: List[AppealResponse] = []
        for a in appeals:
            # Action details
            act = (await db.execute(select(ModerationAction).where(ModerationAction.id == a.moderation_action_id))).scalar_one_or_none()
            act_details = None
            if act:
                act_details = {
                    "action_type": act.action_type.value if hasattr(act.action_type, "value") else str(act.action_type),
                    "reason": act.reason,
                    "target_type": act.target_type,
                }

            items.append(
                AppealResponse(
                    id=a.id,
                    moderation_action_id=a.moderation_action_id,
                    appellant_persona_id=a.appellant_persona_id,
                    reason=a.reason,
                    status=a.status.value if hasattr(a.status, "value") else str(a.status),
                    reviewed_at=ensure_utc(a.reviewed_at) if a.reviewed_at else None,
                    resolution_notes=a.resolution_notes,
                    created_at=ensure_utc(a.created_at),
                    action_details=act_details,
                )
            )

        return AppealListResponse(items=items, total=total, pending_count=pending_count)

    @staticmethod
    async def review_appeal(
        db: AsyncSession,
        appeal_id: uuid.UUID,
        decision: str,
        resolution_notes: Optional[str],
        moderator: Account,
    ) -> AppealResponse:
        """
        Review an appeal:
        - APPROVE: Overturns the action, restores content or restores persona/account status.
        - REJECT: Upholds the original moderation penalty.
        """
        appeal_stmt = select(Appeal).where(Appeal.id == appeal_id)
        appeal = (await db.execute(appeal_stmt)).scalar_one_or_none()
        if not appeal:
            raise HTTPException(status_code=404, detail="Appeal not found")

        dec_upper = decision.upper().strip()
        now = utc_now()
        appeal.reviewed_by = moderator.id
        appeal.reviewed_at = now
        appeal.resolution_notes = resolution_notes

        action_stmt = select(ModerationAction).where(ModerationAction.id == appeal.moderation_action_id)
        action = (await db.execute(action_stmt)).scalar_one_or_none()

        if dec_upper == "APPROVE":
            appeal.status = AppealStatus.APPROVED
            # Overturn action if action exists
            if action:
                if action.action_type == ModerationActionType.POST_REMOVED:
                    if action.target_type == "POST":
                        p = (await db.execute(select(Post).where(Post.id == action.target_id))).scalar_one_or_none()
                        if p:
                            p.is_deleted = False
                            p.moderation_status = "PUBLISHED"
                    elif action.target_type == "STORY":
                        s = (await db.execute(select(Story).where(Story.id == action.target_id))).scalar_one_or_none()
                        if s:
                            s.is_deleted = False
                            s.moderation_status = "APPROVED"
                    elif action.target_type == "COMMENT":
                        c = (await db.execute(select(Comment).where(Comment.id == action.target_id))).scalar_one_or_none()
                        if c:
                            c.is_deleted = False
                            c.moderation_status = "PUBLISHED"
                elif action.action_type == ModerationActionType.PERSONA_SUSPENDED:
                    p = (await db.execute(select(Persona).where(Persona.id == action.target_id))).scalar_one_or_none()
                    if p:
                        p.is_active = True
                        p.is_discoverable = True
                elif action.action_type == ModerationActionType.ACCOUNT_BANNED:
                    # Look up account
                    p = (await db.execute(select(Persona).where(Persona.id == appeal.appellant_persona_id))).scalar_one_or_none()
                    if p:
                        acc = (await db.execute(select(Account).where(Account.id == p.account_id))).scalar_one_or_none()
                        if acc:
                            acc.status = AccountStatus.ACTIVE
                            p.is_active = True
        else:
            appeal.status = AppealStatus.REJECTED

        await db.commit()
        await db.refresh(appeal)

        # Audit log
        await TrustAndSafetyService.log_audit_event(
            db,
            actor_id=moderator.id,
            actor_type="MODERATOR",
            action=f"APPEAL_{dec_upper}",
            target_type="APPEAL",
            target_id=appeal.id,
            details={"decision": dec_upper, "notes": resolution_notes},
        )

        return AppealResponse(
            id=appeal.id,
            moderation_action_id=appeal.moderation_action_id,
            appellant_persona_id=appeal.appellant_persona_id,
            reason=appeal.reason,
            status=appeal.status.value if hasattr(appeal.status, "value") else str(appeal.status),
            reviewed_at=ensure_utc(appeal.reviewed_at),
            resolution_notes=appeal.resolution_notes,
            created_at=ensure_utc(appeal.created_at),
        )

    # --- 6. Invitation Management for Admins ---

    @staticmethod
    async def list_admin_invitations(
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> AdminInvitationListResponse:
        """List platform invitations with masked emails. Zero raw token exposure."""
        total = (await db.execute(select(func.count(Invitation.id)))).scalar() or 0

        stmt = (
            select(Invitation)
            .order_by(desc(Invitation.created_at))
            .limit(limit)
            .offset(offset)
        )
        invites = (await db.execute(stmt)).scalars().all()

        items: List[AdminInvitationItem] = []
        for inv in invites:
            # Inviter persona name if available
            p_name = None
            if inv.inviter_account_id:
                p_res = await db.execute(
                    select(Persona.display_name).where(Persona.account_id == inv.inviter_account_id)
                )
                p_name = p_res.scalars().first()

            items.append(
                AdminInvitationItem(
                    id=inv.id,
                    inviter_persona_name=p_name or "Founding Member",
                    recipient_email_masked=mask_email(inv.recipient_email_hint or "user@campus.edu"),
                    status=inv.status.value if hasattr(inv.status, "value") else str(inv.status),
                    created_at=ensure_utc(inv.created_at),
                    expires_at=ensure_utc(inv.expires_at),
                    redeemed_at=ensure_utc(inv.redeemed_at) if inv.redeemed_at else None,
                )
            )

        return AdminInvitationListResponse(items=items, total=total)

    @staticmethod
    async def admin_revoke_invitation(
        db: AsyncSession,
        invitation_id: uuid.UUID,
        admin: Account,
    ) -> Dict[str, Any]:
        """Security admin revocation of suspicious invitations."""
        stmt = select(Invitation).where(Invitation.id == invitation_id)
        inv = (await db.execute(stmt)).scalar_one_or_none()
        if not inv:
            raise HTTPException(status_code=404, detail="Invitation not found")

        if inv.status == InvitationStatus.USED:
            raise HTTPException(status_code=400, detail="Cannot revoke an already redeemed invitation")

        inv.status = InvitationStatus.REVOKED
        await db.commit()

        await TrustAndSafetyService.log_audit_event(
            db,
            actor_id=admin.id,
            actor_type="SECURITY_ADMIN",
            action="INVITATION_REVOKED_BY_ADMIN",
            target_type="INVITATION",
            target_id=inv.id,
        )

        return {"id": str(inv.id), "status": "REVOKED"}

    # --- 7. Account Standing (Zero Identity Vault Leakage) ---

    @staticmethod
    async def list_admin_accounts(
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> AdminAccountListResponse:
        """
        Inspect account standing and compliance metrics.
        STRICT ZERO IDENTITY LEAKAGE: Never returns raw emails, email hashes, or Supabase UUIDs.
        """
        total = (await db.execute(select(func.count(Account.id)))).scalar() or 0

        stmt = (
            select(Account)
            .options(selectinload(Account.personas))
            .order_by(desc(Account.created_at))
            .limit(limit)
            .offset(offset)
        )
        accounts = (await db.execute(stmt)).scalars().all()

        items: List[AdminAccountItem] = []
        for acc in accounts:
            persona_names = [p.display_name for p in acc.personas]

            # Calculate total strikes
            strikes = 0
            if acc.personas:
                p_ids = [p.id for p in acc.personas]
                strikes_res = await db.execute(
                    select(func.coalesce(func.sum(ModerationAction.strike_count), 0)).where(
                        ModerationAction.target_persona_id.in_(p_ids)
                    )
                )
                strikes = int(strikes_res.scalar() or 0)

            items.append(
                AdminAccountItem(
                    id=acc.id,
                    status=acc.status.value if hasattr(acc.status, "value") else str(acc.status),
                    role=acc.role,
                    personas_count=len(acc.personas),
                    persona_display_names=persona_names,
                    invite_quota=acc.invite_quota,
                    is_age_verified=acc.is_age_verified,
                    strike_count=strikes,
                    created_at=ensure_utc(acc.created_at),
                )
            )

        return AdminAccountListResponse(items=items, total=total)

    # --- 8. Immutable Audit Logs ---

    @staticmethod
    async def list_audit_logs(
        db: AsyncSession,
        action_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditLogListResponse:
        """Query immutable security audit log journal."""
        conditions = []
        if action_filter and action_filter.upper() != "ALL":
            conditions.append(AuditLog.action.ilike(f"%{action_filter.strip()}%"))

        total = (
            await db.execute(select(func.count(AuditLog.id)).where(*conditions))
        ).scalar() or 0

        stmt = (
            select(AuditLog)
            .where(*conditions)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        logs = (await db.execute(stmt)).scalars().all()

        items = [
            AuditLogItem(
                id=log.id,
                actor_type=log.actor_type,
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                ip_hash=log.ip_hash[:16] + "..." if log.ip_hash else None,
                details=log.details_json,
                created_at=ensure_utc(log.created_at),
            )
            for log in logs
        ]

        return AuditLogListResponse(items=items, total=total)

    # --- 9. User Safety: Block Management & Account Deletion ---

    @staticmethod
    async def list_my_blocks(
        db: AsyncSession,
        current_persona: Persona,
    ) -> List[BlockedPersonaItem]:
        """User safety: View active blocks initiated by caller."""
        stmt = (
            select(Block, Persona)
            .join(Persona, Persona.id == Block.blocked_persona_id)
            .where(Block.blocker_persona_id == current_persona.id)
            .order_by(desc(Block.created_at))
        )
        rows = (await db.execute(stmt)).all()

        return [
            BlockedPersonaItem(
                persona_id=p.id,
                display_name=p.display_name,
                avatar_seed=p.avatar_seed,
                reason=b.reason,
                blocked_at=ensure_utc(b.created_at),
            )
            for b, p in rows
        ]

    @staticmethod
    async def delete_user_account(
        db: AsyncSession,
        account: Account,
    ) -> Dict[str, str]:
        """
        User safety: Self-service permanent account deletion.
        Cascades deletion across personas, posts, comments, stories, and blocks.
        Logs an anonymized audit record without storing identifiable data.
        """
        account_id = account.id

        # Revoke all unredeemed sent invitations
        inv_stmt = select(Invitation).where(
            and_(
                Invitation.inviter_account_id == account_id,
                Invitation.status != InvitationStatus.USED,
            )
        )
        for inv in (await db.execute(inv_stmt)).scalars().all():
            inv.status = InvitationStatus.REVOKED

        # Soft/Hard delete account records
        account.status = AccountStatus.BANNED
        account.invite_quota = 0

        # Deactivate all personas
        all_p = (await db.execute(select(Persona).where(Persona.account_id == account_id))).scalars().all()
        for p in all_p:
            p.is_active = False
            p.is_discoverable = False
            # Soft delete posts and stories
            await db.execute(
                Post.__table__.update().where(Post.persona_id == p.id).values(is_deleted=True)
            )
            await db.execute(
                Story.__table__.update().where(Story.persona_id == p.id).values(is_deleted=True)
            )

        await db.commit()

        # Immutable audit log
        await TrustAndSafetyService.log_audit_event(
            db,
            actor_id=None,
            actor_type="ACCOUNT",
            action="ACCOUNT_DELETED_BY_USER",
            target_type="ACCOUNT",
            target_id=account_id,
        )

        return {"status": "DELETED", "message": "Your account and all associated personas have been permanently removed."}

    # --- 10. Admin MFA Setup & Verification ---

    @staticmethod
    async def setup_admin_mfa(
        db: AsyncSession,
        account: Account,
    ) -> MfaSetupResponse:
        """Generate a new RFC 6238 Base32 secret for admin MFA."""
        secret = generate_mfa_secret()
        account.mfa_secret = secret
        await db.commit()

        otpauth = f"otpauth://totp/AFTR-Admin:admin?secret={secret}&issuer=AFTR"
        return MfaSetupResponse(
            secret=secret,
            otpauth_url=otpauth,
            instruction="Import the secret into Google Authenticator or your MFA app, then verify with a 6-digit code.",
        )

    @staticmethod
    async def verify_and_enable_mfa(
        db: AsyncSession,
        account: Account,
        code: str,
    ) -> Dict[str, Any]:
        """Verify code and activate MFA for administrator."""
        if not account.mfa_secret:
            raise HTTPException(status_code=400, detail="MFA setup has not been initiated. Call /admin/mfa/setup first.")

        if not verify_totp(account.mfa_secret, code):
            raise HTTPException(status_code=400, detail="Invalid 6-digit verification code.")

        account.mfa_enabled = True
        await db.commit()

        await TrustAndSafetyService.log_audit_event(
            db,
            actor_id=account.id,
            actor_type="ADMIN",
            action="MFA_ENABLED",
            target_type="ACCOUNT",
            target_id=account.id,
        )

        return {"status": "MFA_ENABLED", "mfa_enabled": True}
