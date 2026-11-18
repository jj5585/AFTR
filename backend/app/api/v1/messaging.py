import json
import uuid
import logging
from typing import Optional, List, Dict
from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_persona, decode_supabase_jwt
from backend.app.core.websocket_manager import ws_manager
from backend.app.models.account import Account, AccountStatus
from backend.app.models.persona import Persona
from backend.app.models.connection import Conversation, ConversationParticipant
from backend.app.schemas.messaging import (
    MessageCreateRequest,
    MessageResponse,
    MessagesPageResponse,
    ConversationSummaryResponse,
    ConversationDetailResponse,
    UnreadCountResponse,
)
from backend.app.services.messaging_service import MessagingService
from backend.app.services.social_service import SocialService

logger = logging.getLogger("aftr.messaging.api")

router = APIRouter(tags=["Messaging"])


@router.get(
    "/conversations",
    response_model=List[ConversationSummaryResponse],
    summary="List caller's conversations",
)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Retrieve all conversations where caller is a participant."""
    return await MessagingService.list_conversations(db, current_persona)


@router.get(
    "/conversations/unread-count",
    response_model=UnreadCountResponse,
    summary="Get unread message and conversation counts",
)
async def get_unread_counts(
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Get total unread message count and number of unread conversations."""
    return await MessagingService.get_unread_counts(db, current_persona)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation detail",
)
async def get_conversation_detail(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Retrieve conversation participants, pseudonym mapping, and online status."""
    return await MessagingService.get_conversation_detail(db, current_persona, conversation_id)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessagesPageResponse,
    summary="Get conversation message history",
)
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    cursor: Optional[str] = Query(None, description="Keyset pagination cursor"),
    limit: int = Query(50, ge=1, le=100, description="Messages per page"),
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Fetch paginated message history. Verifies membership on every call."""
    return await MessagingService.get_messages(
        db=db,
        current_persona=current_persona,
        conversation_id=conversation_id,
        cursor=cursor,
        limit=limit,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a private message",
)
async def send_private_message(
    conversation_id: uuid.UUID,
    body: MessageCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Send an encrypted message and broadcast to the realtime conversation channel."""
    return await MessagingService.send_message(
        db=db,
        current_persona=current_persona,
        conversation_id=conversation_id,
        content=body.content,
    )


@router.delete(
    "/messages/{message_id}",
    response_model=MessageResponse,
    summary="Delete a message",
)
async def delete_message(
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Delete own message with author authorization check."""
    return await MessagingService.delete_message(
        db=db,
        current_persona=current_persona,
        message_id=message_id,
    )


@router.post(
    "/conversations/{conversation_id}/block",
    summary="Block conversation and peer",
)
async def block_conversation(
    conversation_id: uuid.UUID,
    reason: Optional[str] = Query(None, description="Optional block reason"),
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Block the other participant, closing the conversation and disabling messaging."""
    return await MessagingService.block_conversation(
        db=db,
        current_persona=current_persona,
        conversation_id=conversation_id,
        reason=reason,
    )


@router.post(
    "/conversations/{conversation_id}/read",
    summary="Mark conversation as read",
)
async def mark_conversation_as_read(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_persona: Persona = Depends(get_current_persona),
):
    """Update last_read_at timestamp to reset unread message counter."""
    return await MessagingService.mark_as_read(
        db=db,
        current_persona=current_persona,
        conversation_id=conversation_id,
    )


# ==========================================
# Realtime Authorized WebSocket Endpoint
# ==========================================

@router.websocket("/ws/conversations/{conversation_id}")
async def websocket_conversation_endpoint(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    token: Optional[str] = Query(None, description="Supabase JWT bearer token"),
    db: AsyncSession = Depends(get_db),
):
    """
    Authorized WebSocket transport for private real-time messaging:
    - Verifies JWT token
    - Verifies conversation membership
    - Rejects unauthorized subscriptions
    - Broadcasts real-time events without logging contents
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return

    try:
        payload = decode_supabase_jwt(token)
        sub = payload.get("sub")
        if not sub:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
        user_uuid = uuid.UUID(sub)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    # Authenticate account & persona
    acc_stmt = select(Account).where(
        Account.supabase_user_id == user_uuid, Account.status == AccountStatus.ACTIVE
    )
    account = (await db.execute(acc_stmt)).scalar_one_or_none()
    if not account:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Account not active")
        return

    p_stmt = select(Persona).where(Persona.account_id == account.id, Persona.is_active == True)
    persona = (await db.execute(p_stmt)).scalar_one_or_none()
    if not persona:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="No active persona")
        return

    # STRICT MEMBERSHIP CHECK: Unauthorized subscriptions rejected immediately
    part_stmt = select(ConversationParticipant).where(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.persona_id == persona.id,
    )
    part = (await db.execute(part_stmt)).scalar_one_or_none()
    if not part:
        logger.warning(
            "Unauthorized WebSocket connection attempt: conv_id=%s, persona_id=%s",
            conversation_id,
            persona.id,
        )
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized subscription")
        return

    # Check conversation active & not blocked
    conv = await db.get(Conversation, conversation_id)
    if not conv or not conv.is_active or conv.blocked_by_persona_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Conversation closed or blocked")
        return

    blocked_ids = await SocialService.get_blocked_persona_ids(db, persona.id)
    stmt_other = select(ConversationParticipant.persona_id).where(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.persona_id != persona.id,
    )
    other_id = (await db.execute(stmt_other)).scalar_one_or_none()
    if other_id and other_id in blocked_ids:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Participants blocked")
        return

    # Accept connection & register in connection manager
    await ws_manager.connect(websocket, conversation_id, persona.id)

    # Broadcast user online status
    await ws_manager.broadcast_to_conversation(
        conversation_id,
        {"type": "user_status", "persona_id": str(persona.id), "is_online": True},
        exclude_socket=websocket,
    )

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                frame = json.loads(raw_text)
            except Exception:
                continue

            frame_type = frame.get("type")
            if frame_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif frame_type == "typing":
                is_typing = bool(frame.get("is_typing", False))
                await ws_manager.broadcast_to_conversation(
                    conversation_id,
                    {"type": "typing", "persona_id": str(persona.id), "is_typing": is_typing},
                    exclude_socket=websocket,
                )
            elif frame_type == "message":
                content = str(frame.get("content", "")).strip()
                if content:
                    await MessagingService.send_message(db, persona, conversation_id, content)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
    finally:
        await ws_manager.disconnect(websocket, conversation_id)
        await ws_manager.broadcast_to_conversation(
            conversation_id,
            {"type": "user_status", "persona_id": str(persona.id), "is_online": False},
        )
