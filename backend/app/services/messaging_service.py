import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple, Set
from fastapi import HTTPException, status
from sqlalchemy import select, or_, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.persona import Persona, CampusAffiliation
from backend.app.models.connection import (
    Conversation,
    ConversationParticipant,
    Message,
)
from backend.app.models.moderation import Block
from backend.app.models.base import utc_now
from backend.app.core.encryption import encrypt_message_content, decrypt_message_content
from backend.app.core.pagination import encode_cursor, decode_cursor
from backend.app.core.websocket_manager import ws_manager
from backend.app.schemas.messaging import (
    MessageResponse,
    MessagesPageResponse,
    ConversationParticipantPublic,
    ConversationSummaryResponse,
    ConversationDetailResponse,
    UnreadCountResponse,
)
from backend.app.services.social_service import SocialService

logger = logging.getLogger("aftr.messaging")


class MessagingService:
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
    async def ensure_participant_pseudonyms(
        db: AsyncSession, conversation_id: uuid.UUID
    ) -> Dict[uuid.UUID, str]:
        """
        Ensure all participants in conversation have a conversation-specific pseudonym.
        Returns a mapping of persona_id -> conversation_pseudonym.
        """
        stmt = (
            select(ConversationParticipant)
            .options(selectinload(ConversationParticipant.persona))
            .where(ConversationParticipant.conversation_id == conversation_id)
        )
        participants = list((await db.execute(stmt)).scalars().all())

        pseudonyms: Dict[uuid.UUID, str] = {}
        dirty = False
        for i, part in enumerate(participants, 1):
            if not part.conversation_pseudonym:
                # Assign a conversation-specific alias
                alias_prefix = "Echo" if i % 2 == 1 else "Shadow"
                part.conversation_pseudonym = f"{alias_prefix}-{part.id.hex[:4].upper()}"
                dirty = True
            pseudonyms[part.persona_id] = part.conversation_pseudonym

        if dirty:
            await db.commit()

        return pseudonyms

    @staticmethod
    async def verify_membership(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        persona_id: uuid.UUID,
    ) -> ConversationParticipant:
        """
        Verify that persona is an active participant in conversation.
        Raises 403 Forbidden if not authorized.
        """
        stmt = select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.persona_id == persona_id,
        )
        part = (await db.execute(stmt)).scalar_one_or_none()
        if not part:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this conversation.",
            )
        return part

    @staticmethod
    async def list_conversations(
        db: AsyncSession,
        current_persona: Persona,
    ) -> List[ConversationSummaryResponse]:
        """
        List all conversations where caller is a participant.
        Calculates conversation-specific pseudonyms, unread count, and last message preview.
        """
        # Find all conversation IDs where caller is participant
        my_parts_stmt = select(ConversationParticipant).where(
            ConversationParticipant.persona_id == current_persona.id
        )
        my_parts = list((await db.execute(my_parts_stmt)).scalars().all())
        if not my_parts:
            return []

        my_part_map = {p.conversation_id: p for p in my_parts}
        conv_ids = list(my_part_map.keys())

        # Bilateral blocked personas
        blocked_ids = await SocialService.get_blocked_persona_ids(db, current_persona.id)

        # Fetch conversations with participants and other personas
        convs_stmt = (
            select(Conversation)
            .options(
                selectinload(Conversation.participants).selectinload(ConversationParticipant.persona)
            )
            .where(Conversation.id.in_(conv_ids))
            .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.created_at.desc())
        )
        conversations = list((await db.execute(convs_stmt)).scalars().all())

        summaries: List[ConversationSummaryResponse] = []
        for conv in conversations:
            my_part = my_part_map.get(conv.id)
            if not my_part:
                continue

            # Identify the other participant
            other_part = next((p for p in conv.participants if p.persona_id != current_persona.id), None)
            if not other_part or not other_part.persona:
                continue

            other_persona = other_part.persona
            is_blocked = (
                conv.blocked_by_persona_id is not None
                or other_persona.id in blocked_ids
            )

            # Ensure pseudonyms are set
            my_pseudonym = my_part.conversation_pseudonym or f"Echo-{my_part.id.hex[:4].upper()}"
            other_pseudonym = other_part.conversation_pseudonym or f"Shadow-{other_part.id.hex[:4].upper()}"

            # Calculate unread messages
            last_read = my_part.last_read_at or datetime(1970, 1, 1, tzinfo=timezone.utc)
            unread_stmt = select(func.count(Message.id)).where(
                Message.conversation_id == conv.id,
                Message.sender_persona_id != current_persona.id,
                Message.is_deleted == False,
                Message.created_at > last_read,
            )
            unread_count = (await db.execute(unread_stmt)).scalar() or 0

            # Get latest message preview
            last_msg_stmt = (
                select(Message)
                .where(Message.conversation_id == conv.id)
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            last_msg = (await db.execute(last_msg_stmt)).scalar_one_or_none()

            last_preview = None
            if last_msg:
                if last_msg.is_deleted:
                    last_preview = "[Message deleted]"
                elif last_msg.is_encrypted:
                    plain = decrypt_message_content(last_msg.content)
                    last_preview = plain[:50] + ("..." if len(plain) > 50 else "")
                else:
                    last_preview = last_msg.content[:50] + ("..." if len(last_msg.content) > 50 else "")

            other_campus = await MessagingService.get_declared_campus(db, other_persona.id)
            is_online = ws_manager.is_persona_online(conv.id, other_persona.id)

            summaries.append(
                ConversationSummaryResponse(
                    id=conv.id,
                    other_participant=ConversationParticipantPublic(
                        persona_id=other_persona.id,
                        conversation_pseudonym=other_pseudonym,
                        display_name=other_persona.display_name,
                        avatar_seed=other_persona.avatar_seed,
                        declared_campus=other_campus,
                        is_online=is_online,
                    ),
                    my_conversation_pseudonym=my_pseudonym,
                    last_message_preview=last_preview,
                    last_message_at=conv.last_message_at or conv.created_at,
                    unread_count=unread_count,
                    is_active=conv.is_active and not is_blocked,
                    is_blocked=is_blocked,
                    created_at=conv.created_at,
                )
            )

        return summaries

    @staticmethod
    async def get_conversation_detail(
        db: AsyncSession,
        current_persona: Persona,
        conversation_id: uuid.UUID,
    ) -> ConversationDetailResponse:
        """Fetch detail of a single conversation, verifying membership."""
        my_part = await MessagingService.verify_membership(db, conversation_id, current_persona.id)
        conv = await db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        # Ensure pseudonyms
        pseudonyms = await MessagingService.ensure_participant_pseudonyms(db, conversation_id)

        stmt = (
            select(ConversationParticipant)
            .options(selectinload(ConversationParticipant.persona))
            .where(ConversationParticipant.conversation_id == conversation_id)
        )
        participants = list((await db.execute(stmt)).scalars().all())

        blocked_ids = await SocialService.get_blocked_persona_ids(db, current_persona.id)
        is_blocked = conv.blocked_by_persona_id is not None

        pub_parts: List[ConversationParticipantPublic] = []
        for p in participants:
            if not p.persona:
                continue
            if p.persona_id in blocked_ids:
                is_blocked = True
            campus = await MessagingService.get_declared_campus(db, p.persona.id)
            pub_parts.append(
                ConversationParticipantPublic(
                    persona_id=p.persona.id,
                    conversation_pseudonym=pseudonyms.get(p.persona_id, "Anonymous"),
                    display_name=p.persona.display_name,
                    avatar_seed=p.persona.avatar_seed,
                    declared_campus=campus,
                    is_online=ws_manager.is_persona_online(conversation_id, p.persona.id),
                )
            )

        my_pseudo = pseudonyms.get(current_persona.id, "Me")

        return ConversationDetailResponse(
            id=conv.id,
            participants=pub_parts,
            my_conversation_pseudonym=my_pseudo,
            is_active=conv.is_active and not is_blocked,
            is_blocked=is_blocked,
            created_at=conv.created_at,
        )

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        current_persona: Persona,
        conversation_id: uuid.UUID,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> MessagesPageResponse:
        """
        Fetch decrypted messages in chronological page.
        Verifies conversation membership on every request.
        """
        await MessagingService.verify_membership(db, conversation_id, current_persona.id)
        pseudonyms = await MessagingService.ensure_participant_pseudonyms(db, conversation_id)

        conditions = [Message.conversation_id == conversation_id]
        if cursor:
            cursor_data = decode_cursor(cursor)
            if cursor_data:
                dt, item_id = cursor_data
                conditions.append(
                    or_(
                        Message.created_at < dt,
                        and_(Message.created_at == dt, Message.id < item_id),
                    )
                )

        stmt = (
            select(Message)
            .where(*conditions)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit + 1)
        )
        msgs = list((await db.execute(stmt)).scalars().all())

        has_more = len(msgs) > limit
        if has_more:
            msgs = msgs[:limit]

        # Reverse so they read chronologically (oldest to newest)
        msgs.reverse()

        items: List[MessageResponse] = []
        for m in msgs:
            is_mine = m.sender_persona_id == current_persona.id
            if m.is_deleted:
                content = "[This message was deleted]"
            elif m.is_encrypted:
                content = decrypt_message_content(m.content)
            else:
                content = m.content

            pseudo = pseudonyms.get(m.sender_persona_id, "Anonymous")

            items.append(
                MessageResponse(
                    id=m.id,
                    conversation_id=m.conversation_id,
                    sender_persona_id=m.sender_persona_id,
                    sender_pseudonym=pseudo,
                    content=content,
                    is_mine=is_mine,
                    is_deleted=m.is_deleted,
                    created_at=m.created_at,
                )
            )

        next_cursor = None
        if has_more and msgs:
            # First item in chronologically reversed list was oldest in fetched slice
            oldest = msgs[0]
            next_cursor = encode_cursor(oldest.created_at, oldest.id)

        return MessagesPageResponse(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    @staticmethod
    async def send_message(
        db: AsyncSession,
        current_persona: Persona,
        conversation_id: uuid.UUID,
        content: str,
    ) -> MessageResponse:
        """
        Send a private message:
        - Verifies conversation membership
        - Verifies conversation is active and not blocked
        - Encrypts message content at rest
        - Updates conversation last_message_at
        - Broadcasts realtime event via WebSocket connection manager
        - NEVER logs message content
        """
        my_part = await MessagingService.verify_membership(db, conversation_id, current_persona.id)

        conv = await db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )

        if conv.blocked_by_persona_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Messaging is disabled because a participant has blocked this conversation.",
            )

        # Bilateral block check
        blocked_ids = await SocialService.get_blocked_persona_ids(db, current_persona.id)
        stmt_other = select(ConversationParticipant.persona_id).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.persona_id != current_persona.id,
        )
        other_id = (await db.execute(stmt_other)).scalar_one_or_none()
        if other_id and other_id in blocked_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Messaging is blocked between participants.",
            )

        if not conv.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This conversation is closed.",
            )

        pseudonyms = await MessagingService.ensure_participant_pseudonyms(db, conversation_id)
        my_pseudonym = pseudonyms.get(current_persona.id, "Anonymous")

        # Encrypt content before DB persistence
        encrypted = encrypt_message_content(content)
        msg = Message(
            conversation_id=conversation_id,
            sender_persona_id=current_persona.id,
            content=encrypted,
            is_encrypted=True,
            is_deleted=False,
        )
        db.add(msg)

        now = utc_now()
        conv.last_message_at = now
        my_part.last_read_at = now

        await db.commit()
        await db.refresh(msg)

        # Audit log metadata only - ZERO content logging
        logger.info(
            "Private message sent: conv_id=%s, sender_persona=%s, msg_id=%s",
            conversation_id,
            current_persona.id,
            msg.id,
        )

        res = MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender_persona_id=msg.sender_persona_id,
            sender_pseudonym=my_pseudonym,
            content=content,
            is_mine=True,
            is_deleted=False,
            created_at=msg.created_at,
        )

        # Broadcast real-time message via WebSockets
        broadcast_payload = {
            "type": "new_message",
            "message": {
                "id": str(res.id),
                "conversation_id": str(res.conversation_id),
                "sender_persona_id": str(res.sender_persona_id),
                "sender_pseudonym": res.sender_pseudonym,
                "content": content,
                "is_deleted": False,
                "created_at": res.created_at.isoformat(),
            },
        }
        await ws_manager.broadcast_to_conversation(conversation_id, broadcast_payload)

        return res

    @staticmethod
    async def delete_message(
        db: AsyncSession,
        current_persona: Persona,
        message_id: uuid.UUID,
    ) -> MessageResponse:
        """
        Delete a message:
        - Verifies caller is the author of the message
        - Soft deletes record
        - Broadcasts deletion event via WebSockets
        """
        msg = await db.get(Message, message_id)
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found.")

        # Membership & ownership check
        await MessagingService.verify_membership(db, msg.conversation_id, current_persona.id)

        if msg.sender_persona_id != current_persona.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own messages.",
            )

        if msg.is_deleted:
            # Already deleted
            pass
        else:
            msg.is_deleted = True
            msg.deleted_at = utc_now()
            msg.content = encrypt_message_content("[Deleted]")
            await db.commit()
            await db.refresh(msg)

        pseudonyms = await MessagingService.ensure_participant_pseudonyms(db, msg.conversation_id)

        # Broadcast deletion
        await ws_manager.broadcast_to_conversation(
            msg.conversation_id,
            {"type": "message_deleted", "message_id": str(msg.id)},
        )

        return MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender_persona_id=msg.sender_persona_id,
            sender_pseudonym=pseudonyms.get(msg.sender_persona_id, "Anonymous"),
            content="[This message was deleted]",
            is_mine=True,
            is_deleted=True,
            created_at=msg.created_at,
        )

    @staticmethod
    async def block_conversation(
        db: AsyncSession,
        current_persona: Persona,
        conversation_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Block a conversation and its participants:
        - Verifies membership
        - Inserts Block record
        - Closes conversation
        - Broadcasts blocked event to WebSockets
        """
        await MessagingService.verify_membership(db, conversation_id, current_persona.id)
        conv = await db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        stmt_other = select(ConversationParticipant.persona_id).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.persona_id != current_persona.id,
        )
        other_id = (await db.execute(stmt_other)).scalar_one_or_none()

        if other_id:
            # Create block if not exists
            blk_stmt = select(Block).where(
                Block.blocker_persona_id == current_persona.id,
                Block.blocked_persona_id == other_id,
            )
            existing_block = (await db.execute(blk_stmt)).scalar_one_or_none()
            if not existing_block:
                block = Block(
                    blocker_persona_id=current_persona.id,
                    blocked_persona_id=other_id,
                    reason=reason or "Blocked from conversation",
                )
                db.add(block)

        conv.is_active = False
        conv.blocked_by_persona_id = current_persona.id
        await db.commit()

        await ws_manager.broadcast_to_conversation(
            conversation_id,
            {"type": "conversation_blocked", "blocked_by": str(current_persona.id)},
        )

        return {"status": "BLOCKED", "conversation_id": str(conversation_id)}

    @staticmethod
    async def mark_as_read(
        db: AsyncSession,
        current_persona: Persona,
        conversation_id: uuid.UUID,
    ) -> Dict[str, str]:
        """Update last_read_at timestamp for caller in this conversation."""
        my_part = await MessagingService.verify_membership(db, conversation_id, current_persona.id)
        my_part.last_read_at = utc_now()
        await db.commit()
        return {"status": "READ", "conversation_id": str(conversation_id)}

    @staticmethod
    async def get_unread_counts(
        db: AsyncSession,
        current_persona: Persona,
    ) -> UnreadCountResponse:
        """Calculate total unread messages and unread conversations count."""
        parts_stmt = select(ConversationParticipant).where(
            ConversationParticipant.persona_id == current_persona.id
        )
        my_parts = list((await db.execute(parts_stmt)).scalars().all())

        total_unread = 0
        unread_convs = 0

        for part in my_parts:
            last_read = part.last_read_at or datetime(1970, 1, 1, tzinfo=timezone.utc)
            stmt = select(func.count(Message.id)).where(
                Message.conversation_id == part.conversation_id,
                Message.sender_persona_id != current_persona.id,
                Message.is_deleted == False,
                Message.created_at > last_read,
            )
            cnt = (await db.execute(stmt)).scalar() or 0
            if cnt > 0:
                total_unread += cnt
                unread_convs += 1

        return UnreadCountResponse(
            total_unread_messages=total_unread,
            unread_conversations_count=unread_convs,
        )
