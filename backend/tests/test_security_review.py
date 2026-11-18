import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.security import create_test_jwt, hash_token, hash_recipient_email
from backend.app.core.rate_limiter import SlidingWindowRateLimiter
from backend.app.models.base import utc_now
from backend.app.models.account import Account, AccountStatus
from backend.app.models.persona import Persona
from backend.app.models.invitation import Invitation, InvitationStatus
from backend.app.models.social import Post, Story
from backend.app.models.event import Event
from backend.app.models.connection import Conversation, ConversationParticipant, Message
from backend.app.services.age_assurance import AgeAssuranceEngine


@pytest.fixture
async def sec_review_users(db_session: AsyncSession):
    """
    Setup 3 test accounts:
    1. Victim / Alice (User A)
    2. Attacker / Bob (User B)
    3. Moderator / Eve
    """
    sub_a = uuid.uuid4()
    sub_b = uuid.uuid4()
    sub_mod = uuid.uuid4()

    acc_a = Account(
        supabase_user_id=sub_a,
        email_hash="hash_sec_a@example.com",
        is_age_verified=True,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
        role="USER",
    )
    acc_b = Account(
        supabase_user_id=sub_b,
        email_hash="hash_sec_b@example.com",
        is_age_verified=True,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
        role="USER",
    )
    acc_mod = Account(
        supabase_user_id=sub_mod,
        email_hash="hash_sec_mod@example.com",
        is_age_verified=True,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
        role="MODERATOR",
    )
    db_session.add_all([acc_a, acc_b, acc_mod])
    await db_session.flush()

    p_a = Persona(account_id=acc_a.id, display_name="AlicePersona", avatar_seed="seed-a", is_active=True)
    p_b = Persona(account_id=acc_b.id, display_name="BobPersona", avatar_seed="seed-b", is_active=True)
    p_mod = Persona(account_id=acc_mod.id, display_name="ModPersona", avatar_seed="seed-mod", is_active=True)
    db_session.add_all([p_a, p_b, p_mod])
    await db_session.commit()

    return {
        "alice": {"account": acc_a, "persona": p_a, "token": create_test_jwt(sub_a, "alice@test.edu")},
        "bob": {"account": acc_b, "persona": p_b, "token": create_test_jwt(sub_b, "bob@test.edu")},
        "mod": {"account": acc_mod, "persona": p_mod, "token": create_test_jwt(sub_mod, "mod@test.edu")},
    }


# --- 1. Cross-Account Authorization & Access Tests ---

@pytest.mark.asyncio
async def test_cross_account_post_deletion_blocked(async_client: AsyncClient, sec_review_users, db_session: AsyncSession):
    """Security check: User B cannot delete User A's post."""
    alice = sec_review_users["alice"]
    bob = sec_review_users["bob"]

    # Alice creates a post
    post = Post(
        persona_id=alice["persona"].id,
        content="Alice's private thoughts and reflections",
        tag="confessions",
        moderation_status="PUBLISHED",
        is_deleted=False,
    )
    db_session.add(post)
    await db_session.commit()

    # Bob attempts to delete Alice's post
    del_res = await async_client.delete(
        f"/api/v1/posts/{post.id}",
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    assert del_res.status_code == 403
    assert "permission" in del_res.json()["detail"].lower() or "delete" in del_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cross_account_story_deletion_blocked(async_client: AsyncClient, sec_review_users, db_session: AsyncSession):
    """Security check: User B cannot delete User A's ephemeral story."""
    alice = sec_review_users["alice"]
    bob = sec_review_users["bob"]

    story = Story(
        persona_id=alice["persona"].id,
        content="Alice's 24-hour midnight thoughts",
        category="night-thoughts",
        visibility="PUBLIC",
        moderation_status="APPROVED",
        is_deleted=False,
        expires_at=utc_now() + timedelta(hours=24),
    )
    db_session.add(story)
    await db_session.commit()

    # Bob attempts to delete Alice's story
    del_res = await async_client.delete(
        f"/api/v1/stories/{story.id}",
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    assert del_res.status_code == 403
    assert "own" in del_res.json()["detail"].lower() or "delete" in del_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cross_account_event_cancellation_blocked(async_client: AsyncClient, sec_review_users, db_session: AsyncSession):
    """Security check: User B cannot cancel User A's meetup."""
    alice = sec_review_users["alice"]
    bob = sec_review_users["bob"]

    event = Event(
        creator_persona_id=alice["persona"].id,
        title="Physics Observatory Star Party",
        description="Public telescope viewing from observatory terrace",
        location_name="Physics Observatory Terrace Deck",
        event_time=utc_now() + timedelta(days=2),
        is_cancelled=False,
        is_deleted=False,
    )
    db_session.add(event)
    await db_session.commit()

    # Bob attempts to cancel Alice's meetup
    cancel_res = await async_client.post(
        f"/api/v1/events/{event.id}/cancel",
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    assert cancel_res.status_code == 403
    assert "organizer" in cancel_res.json()["detail"].lower()


# --- 2. Private Messaging Isolation Tests ---

@pytest.mark.asyncio
async def test_private_messaging_isolation_and_membership_check(async_client: AsyncClient, sec_review_users, db_session: AsyncSession):
    """
    Security check:
    - User B cannot view messages in a conversation they are not part of.
    - User B cannot send messages to a conversation they are not part of.
    """
    alice = sec_review_users["alice"]
    bob = sec_review_users["bob"]
    mod = sec_review_users["mod"]

    # Conversation between Alice and Mod
    conv = Conversation(blocked_by_persona_id=None)
    db_session.add(conv)
    await db_session.flush()

    part1 = ConversationParticipant(conversation_id=conv.id, persona_id=alice["persona"].id, conversation_pseudonym="Echo-Alice")
    part2 = ConversationParticipant(conversation_id=conv.id, persona_id=mod["persona"].id, conversation_pseudonym="Shadow-Mod")
    db_session.add_all([part1, part2])
    await db_session.commit()

    # Bob attempts to read Alice's conversation messages
    read_res = await async_client.get(
        f"/api/v1/conversations/{conv.id}/messages",
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    assert read_res.status_code == 403
    assert "member" in read_res.json()["detail"].lower() or "participant" in read_res.json()["detail"].lower()

    # Bob attempts to send message to Alice's conversation
    send_res = await async_client.post(
        f"/api/v1/conversations/{conv.id}/messages",
        json={"content": "Eavesdropping intruder message"},
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    assert send_res.status_code == 403
    assert "member" in send_res.json()["detail"].lower() or "participant" in send_res.json()["detail"].lower()


# --- 3. Rate Limiting Tests ---

@pytest.mark.asyncio
async def test_rate_limiting_enforcement():
    """
    Security check: Rapid requests trigger 429 Too Many Requests with Retry-After header.
    """
    test_prefix = f"test_limit_{uuid.uuid4().hex[:8]}"
    limiter = SlidingWindowRateLimiter(requests=3, window_seconds=60, key_prefix=test_prefix)

    class DummyClient:
        host = "192.168.1.100"

    class DummyRequest:
        def __init__(self):
            self.client = DummyClient()
            self.headers = {"Authorization": "Bearer test_token_xyz"}
            self.url = type("URL", (), {"path": "/test/rate-limited"})()

    req = DummyRequest()

    # 1st call -> OK
    assert await limiter(req) is True
    # 2nd call -> OK
    assert await limiter(req) is True
    # 3rd call -> OK
    assert await limiter(req) is True

    # 4th call -> Exceeded!
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await limiter(req)
    assert exc_info.value.status_code == 429
    assert "rate limit exceeded" in exc_info.value.detail.lower()
    assert "Retry-After" in exc_info.value.headers


# --- 4. Underage Access Prevention Tests ---

@pytest.mark.asyncio
async def test_underage_access_prevention():
    """
    Security check: AgeAssuranceEngine strictly rejects any evidence indicating age < 18.
    No checkbox or fake verification can bypass this gate.
    """
    current_year = datetime.now().year
    underage_birthdate = date(current_year - 16, 5, 20)  # 16 years old

    res = AgeAssuranceEngine.verify_and_generate_proof(
        email="minor@campus.edu",
        birth_date=underage_birthdate,
        evidence_type="MOCK_GOVERNMENT_ID",
        provider_session_token="mock_prov_token",
    )
    assert res.is_verified is False
    assert "18 years" in res.error_message


# --- 5. Zero Identity Leakage & No College Email Requirement Tests ---

@pytest.mark.asyncio
async def test_zero_identity_leakage_and_no_college_email_requirement(async_client: AsyncClient, sec_review_users):
    """
    Security check:
    1. Public posts feed contains zero real emails, auth IDs, or IP addresses.
    2. Any standard personal email (e.g. user@gmail.com) is valid; college email is NOT required.
    """
    alice = sec_review_users["alice"]
    headers = {"Authorization": f"Bearer {alice['token']}"}

    # Fetch public posts
    feed_res = await async_client.get("/api/v1/posts", headers=headers)
    assert feed_res.status_code == 200

    items = feed_res.json()["items"]
    for post in items:
        # Check author object
        author = post["persona"]
        assert "email" not in author
        assert "email_hash" not in author
        assert "supabase_user_id" not in author
        assert "account_id" not in author
        # Must only have pseudonym
        assert "display_name" in author
        assert "avatar_seed" in author

    # Verify standard personal email initiation works (no .edu requirement)
    init_res = await async_client.post(
        "/api/v1/auth/age/initiate",
        json={"email": "adult_citizen@gmail.com"},
    )
    assert init_res.status_code == 200
    assert "session_id" in init_res.json()


# --- 6. Security Headers Verification ---

@pytest.mark.asyncio
async def test_production_security_headers_present(async_client: AsyncClient):
    """
    Security check: Verify that critical production security headers are set on all responses:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - Strict-Transport-Security
    - Content-Security-Policy
    - Referrer-Policy
    """
    res = await async_client.get("/")
    assert res.status_code == 200
    headers = res.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "max-age=" in headers.get("Strict-Transport-Security", "")
    assert "default-src" in headers.get("Content-Security-Policy", "")
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
