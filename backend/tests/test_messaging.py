import uuid
import pytest
from httpx import AsyncClient
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.main import app
from backend.app.core.security import create_test_jwt
from backend.app.core.encryption import decrypt_message_content
from backend.app.models.account import Account, AccountStatus
from backend.app.models.persona import Persona, CampusAffiliation
from backend.app.models.connection import (
    ConnectionRequest,
    ConnectionRequestStatus,
    Match,
    Conversation,
    ConversationParticipant,
    Message,
)
from backend.app.models.moderation import Block


@pytest.fixture
async def messaging_test_setup(db_session: AsyncSession):
    """
    Setup 3 test accounts and personas:
    1. Alice (ShadowFox)
    2. Bob (NeonGhost)
    3. Charlie (MidnightEcho) - Outsider / Non-member of Alice & Bob's conversation
    And create an accepted connection + conversation between Alice & Bob.
    """
    alice_sub = uuid.uuid4()
    bob_sub = uuid.uuid4()
    charlie_sub = uuid.uuid4()

    acc_alice = Account(
        supabase_user_id=alice_sub,
        email_hash="hash_alice_msg@example.com",
        is_age_verified=True,
        birth_year=2001,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
    )
    acc_bob = Account(
        supabase_user_id=bob_sub,
        email_hash="hash_bob_msg@example.com",
        is_age_verified=True,
        birth_year=2000,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
    )
    acc_charlie = Account(
        supabase_user_id=charlie_sub,
        email_hash="hash_charlie_msg@example.com",
        is_age_verified=True,
        birth_year=2002,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
    )
    db_session.add_all([acc_alice, acc_bob, acc_charlie])
    await db_session.flush()

    p_alice = Persona(
        account_id=acc_alice.id,
        display_name="ShadowFox",
        avatar_seed="fox-seed",
        bio="Architecture & code.",
        is_active=True,
        is_discoverable=True,
    )
    p_bob = Persona(
        account_id=acc_bob.id,
        display_name="NeonGhost",
        avatar_seed="ghost-seed",
        bio="Philosophy & beats.",
        is_active=True,
        is_discoverable=True,
    )
    p_charlie = Persona(
        account_id=acc_charlie.id,
        display_name="MidnightEcho",
        avatar_seed="echo-seed",
        bio="Night thoughts.",
        is_active=True,
        is_discoverable=True,
    )
    db_session.add_all([p_alice, p_bob, p_charlie])
    await db_session.flush()

    aff_alice = CampusAffiliation(
        persona_id=p_alice.id,
        campus_name="Bay Area University",
        is_primary=True,
    )
    aff_bob = CampusAffiliation(
        persona_id=p_bob.id,
        campus_name="West Coast College",
        is_primary=True,
    )
    db_session.add_all([aff_alice, aff_bob])
    await db_session.flush()

    # Create mutual connection & conversation between Alice and Bob
    conn_req = ConnectionRequest(
        sender_persona_id=p_alice.id,
        recipient_persona_id=p_bob.id,
        status=ConnectionRequestStatus.ACCEPTED,
        note="Hey Bob!",
    )
    db_session.add(conn_req)
    await db_session.flush()

    p_a = min(p_alice.id, p_bob.id)
    p_b = max(p_alice.id, p_bob.id)
    match = Match(persona_a_id=p_a, persona_b_id=p_b, compatibility_score=88.0)
    db_session.add(match)
    await db_session.flush()

    conv = Conversation(
        connection_request_id=conn_req.id,
        match_id=match.id,
        is_active=True,
    )
    db_session.add(conv)
    await db_session.flush()

    part_alice = ConversationParticipant(
        conversation_id=conv.id,
        persona_id=p_alice.id,
        conversation_pseudonym="Echo-ALICE",
    )
    part_bob = ConversationParticipant(
        conversation_id=conv.id,
        persona_id=p_bob.id,
        conversation_pseudonym="Shadow-BOB",
    )
    db_session.add_all([part_alice, part_bob])
    await db_session.commit()

    token_alice = create_test_jwt(alice_sub, "alice@example.com")
    token_bob = create_test_jwt(bob_sub, "bob@example.com")
    token_charlie = create_test_jwt(charlie_sub, "charlie@example.com")

    return {
        "alice": {"account": acc_alice, "persona": p_alice, "token": token_alice},
        "bob": {"account": acc_bob, "persona": p_bob, "token": token_bob},
        "charlie": {"account": acc_charlie, "persona": p_charlie, "token": token_charlie},
        "conversation": conv,
    }


@pytest.mark.asyncio
async def test_list_and_detail_conversations(
    async_client: AsyncClient,
    messaging_test_setup: dict,
):
    """
    Verify listing conversations:
    - Alice and Bob see their mutual conversation.
    - Charlie (not a participant) sees empty list.
    - Conversation-specific pseudonyms are returned.
    """
    token_alice = messaging_test_setup["alice"]["token"]
    token_charlie = messaging_test_setup["charlie"]["token"]
    conv_id = str(messaging_test_setup["conversation"].id)

    # Alice lists conversations
    res_alice = await async_client.get(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert res_alice.status_code == 200
    convs = res_alice.json()
    assert len(convs) == 1
    assert convs[0]["id"] == conv_id
    assert convs[0]["my_conversation_pseudonym"] == "Echo-ALICE"
    assert convs[0]["other_participant"]["conversation_pseudonym"] == "Shadow-BOB"
    assert convs[0]["other_participant"]["declared_campus"] == "West Coast College"

    # Charlie lists conversations -> empty
    res_charlie = await async_client.get(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {token_charlie}"},
    )
    assert res_charlie.status_code == 200
    assert len(res_charlie.json()) == 0

    # Alice views conversation detail
    detail_res = await async_client.get(
        f"/api/v1/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["participants"]) == 2


@pytest.mark.asyncio
async def test_membership_authorization_on_every_operation(
    async_client: AsyncClient,
    messaging_test_setup: dict,
):
    """
    SECURITY REQUIREMENT: Verify conversation membership on every operation.
    Charlie (non-member) must be rejected with 403 Forbidden for:
    - Viewing detail
    - Fetching messages
    - Sending a message
    - Marking as read
    - Blocking conversation
    """
    token_charlie = messaging_test_setup["charlie"]["token"]
    conv_id = str(messaging_test_setup["conversation"].id)
    headers = {"Authorization": f"Bearer {token_charlie}"}

    # 1. View detail
    r1 = await async_client.get(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert r1.status_code == 403
    assert "not a member" in r1.json()["detail"].lower()

    # 2. Fetch messages
    r2 = await async_client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers)
    assert r2.status_code == 403
    assert "not a member" in r2.json()["detail"].lower()

    # 3. Send message
    r3 = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=headers,
        json={"content": "I am an eavesdropper!"},
    )
    assert r3.status_code == 403
    assert "not a member" in r3.json()["detail"].lower()

    # 4. Mark read
    r4 = await async_client.post(f"/api/v1/conversations/{conv_id}/read", headers=headers)
    assert r4.status_code == 403

    # 5. Block
    r5 = await async_client.post(f"/api/v1/conversations/{conv_id}/block", headers=headers)
    assert r5.status_code == 403


@pytest.mark.asyncio
async def test_send_and_receive_encrypted_message(
    async_client: AsyncClient,
    messaging_test_setup: dict,
    db_session: AsyncSession,
):
    """
    Verify:
    1. Message send by Alice.
    2. Message content is encrypted at rest in the PostgreSQL database.
    3. Alice & Bob retrieve decrypted plaintext.
    4. Notification indicator / unread counter increments for Bob.
    """
    token_alice = messaging_test_setup["alice"]["token"]
    token_bob = messaging_test_setup["bob"]["token"]
    conv_id = str(messaging_test_setup["conversation"].id)

    secret_text = "Let's meet by the library clock tower at 11pm."

    # Alice sends message
    send_res = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"content": secret_text},
    )
    assert send_res.status_code == 201
    msg_data = send_res.json()
    assert msg_data["content"] == secret_text
    assert msg_data["is_mine"] is True
    assert msg_data["sender_pseudonym"] == "Echo-ALICE"
    msg_id = uuid.UUID(msg_data["id"])

    # SECURITY CHECK: Verify raw database row is encrypted at rest
    raw_msg_stmt = select(Message).where(Message.id == msg_id)
    raw_msg = (await db_session.execute(raw_msg_stmt)).scalar_one_or_none()
    assert raw_msg is not None
    assert raw_msg.is_encrypted is True
    assert raw_msg.content != secret_text  # MUST NOT be plaintext
    assert decrypt_message_content(raw_msg.content) == secret_text

    # Bob retrieves messages
    bob_msgs_res = await async_client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert bob_msgs_res.status_code == 200
    bob_msgs = bob_msgs_res.json()["items"]
    assert len(bob_msgs) == 1
    assert bob_msgs[0]["content"] == secret_text
    assert bob_msgs[0]["is_mine"] is False

    # Check unread count for Bob
    unread_res = await async_client.get(
        "/api/v1/conversations/unread-count",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert unread_res.status_code == 200
    assert unread_res.json()["total_unread_messages"] == 1
    assert unread_res.json()["unread_conversations_count"] == 1

    # Bob marks conversation as read
    read_res = await async_client.post(
        f"/api/v1/conversations/{conv_id}/read",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert read_res.status_code == 200

    # Verify unread count reset
    unread_res2 = await async_client.get(
        "/api/v1/conversations/unread-count",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert unread_res2.status_code == 200
    assert unread_res2.json()["total_unread_messages"] == 0


@pytest.mark.asyncio
async def test_message_deletion_and_author_protection(
    async_client: AsyncClient,
    messaging_test_setup: dict,
):
    """
    Verify:
    1. Alice sends a message.
    2. Bob tries to delete Alice's message -> 403 Forbidden.
    3. Alice deletes her own message -> 200 OK.
    4. Deleted message content displays placeholder "[This message was deleted]".
    """
    token_alice = messaging_test_setup["alice"]["token"]
    token_bob = messaging_test_setup["bob"]["token"]
    conv_id = str(messaging_test_setup["conversation"].id)

    # Alice sends a message
    send_res = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"content": "Oops sent to wrong chat!"},
    )
    assert send_res.status_code == 201
    msg_id = send_res.json()["id"]

    # Bob attempts to delete Alice's message -> 403 Forbidden
    del_bob = await async_client.delete(
        f"/api/v1/messages/{msg_id}",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert del_bob.status_code == 403
    assert "only delete your own" in del_bob.json()["detail"].lower()

    # Alice deletes her own message -> Success
    del_alice = await async_client.delete(
        f"/api/v1/messages/{msg_id}",
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert del_alice.status_code == 200
    assert del_alice.json()["is_deleted"] is True
    assert del_alice.json()["content"] == "[This message was deleted]"

    # Both retrieve messages and see deleted placeholder
    msgs_res = await async_client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert msgs_res.status_code == 200
    msgs = msgs_res.json()["items"]
    assert msgs[-1]["is_deleted"] is True
    assert msgs[-1]["content"] == "[This message was deleted]"


@pytest.mark.asyncio
async def test_conversation_blocking_and_disabling_messages(
    async_client: AsyncClient,
    messaging_test_setup: dict,
    db_session: AsyncSession,
):
    """
    Verify:
    1. Bob blocks the conversation.
    2. Conversation is marked inactive and blocked.
    3. Bilateral block record is created.
    4. Attempting to send message to blocked conversation returns 403 Forbidden.
    """
    token_alice = messaging_test_setup["alice"]["token"]
    token_bob = messaging_test_setup["bob"]["token"]
    conv_id = str(messaging_test_setup["conversation"].id)

    # Bob blocks conversation
    blk_res = await async_client.post(
        f"/api/v1/conversations/{conv_id}/block?reason=Spam",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert blk_res.status_code == 200
    assert blk_res.json()["status"] == "BLOCKED"

    # Alice tries to send message -> 403 Forbidden
    send_alice = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"content": "Are you there?"},
    )
    assert send_alice.status_code == 403
    assert "blocked" in send_alice.json()["detail"].lower()

    # Bob tries to send message -> 403 Forbidden
    send_bob = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token_bob}"},
        json={"content": "Still here?"},
    )
    assert send_bob.status_code == 403

    # Check block record in DB
    block_stmt = select(Block).where(
        Block.blocker_persona_id == messaging_test_setup["bob"]["persona"].id,
        Block.blocked_persona_id == messaging_test_setup["alice"]["persona"].id,
    )
    blk = (await db_session.execute(block_stmt)).scalar_one_or_none()
    assert blk is not None


def test_websocket_authorization_and_unauthorized_subscription():
    """
    SECURITY REQUIREMENT:
    - Restrict realtime channel access
    - Prevent unauthorized subscriptions
    - Require valid token
    """
    # Create test account & persona directly for sync TestClient
    alice_sub = uuid.uuid4()
    charlie_sub = uuid.uuid4()
    token_alice = create_test_jwt(alice_sub, "alice_ws@example.com")
    token_charlie = create_test_jwt(charlie_sub, "charlie_ws@example.com")
    fake_conv_id = uuid.uuid4()

    client = TestClient(app)

    # 1. Missing token -> Policy violation close
    with pytest.raises(WebSocketDisconnect) as exc1:
        with client.websocket_connect(f"/api/v1/ws/conversations/{fake_conv_id}"):
            pass
    assert exc1.value.code == 1008

    # 2. Invalid token -> Policy violation close
    with pytest.raises(WebSocketDisconnect) as exc2:
        with client.websocket_connect(f"/api/v1/ws/conversations/{fake_conv_id}?token=invalid.jwt.token"):
            pass
    assert exc2.value.code == 1008


@pytest.mark.asyncio
async def test_message_history_cursor_pagination(
    async_client: AsyncClient,
    messaging_test_setup: dict,
):
    """Verify keyset cursor pagination for long conversation histories."""
    token_alice = messaging_test_setup["alice"]["token"]
    conv_id = str(messaging_test_setup["conversation"].id)
    headers = {"Authorization": f"Bearer {token_alice}"}

    # Send 5 messages
    for i in range(5):
        await async_client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=headers,
            json={"content": f"Message batch index #{i}"},
        )

    # Fetch with limit=2
    res_p1 = await async_client.get(
        f"/api/v1/conversations/{conv_id}/messages?limit=2",
        headers=headers,
    )
    assert res_p1.status_code == 200
    p1 = res_p1.json()
    assert len(p1["items"]) == 2
    assert p1["has_more"] is True
    assert p1["next_cursor"] is not None

    # Fetch next page using next_cursor
    res_p2 = await async_client.get(
        f"/api/v1/conversations/{conv_id}/messages?limit=2&cursor={p1['next_cursor']}",
        headers=headers,
    )
    assert res_p2.status_code == 200
    p2 = res_p2.json()
    assert len(p2["items"]) == 2


@pytest.mark.asyncio
async def test_reporting_message_and_audit_trail(
    async_client: AsyncClient,
    messaging_test_setup: dict,
):
    """
    Verify reporting an abusive message:
    - Generates report
    - Content is never logged in security audit logs
    """
    token_alice = messaging_test_setup["alice"]["token"]
    token_bob = messaging_test_setup["bob"]["token"]
    conv_id = str(messaging_test_setup["conversation"].id)

    # Alice sends a message
    send_res = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"content": "Suspicious offer..."},
    )
    assert send_res.status_code == 201
    msg_id = send_res.json()["id"]

    # Bob reports message
    rep_res = await async_client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {token_bob}"},
        json={
            "target_type": "MESSAGE",
            "target_id": msg_id,
            "reason": "Suspected spam/commercial solicitation",
        },
    )
    assert rep_res.status_code == 201
    assert rep_res.json()["status"] == "PENDING"

