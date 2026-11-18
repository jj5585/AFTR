import json
import uuid
from typing import Optional, List, Set, Tuple, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy import select, or_, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.persona import Persona, CampusAffiliation, Interest, PersonaInterest
from backend.app.models.base import utc_now
from backend.app.models.connection import (
    ConnectionRequest,
    ConnectionRequestStatus,
    Match,
    Conversation,
    ConversationParticipant,
    Message,
)
from backend.app.core.encryption import encrypt_message_content
from backend.app.core.pagination import encode_cursor, decode_cursor
from backend.app.schemas.social import PersonaPublicResponse
from backend.app.schemas.discovery import (
    InterestResponse,
    DiscoveryPreferencesUpdateRequest,
    DiscoveryPreferencesResponse,
    DiscoveryCardResponse,
    DiscoveryFeedResponse,
    ConnectionRequestResponse,
    ConnectionRequestsListResponse,
    MatchResponse,
    MatchesListResponse,
)
from backend.app.services.social_service import SocialService

# Seed interests taxonomy for campus adult communities
DEFAULT_INTERESTS = [
    {"name": "Night Owl", "slug": "night-owl", "is_adult": True},
    {"name": "Late Talks", "slug": "late-talks", "is_adult": True},
    {"name": "Study Partner", "slug": "study-partner", "is_adult": False},
    {"name": "Fitness & Gym", "slug": "fitness-gym", "is_adult": False},
    {"name": "Deep Convos", "slug": "deep-convos", "is_adult": True},
    {"name": "Gamer", "slug": "gamer", "is_adult": False},
    {"name": "Music & Concerts", "slug": "music-concerts", "is_adult": False},
    {"name": "Creative Arts", "slug": "creative-arts", "is_adult": False},
    {"name": "Casual Vibe", "slug": "casual-vibe", "is_adult": True},
    {"name": "Coffee Breaks", "slug": "coffee-breaks", "is_adult": False},
    {"name": "Outdoor Adventures", "slug": "outdoor-adventures", "is_adult": False},
    {"name": "Foodie Trips", "slug": "foodie-trips", "is_adult": False},
]


class DiscoveryService:
    @staticmethod
    async def get_or_seed_interests(db: AsyncSession) -> List[InterestResponse]:
        """Fetch all interests taxonomy, seeding default tags if empty."""
        stmt = select(Interest).order_by(Interest.name.asc())
        result = await db.execute(stmt)
        interests = list(result.scalars().all())

        if not interests:
            new_interests = []
            for item in DEFAULT_INTERESTS:
                inst = Interest(name=item["name"], slug=item["slug"], is_adult=item["is_adult"])
                db.add(inst)
                new_interests.append(inst)
            await db.commit()
            for inst in new_interests:
                await db.refresh(inst)
            interests = new_interests

        return [
            InterestResponse(
                id=i.id,
                name=i.name,
                slug=i.slug,
                is_adult=i.is_adult,
            )
            for i in interests
        ]

    @staticmethod
    async def get_declared_campus(db: AsyncSession, persona_id: uuid.UUID) -> Optional[str]:
        """Get primary declared campus for a persona."""
        stmt = (
            select(CampusAffiliation.campus_name)
            .where(CampusAffiliation.persona_id == persona_id)
            .order_by(CampusAffiliation.is_primary.desc())
            .limit(1)
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def get_my_preferences(
        db: AsyncSession, current_persona: Persona
    ) -> DiscoveryPreferencesResponse:
        """Get discovery preferences and selected interests for the caller."""
        # Query caller's selected interests
        stmt = (
            select(Interest)
            .join(PersonaInterest, PersonaInterest.interest_id == Interest.id)
            .where(PersonaInterest.persona_id == current_persona.id)
        )
        interests = list((await db.execute(stmt)).scalars().all())

        dating_prefs = None
        if current_persona.dating_preferences_json:
            try:
                dating_prefs = json.loads(current_persona.dating_preferences_json)
            except Exception:
                dating_prefs = None

        return DiscoveryPreferencesResponse(
            is_discoverable=current_persona.is_discoverable,
            relationship_intention=current_persona.relationship_intention,
            min_age_preference=current_persona.min_age_preference,
            max_age_preference=current_persona.max_age_preference,
            dating_preferences=dating_prefs,
            interests=[
                InterestResponse(id=i.id, name=i.name, slug=i.slug, is_adult=i.is_adult)
                for i in interests
            ],
        )

    @staticmethod
    async def update_preferences(
        db: AsyncSession,
        current_persona: Persona,
        update_data: DiscoveryPreferencesUpdateRequest,
    ) -> DiscoveryPreferencesResponse:
        """Update discovery settings, intentions, and interests."""
        if update_data.is_discoverable is not None:
            current_persona.is_discoverable = update_data.is_discoverable
        if update_data.relationship_intention is not None:
            current_persona.relationship_intention = update_data.relationship_intention
        if update_data.min_age_preference is not None:
            current_persona.min_age_preference = update_data.min_age_preference
        if update_data.max_age_preference is not None:
            current_persona.max_age_preference = update_data.max_age_preference
        if update_data.dating_preferences is not None:
            current_persona.dating_preferences_json = json.dumps(update_data.dating_preferences)

        if update_data.interest_ids is not None:
            # Delete old interests
            await db.execute(
                delete(PersonaInterest).where(PersonaInterest.persona_id == current_persona.id)
            )
            # Add new selected interests
            for interest_id in update_data.interest_ids:
                # Verify interest exists
                chk = await db.get(Interest, interest_id)
                if chk:
                    db.add(PersonaInterest(persona_id=current_persona.id, interest_id=interest_id))

        await db.commit()
        await db.refresh(current_persona)

        return await DiscoveryService.get_my_preferences(db, current_persona)

    @staticmethod
    async def get_discovery_feed(
        db: AsyncSession,
        current_persona: Persona,
        cursor: Optional[str] = None,
        limit: int = 15,
        campus_filter: Optional[str] = None,
        intention_filter: Optional[str] = None,
    ) -> DiscoveryFeedResponse:
        """
        Fetch anonymous discovery cards matching preferences and filters.
        Enforces:
        - Opt-in discoverability (caller must be discoverable)
        - Bilateral block isolation
        - Zero identity leakage
        - Realistic compatibility score computation
        """
        if not current_persona.is_discoverable:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must opt into discoverability in your profile to view discovery cards.",
            )

        # Bilateral block isolation
        blocked_ids = await SocialService.get_blocked_persona_ids(db, current_persona.id)
        excluded_ids = blocked_ids | {current_persona.id}

        # Caller declared campus
        caller_campus = await DiscoveryService.get_declared_campus(db, current_persona.id)

        # Caller interests
        caller_interests_stmt = (
            select(Interest.name)
            .join(PersonaInterest, PersonaInterest.interest_id == Interest.id)
            .where(PersonaInterest.persona_id == current_persona.id)
        )
        caller_interest_names: Set[str] = set(
            (await db.execute(caller_interests_stmt)).scalars().all()
        )

        # Base candidate query
        conditions = [
            Persona.is_active == True,
            Persona.is_discoverable == True,
            Persona.id.not_in(excluded_ids),
        ]

        if intention_filter:
            conditions.append(Persona.relationship_intention == intention_filter)

        if cursor:
            cursor_data = decode_cursor(cursor)
            if cursor_data:
                dt, item_id = cursor_data
                conditions.append(
                    or_(
                        Persona.created_at < dt,
                        and_(Persona.created_at == dt, Persona.id < item_id),
                    )
                )

        stmt = (
            select(Persona)
            .where(*conditions)
            .order_by(Persona.created_at.desc(), Persona.id.desc())
            .limit(limit + 1)
        )
        candidates = list((await db.execute(stmt)).scalars().all())

        has_more = len(candidates) > limit
        if has_more:
            candidates = candidates[:limit]

        # Fetch active connection requests between caller and these candidates
        candidate_ids = [c.id for c in candidates]
        connection_status_map: Dict[uuid.UUID, Tuple[str, Optional[uuid.UUID]]] = {}

        if candidate_ids:
            req_stmt = select(ConnectionRequest).where(
                or_(
                    and_(
                        ConnectionRequest.sender_persona_id == current_persona.id,
                        ConnectionRequest.recipient_persona_id.in_(candidate_ids),
                    ),
                    and_(
                        ConnectionRequest.recipient_persona_id == current_persona.id,
                        ConnectionRequest.sender_persona_id.in_(candidate_ids),
                    ),
                )
            )
            req_results = (await db.execute(req_stmt)).scalars().all()
            for req in req_results:
                if req.status == ConnectionRequestStatus.PENDING:
                    if req.sender_persona_id == current_persona.id:
                        connection_status_map[req.recipient_persona_id] = ("PENDING_SENT", req.id)
                    else:
                        connection_status_map[req.sender_persona_id] = ("PENDING_RECEIVED", req.id)
                elif req.status == ConnectionRequestStatus.ACCEPTED:
                    other_id = (
                        req.recipient_persona_id
                        if req.sender_persona_id == current_persona.id
                        else req.sender_persona_id
                    )
                    connection_status_map[other_id] = ("ACCEPTED", req.id)
                elif req.status == ConnectionRequestStatus.REJECTED:
                    other_id = (
                        req.recipient_persona_id
                        if req.sender_persona_id == current_persona.id
                        else req.sender_persona_id
                    )
                    connection_status_map[other_id] = ("REJECTED", req.id)
                elif req.status == ConnectionRequestStatus.WITHDRAWN:
                    other_id = (
                        req.recipient_persona_id
                        if req.sender_persona_id == current_persona.id
                        else req.sender_persona_id
                    )
                    connection_status_map[other_id] = ("WITHDRAWN", req.id)

        items: List[DiscoveryCardResponse] = []
        for candidate in candidates:
            cand_campus = await DiscoveryService.get_declared_campus(db, candidate.id)

            if campus_filter and (not cand_campus or campus_filter.lower() not in cand_campus.lower()):
                continue

            # Candidate interests
            cand_interests_stmt = (
                select(Interest.name)
                .join(PersonaInterest, PersonaInterest.interest_id == Interest.id)
                .where(PersonaInterest.persona_id == candidate.id)
            )
            cand_interest_names: Set[str] = set(
                (await db.execute(cand_interests_stmt)).scalars().all()
            )

            mutual_interests = list(caller_interest_names & cand_interest_names)

            # Compatibility scoring
            base_score = 65.0
            interest_bonus = min(24.0, len(mutual_interests) * 8.0)
            intention_bonus = (
                10.0
                if (
                    candidate.relationship_intention
                    and current_persona.relationship_intention
                    and candidate.relationship_intention == current_persona.relationship_intention
                )
                else 0.0
            )
            campus_bonus = 5.0 if (caller_campus and cand_campus and caller_campus == cand_campus) else 0.0

            compatibility = min(99.0, max(50.0, base_score + interest_bonus + intention_bonus + campus_bonus))

            conn_status, req_id = connection_status_map.get(candidate.id, ("NONE", None))

            items.append(
                DiscoveryCardResponse(
                    persona=PersonaPublicResponse(
                        id=candidate.id,
                        display_name=candidate.display_name,
                        avatar_seed=candidate.avatar_seed,
                        declared_campus=cand_campus,
                        is_active=candidate.is_active,
                    ),
                    compatibility_score=round(compatibility, 1),
                    mutual_interests=mutual_interests,
                    relationship_intention=candidate.relationship_intention,
                    connection_status=conn_status,
                    connection_request_id=req_id,
                )
            )

        next_cursor = None
        if has_more and candidates:
            last = candidates[-1]
            next_cursor = encode_cursor(last.created_at, last.id)

        return DiscoveryFeedResponse(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    @staticmethod
    async def send_connection_request(
        db: AsyncSession,
        current_persona: Persona,
        recipient_persona_id: uuid.UUID,
        note: Optional[str] = None,
    ) -> ConnectionRequestResponse:
        """
        Send an anonymous connection request with optional polite intro note.
        Prevents self-connection, duplicates, and respects blocking.
        """
        if current_persona.id == recipient_persona_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send a connection request to yourself.",
            )

        # Bilateral block check
        blocked_ids = await SocialService.get_blocked_persona_ids(db, current_persona.id)
        if recipient_persona_id in blocked_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Action not permitted.",
            )

        # Recipient check
        recipient = await db.get(Persona, recipient_persona_id)
        if not recipient or not recipient.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target persona not found.",
            )
        if not recipient.is_discoverable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This persona is not currently discoverable.",
            )

        # Check existing requests between these two in either direction
        stmt = select(ConnectionRequest).where(
            or_(
                and_(
                    ConnectionRequest.sender_persona_id == current_persona.id,
                    ConnectionRequest.recipient_persona_id == recipient_persona_id,
                ),
                and_(
                    ConnectionRequest.sender_persona_id == recipient_persona_id,
                    ConnectionRequest.recipient_persona_id == current_persona.id,
                ),
            )
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            if existing.status == ConnectionRequestStatus.ACCEPTED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You are already connected with this persona.",
                )
            if existing.status == ConnectionRequestStatus.PENDING:
                if existing.sender_persona_id == current_persona.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="A connection request is already pending.",
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="This persona has already sent you a connection request. Please accept it.",
                    )
            if existing.sender_persona_id == current_persona.id and existing.status == ConnectionRequestStatus.WITHDRAWN:
                # Re-activate withdrawn request
                existing.status = ConnectionRequestStatus.PENDING
                existing.note = note
                await db.commit()
                await db.refresh(existing)
                req = existing
            elif existing.status == ConnectionRequestStatus.REJECTED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to send connection request to this persona.",
                )
            else:
                # If recipient previously withdrew or other state, update or recreate
                existing.sender_persona_id = current_persona.id
                existing.recipient_persona_id = recipient_persona_id
                existing.status = ConnectionRequestStatus.PENDING
                existing.note = note
                await db.commit()
                await db.refresh(existing)
                req = existing
        else:
            req = ConnectionRequest(
                sender_persona_id=current_persona.id,
                recipient_persona_id=recipient_persona_id,
                status=ConnectionRequestStatus.PENDING,
                note=note,
            )
            db.add(req)
            await db.commit()
            await db.refresh(req)

        sender_campus = await DiscoveryService.get_declared_campus(db, current_persona.id)
        recipient_campus = await DiscoveryService.get_declared_campus(db, recipient.id)

        return ConnectionRequestResponse(
            id=req.id,
            sender_persona=PersonaPublicResponse(
                id=current_persona.id,
                display_name=current_persona.display_name,
                avatar_seed=current_persona.avatar_seed,
                declared_campus=sender_campus,
                is_active=current_persona.is_active,
            ),
            recipient_persona=PersonaPublicResponse(
                id=recipient.id,
                display_name=recipient.display_name,
                avatar_seed=recipient.avatar_seed,
                declared_campus=recipient_campus,
                is_active=recipient.is_active,
            ),
            note=req.note,
            status=req.status.value,
            created_at=req.created_at,
        )

    @staticmethod
    async def accept_connection_request(
        db: AsyncSession,
        current_persona: Persona,
        request_id: uuid.UUID,
    ) -> Tuple[ConnectionRequestResponse, MatchResponse]:
        """
        Accept an incoming connection request:
        1. Set status to ACCEPTED
        2. Create canonical Match record
        3. Unlock bilateral Conversation and add ConversationParticipants
        """
        req = await db.get(ConnectionRequest, request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection request not found.",
            )

        if req.recipient_persona_id != current_persona.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to accept this connection request.",
            )

        if req.status != ConnectionRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot accept request with status '{req.status.value}'.",
            )

        sender = await db.get(Persona, req.sender_persona_id)
        if not sender or not sender.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sender persona is no longer active.",
            )

        # Bilateral block check
        blocked_ids = await SocialService.get_blocked_persona_ids(db, current_persona.id)
        if sender.id in blocked_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Action not permitted.",
            )

        # 1. Update request status
        req.status = ConnectionRequestStatus.ACCEPTED

        # 2. Canonical match pair (persona_a_id < persona_b_id)
        p_a = min(req.sender_persona_id, req.recipient_persona_id)
        p_b = max(req.sender_persona_id, req.recipient_persona_id)

        match_stmt = select(Match).where(
            Match.persona_a_id == p_a,
            Match.persona_b_id == p_b,
        )
        match = (await db.execute(match_stmt)).scalar_one_or_none()

        if not match:
            # Calculate match compatibility score
            match = Match(
                persona_a_id=p_a,
                persona_b_id=p_b,
                compatibility_score=85.0,
            )
            db.add(match)
            await db.flush()

        # 3. Create or unlock private Conversation
        conv_stmt = select(Conversation).where(
            or_(
                Conversation.connection_request_id == req.id,
                Conversation.match_id == match.id,
            )
        )
        conv = (await db.execute(conv_stmt)).scalar_one_or_none()

        if not conv:
            now_dt = utc_now()
            conv = Conversation(
                connection_request_id=req.id,
                match_id=match.id,
                is_active=True,
                last_message_at=now_dt if req.note else None,
            )
            db.add(conv)
            await db.flush()

            # Add participants with conversation-specific pseudonyms
            p1_pseudo = f"Echo-{req.sender_persona_id.hex[:4].upper()}"
            p2_pseudo = f"Shadow-{req.recipient_persona_id.hex[:4].upper()}"

            db.add(ConversationParticipant(
                conversation_id=conv.id,
                persona_id=req.sender_persona_id,
                conversation_pseudonym=p1_pseudo,
                last_read_at=now_dt if req.note else None,
            ))
            db.add(ConversationParticipant(
                conversation_id=conv.id,
                persona_id=req.recipient_persona_id,
                conversation_pseudonym=p2_pseudo,
                last_read_at=None,
            ))

            # If note was included in connection request, create first message from sender (encrypted)
            if req.note:
                encrypted_note = encrypt_message_content(req.note)
                db.add(
                    Message(
                        conversation_id=conv.id,
                        sender_persona_id=req.sender_persona_id,
                        content=encrypted_note,
                        is_encrypted=True,
                    )
                )

        await db.commit()
        await db.refresh(req)
        await db.refresh(match)

        sender_campus = await DiscoveryService.get_declared_campus(db, sender.id)
        recipient_campus = await DiscoveryService.get_declared_campus(db, current_persona.id)

        req_response = ConnectionRequestResponse(
            id=req.id,
            sender_persona=PersonaPublicResponse(
                id=sender.id,
                display_name=sender.display_name,
                avatar_seed=sender.avatar_seed,
                declared_campus=sender_campus,
                is_active=sender.is_active,
            ),
            recipient_persona=PersonaPublicResponse(
                id=current_persona.id,
                display_name=current_persona.display_name,
                avatar_seed=current_persona.avatar_seed,
                declared_campus=recipient_campus,
                is_active=current_persona.is_active,
            ),
            note=req.note,
            status=req.status.value,
            created_at=req.created_at,
        )

        match_response = MatchResponse(
            id=match.id,
            matched_persona=PersonaPublicResponse(
                id=sender.id,
                display_name=sender.display_name,
                avatar_seed=sender.avatar_seed,
                declared_campus=sender_campus,
                is_active=sender.is_active,
            ),
            compatibility_score=match.compatibility_score,
            conversation_id=conv.id,
            created_at=match.created_at,
        )

        return req_response, match_response

    @staticmethod
    async def reject_connection_request(
        db: AsyncSession,
        current_persona: Persona,
        request_id: uuid.UUID,
    ) -> ConnectionRequestResponse:
        """Reject an incoming connection request."""
        req = await db.get(ConnectionRequest, request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection request not found.",
            )

        if req.recipient_persona_id != current_persona.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to reject this connection request.",
            )

        if req.status != ConnectionRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject request with status '{req.status.value}'.",
            )

        req.status = ConnectionRequestStatus.REJECTED
        await db.commit()
        await db.refresh(req)

        sender = await db.get(Persona, req.sender_persona_id)
        sender_campus = await DiscoveryService.get_declared_campus(db, sender.id) if sender else None
        recipient_campus = await DiscoveryService.get_declared_campus(db, current_persona.id)

        return ConnectionRequestResponse(
            id=req.id,
            sender_persona=PersonaPublicResponse(
                id=sender.id if sender else req.sender_persona_id,
                display_name=sender.display_name if sender else "Anonymous",
                avatar_seed=sender.avatar_seed if sender else "seed",
                declared_campus=sender_campus,
                is_active=sender.is_active if sender else False,
            ),
            recipient_persona=PersonaPublicResponse(
                id=current_persona.id,
                display_name=current_persona.display_name,
                avatar_seed=current_persona.avatar_seed,
                declared_campus=recipient_campus,
                is_active=current_persona.is_active,
            ),
            note=req.note,
            status=req.status.value,
            created_at=req.created_at,
        )

    @staticmethod
    async def withdraw_connection_request(
        db: AsyncSession,
        current_persona: Persona,
        request_id: uuid.UUID,
    ) -> ConnectionRequestResponse:
        """Withdraw an outgoing pending connection request."""
        req = await db.get(ConnectionRequest, request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection request not found.",
            )

        if req.sender_persona_id != current_persona.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to withdraw this connection request.",
            )

        if req.status != ConnectionRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot withdraw request with status '{req.status.value}'.",
            )

        req.status = ConnectionRequestStatus.WITHDRAWN
        await db.commit()
        await db.refresh(req)

        recipient = await db.get(Persona, req.recipient_persona_id)
        sender_campus = await DiscoveryService.get_declared_campus(db, current_persona.id)
        recipient_campus = await DiscoveryService.get_declared_campus(db, recipient.id) if recipient else None

        return ConnectionRequestResponse(
            id=req.id,
            sender_persona=PersonaPublicResponse(
                id=current_persona.id,
                display_name=current_persona.display_name,
                avatar_seed=current_persona.avatar_seed,
                declared_campus=sender_campus,
                is_active=current_persona.is_active,
            ),
            recipient_persona=PersonaPublicResponse(
                id=recipient.id if recipient else req.recipient_persona_id,
                display_name=recipient.display_name if recipient else "Anonymous",
                avatar_seed=recipient.avatar_seed if recipient else "seed",
                declared_campus=recipient_campus,
                is_active=recipient.is_active if recipient else False,
            ),
            note=req.note,
            status=req.status.value,
            created_at=req.created_at,
        )

    @staticmethod
    async def get_connection_requests(
        db: AsyncSession,
        current_persona: Persona,
    ) -> ConnectionRequestsListResponse:
        """List incoming and outgoing pending connection requests."""
        blocked_ids = await SocialService.get_blocked_persona_ids(db, current_persona.id)

        # Incoming requests
        in_stmt = select(ConnectionRequest).where(
            ConnectionRequest.recipient_persona_id == current_persona.id,
            ConnectionRequest.status == ConnectionRequestStatus.PENDING,
        ).order_by(ConnectionRequest.created_at.desc())
        in_results = list((await db.execute(in_stmt)).scalars().all())

        # Outgoing requests
        out_stmt = select(ConnectionRequest).where(
            ConnectionRequest.sender_persona_id == current_persona.id,
            ConnectionRequest.status == ConnectionRequestStatus.PENDING,
        ).order_by(ConnectionRequest.created_at.desc())
        out_results = list((await db.execute(out_stmt)).scalars().all())

        curr_campus = await DiscoveryService.get_declared_campus(db, current_persona.id)

        incoming: List[ConnectionRequestResponse] = []
        for req in in_results:
            if req.sender_persona_id in blocked_ids:
                continue
            sender = await db.get(Persona, req.sender_persona_id)
            if not sender or not sender.is_active:
                continue
            sender_campus = await DiscoveryService.get_declared_campus(db, sender.id)
            incoming.append(
                ConnectionRequestResponse(
                    id=req.id,
                    sender_persona=PersonaPublicResponse(
                        id=sender.id,
                        display_name=sender.display_name,
                        avatar_seed=sender.avatar_seed,
                        declared_campus=sender_campus,
                        is_active=sender.is_active,
                    ),
                    recipient_persona=PersonaPublicResponse(
                        id=current_persona.id,
                        display_name=current_persona.display_name,
                        avatar_seed=current_persona.avatar_seed,
                        declared_campus=curr_campus,
                        is_active=current_persona.is_active,
                    ),
                    note=req.note,
                    status=req.status.value,
                    created_at=req.created_at,
                )
            )

        outgoing: List[ConnectionRequestResponse] = []
        for req in out_results:
            if req.recipient_persona_id in blocked_ids:
                continue
            recipient = await db.get(Persona, req.recipient_persona_id)
            if not recipient or not recipient.is_active:
                continue
            recipient_campus = await DiscoveryService.get_declared_campus(db, recipient.id)
            outgoing.append(
                ConnectionRequestResponse(
                    id=req.id,
                    sender_persona=PersonaPublicResponse(
                        id=current_persona.id,
                        display_name=current_persona.display_name,
                        avatar_seed=current_persona.avatar_seed,
                        declared_campus=curr_campus,
                        is_active=current_persona.is_active,
                    ),
                    recipient_persona=PersonaPublicResponse(
                        id=recipient.id,
                        display_name=recipient.display_name,
                        avatar_seed=recipient.avatar_seed,
                        declared_campus=recipient_campus,
                        is_active=recipient.is_active,
                    ),
                    note=req.note,
                    status=req.status.value,
                    created_at=req.created_at,
                )
            )

        return ConnectionRequestsListResponse(incoming=incoming, outgoing=outgoing)

    @staticmethod
    async def get_matches(
        db: AsyncSession,
        current_persona: Persona,
    ) -> MatchesListResponse:
        """List all mutual accepted matches for the current persona."""
        blocked_ids = await SocialService.get_blocked_persona_ids(db, current_persona.id)

        stmt = select(Match).where(
            or_(
                Match.persona_a_id == current_persona.id,
                Match.persona_b_id == current_persona.id,
            )
        ).order_by(Match.created_at.desc())
        matches = list((await db.execute(stmt)).scalars().all())

        results: List[MatchResponse] = []
        for match in matches:
            partner_id = (
                match.persona_b_id if match.persona_a_id == current_persona.id else match.persona_a_id
            )
            if partner_id in blocked_ids:
                continue

            partner = await db.get(Persona, partner_id)
            if not partner or not partner.is_active:
                continue

            partner_campus = await DiscoveryService.get_declared_campus(db, partner.id)

            # Find conversation_id if available
            conv_stmt = select(Conversation.id).where(Conversation.match_id == match.id)
            conv_id = (await db.execute(conv_stmt)).scalar_one_or_none()

            results.append(
                MatchResponse(
                    id=match.id,
                    matched_persona=PersonaPublicResponse(
                        id=partner.id,
                        display_name=partner.display_name,
                        avatar_seed=partner.avatar_seed,
                        declared_campus=partner_campus,
                        is_active=partner.is_active,
                    ),
                    compatibility_score=match.compatibility_score,
                    conversation_id=conv_id,
                    created_at=match.created_at,
                )
            )

        return MatchesListResponse(matches=results)
