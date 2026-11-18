import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.main import app
from backend.app.core.security import create_test_jwt
from backend.app.models.account import Account, AccountStatus
from backend.app.models.persona import Persona, CampusAffiliation
from backend.app.models.social import Post, Comment, Reaction
from backend.app.models.moderation import Block


@pytest.fixture
async def social_test_users(db_session: AsyncSession):
    """
    Setup 3 test accounts and personas:
    1. Alice (ShadowFox) - Bay Area University
    2. Bob (NeonGhost) - West Coast College
    3. Charlie (MidnightEcho) - Bay Area University
    """
    alice_sub = uuid.uuid4()
    bob_sub = uuid.uuid4()
    charlie_sub = uuid.uuid4()

    acc_alice = Account(
        supabase_user_id=alice_sub,
        email_hash="hash_alice@example.com",
        is_age_verified=True,
        birth_year=2001,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
    )
    acc_bob = Account(
        supabase_user_id=bob_sub,
        email_hash="hash_bob@example.com",
        is_age_verified=True,
        birth_year=2000,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
    )
    acc_charlie = Account(
        supabase_user_id=charlie_sub,
        email_hash="hash_charlie@example.com",
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
    )
    p_bob = Persona(
        account_id=acc_bob.id,
        display_name="NeonGhost",
        avatar_seed="ghost-seed",
        bio="Philosophy & beats.",
        is_active=True,
    )
    p_charlie = Persona(
        account_id=acc_charlie.id,
        display_name="MidnightEcho",
        avatar_seed="echo-seed",
        bio="Night thoughts.",
        is_active=True,
    )
    db_session.add_all([p_alice, p_bob, p_charlie])
    await db_session.flush()

    aff_alice = CampusAffiliation(
        persona_id=p_alice.id,
        campus_name="Bay Area University",
        campus_code="BAU",
        is_primary=True,
    )
    aff_bob = CampusAffiliation(
        persona_id=p_bob.id,
        campus_name="West Coast College",
        campus_code="WCC",
        is_primary=True,
    )
    db_session.add_all([aff_alice, aff_bob])
    await db_session.commit()

    return {
        "alice": {
            "account": acc_alice,
            "persona": p_alice,
            "token": create_test_jwt(alice_sub, "alice@example.com"),
        },
        "bob": {
            "account": acc_bob,
            "persona": p_bob,
            "token": create_test_jwt(bob_sub, "bob@example.com"),
        },
        "charlie": {
            "account": acc_charlie,
            "persona": p_charlie,
            "token": create_test_jwt(charlie_sub, "charlie@example.com"),
        },
    }


@pytest.mark.asyncio
async def test_create_post_success_and_identity_isolation(async_client: AsyncClient, social_test_users):
    """Verify post publication succeeds and returns NO real account info (only public persona)."""
    alice = social_test_users["alice"]

    payload = {
        "content": "Secret lab confession: falling for a fellow researcher after hours.",
        "tag": "confessions",
        "post_type": "CONFESSION",
        "is_sensitive": False,
        "allow_comments": True,
        "campus_name": "Bay Area University",
    }
    res = await async_client.post(
        "/api/v1/posts",
        json=payload,
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["content"] == payload["content"]
    assert data["tag"] == "confessions"
    assert data["campus_name"] == "Bay Area University"
    assert data["allow_comments"] is True
    assert data["is_own"] is True

    # STRICT PRIVACY & ZERO LEAKAGE: Check persona object
    persona_data = data["persona"]
    assert persona_data["display_name"] == "ShadowFox"
    assert "account_id" not in persona_data
    assert "email" not in persona_data
    assert "supabase_user_id" not in persona_data
    assert "account_id" not in data


@pytest.mark.asyncio
async def test_pre_publication_moderation_pii_shield(async_client: AsyncClient, social_test_users):
    """Verify ContentModerationEngine hard-rejects doxxing and PII patterns before publication."""
    alice = social_test_users["alice"]

    # 1. Phone number test
    res_phone = await async_client.post(
        "/api/v1/posts",
        json={"content": "Call me at 415-555-0199 for late night party in tower 3.", "tag": "dating"},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert res_phone.status_code == 400
    assert "Phone number detected" in res_phone.json()["detail"]

    # 2. Email test
    res_email = await async_client.post(
        "/api/v1/posts",
        json={"content": "Send answers to student@campus.edu please.", "tag": "questions"},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert res_email.status_code == 400
    assert "Email address detected" in res_email.json()["detail"]

    # 3. Student ID test
    res_id = await async_client.post(
        "/api/v1/posts",
        json={"content": "Lost my wallet, student id: 9948210 if found.", "tag": "campus-life"},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert res_id.status_code == 400
    assert "Student / College ID number detected" in res_id.json()["detail"]


@pytest.mark.asyncio
async def test_post_ownership_and_deletion(async_client: AsyncClient, social_test_users):
    """Verify authors can delete own posts; non-authors receive 403 Forbidden."""
    alice = social_test_users["alice"]
    bob = social_test_users["bob"]

    # Alice creates a post
    res_create = await async_client.post(
        "/api/v1/posts",
        json={"content": "A fleeting thought on architecture and solitude.", "tag": "experiences"},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    post_id = res_create.json()["id"]

    # Bob attempts to delete Alice's post -> 403 Forbidden
    res_bob_delete = await async_client.delete(
        f"/api/v1/posts/{post_id}",
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    assert res_bob_delete.status_code == 403
    assert "permission" in res_bob_delete.json()["detail"]

    # Alice deletes her own post -> 204 No Content
    res_alice_delete = await async_client.delete(
        f"/api/v1/posts/{post_id}",
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert res_alice_delete.status_code == 204

    # Verify post is no longer returned in public feed
    res_feed = await async_client.get("/api/v1/posts")
    post_ids = [p["id"] for p in res_feed.json()["items"]]
    assert post_id not in post_ids


@pytest.mark.asyncio
async def test_author_view_own_posts_privately(async_client: AsyncClient, social_test_users):
    """Verify author can view their own posts privately via /api/v1/posts/me."""
    alice = social_test_users["alice"]

    # Alice creates a private post with comments disabled
    await async_client.post(
        "/api/v1/posts",
        json={"content": "Private journal confession on late night thoughts.", "allow_comments": False},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )

    res_me = await async_client.get(
        "/api/v1/posts/me",
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert res_me.status_code == 200
    items = res_me.json()["items"]
    assert len(items) >= 1
    assert any("Private journal confession" in p["content"] for p in items)
    assert all(p["is_own"] is True for p in items)


@pytest.mark.asyncio
async def test_disabling_comments_and_threaded_replies(async_client: AsyncClient, social_test_users):
    """Verify posts with comments disabled reject new comments; allowed posts accept threaded replies."""
    alice = social_test_users["alice"]
    bob = social_test_users["bob"]

    # 1. Post with comments disabled
    res_disabled_post = await async_client.post(
        "/api/v1/posts",
        json={"content": "No comments allowed on this unfiltered adult thought.", "allow_comments": False},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    disabled_post_id = res_disabled_post.json()["id"]

    # Bob attempts to comment -> 403 Forbidden
    res_comment_fail = await async_client.post(
        f"/api/v1/posts/{disabled_post_id}/comments",
        json={"content": "I disagree with you!"},
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    assert res_comment_fail.status_code == 403
    assert "disabled" in res_comment_fail.json()["detail"]

    # 2. Post with comments enabled
    res_enabled_post = await async_client.post(
        "/api/v1/posts",
        json={"content": "Open discussion: is college social life performative?", "allow_comments": True},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    enabled_post_id = res_enabled_post.json()["id"]

    # Bob adds top-level comment
    res_bob_comment = await async_client.post(
        f"/api/v1/posts/{enabled_post_id}/comments",
        json={"content": "Completely performative. Everyone poses on LinkedIn."},
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    assert res_bob_comment.status_code == 201
    bob_comment_id = res_bob_comment.json()["id"]
    assert res_bob_comment.json()["is_op"] is False

    # Alice replies as OP (threaded reply with parent_id)
    res_alice_reply = await async_client.post(
        f"/api/v1/posts/{enabled_post_id}/comments",
        json={"content": "Exactly my point! Glad someone else feels it.", "parent_id": bob_comment_id},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert res_alice_reply.status_code == 201
    assert res_alice_reply.json()["is_op"] is True
    assert res_alice_reply.json()["parent_id"] == bob_comment_id

    # Verify comment list returns both comments
    res_list = await async_client.get(f"/api/v1/posts/{enabled_post_id}/comments")
    assert res_list.status_code == 200
    comments = res_list.json()["items"]
    assert len(comments) == 2


@pytest.mark.asyncio
async def test_anonymous_reactions(async_client: AsyncClient, social_test_users):
    """Verify anonymous reaction toggling and summary updates."""
    alice = social_test_users["alice"]
    bob = social_test_users["bob"]

    # Create post
    post_res = await async_client.post(
        "/api/v1/posts",
        json={"content": "Spicy unfiltered discussion topic for adult community.", "tag": "adult-interests"},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    post_id = post_res.json()["id"]

    # Bob reacts with FLAME
    res_rx1 = await async_client.post(
        f"/api/v1/posts/{post_id}/reactions",
        json={"reaction_type": "FLAME"},
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    assert res_rx1.status_code == 200
    assert res_rx1.json()["action"] == "ADDED"
    assert res_rx1.json()["reaction_type"] == "FLAME"
    assert res_rx1.json()["reactions_summary"]["flames"] == 1

    # Bob changes reaction to HEART
    res_rx2 = await async_client.post(
        f"/api/v1/posts/{post_id}/reactions",
        json={"reaction_type": "HEART"},
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    assert res_rx2.status_code == 200
    assert res_rx2.json()["action"] == "UPDATED"
    assert res_rx2.json()["reactions_summary"]["flames"] == 0
    assert res_rx2.json()["reactions_summary"]["hearts"] == 1

    # Bob repeats HEART -> Toggles off (REMOVED)
    res_rx3 = await async_client.post(
        f"/api/v1/posts/{post_id}/reactions",
        json={"reaction_type": "HEART"},
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    assert res_rx3.status_code == 200
    assert res_rx3.json()["action"] == "REMOVED"
    assert res_rx3.json()["reaction_type"] is None
    assert res_rx3.json()["reactions_summary"]["hearts"] == 0


@pytest.mark.asyncio
async def test_blocking_and_feed_isolation(async_client: AsyncClient, social_test_users):
    """
    Verify blocking enforces bilateral isolation:
    - Persona A blocks Persona B.
    - Persona B's posts disappear from Persona A's feed.
    - Persona A's posts disappear from Persona B's feed.
    - Unblocking restores visibility.
    """
    alice = social_test_users["alice"]
    bob = social_test_users["bob"]

    # Alice creates Post A
    res_a = await async_client.post(
        "/api/v1/posts",
        json={"content": "Alice unique post for block isolation testing 12345."},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    post_a_id = res_a.json()["id"]

    # Bob creates Post B
    res_b = await async_client.post(
        "/api/v1/posts",
        json={"content": "Bob unique post for block isolation testing 67890."},
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    post_b_id = res_b.json()["id"]

    # Prior to blocking: Alice sees Bob's post, Bob sees Alice's post
    feed_alice_before = await async_client.get("/api/v1/posts", headers={"Authorization": f"Bearer {alice['token']}"})
    feed_ids_alice_before = [p["id"] for p in feed_alice_before.json()["items"]]
    assert post_b_id in feed_ids_alice_before

    # Anti-Self block check: Alice cannot block herself
    res_self_block = await async_client.post(
        "/api/v1/blocks",
        json={"blocked_persona_id": str(alice["persona"].id)},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert res_self_block.status_code == 400
    assert "own persona" in res_self_block.json()["detail"]

    # Alice blocks Bob
    res_block = await async_client.post(
        "/api/v1/blocks",
        json={"blocked_persona_id": str(bob["persona"].id), "reason": "Unwanted vibes"},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert res_block.status_code == 201

    # BILATERAL ISOLATION CHECK:
    # 1. In Alice's feed, Bob's post is excluded
    feed_alice_after = await async_client.get("/api/v1/posts", headers={"Authorization": f"Bearer {alice['token']}"})
    feed_ids_alice_after = [p["id"] for p in feed_alice_after.json()["items"]]
    assert post_b_id not in feed_ids_alice_after

    # 2. In Bob's feed, Alice's post is excluded
    feed_bob_after = await async_client.get("/api/v1/posts", headers={"Authorization": f"Bearer {bob['token']}"})
    feed_ids_bob_after = [p["id"] for p in feed_bob_after.json()["items"]]
    assert post_a_id not in feed_ids_bob_after

    # Alice unblocks Bob
    res_unblock = await async_client.delete(
        f"/api/v1/blocks/{bob['persona'].id}",
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert res_unblock.status_code == 204

    # Visibility restored
    feed_alice_restored = await async_client.get("/api/v1/posts", headers={"Authorization": f"Bearer {alice['token']}"})
    feed_ids_alice_restored = [p["id"] for p in feed_alice_restored.json()["items"]]
    assert post_b_id in feed_ids_alice_restored


@pytest.mark.asyncio
async def test_campus_filters_and_cursor_pagination(async_client: AsyncClient, social_test_users):
    """Verify filtering by self-declared campus and keyset cursor pagination."""
    alice = social_test_users["alice"]
    bob = social_test_users["bob"]

    # Create posts with different declared campuses
    await async_client.post(
        "/api/v1/posts",
        json={"content": "Bay Area Post Alpha 100", "campus_name": "Bay Area University"},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    await async_client.post(
        "/api/v1/posts",
        json={"content": "West Coast Post Beta 200", "campus_name": "West Coast College"},
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    await async_client.post(
        "/api/v1/posts",
        json={"content": "Bay Area Post Gamma 300", "campus_name": "Bay Area University"},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )

    # 1. Campus filter test
    res_bau = await async_client.get("/api/v1/posts?campus=Bay Area University")
    assert res_bau.status_code == 200
    items_bau = res_bau.json()["items"]
    assert all(p["campus_name"] == "Bay Area University" for p in items_bau)
    assert not any("West Coast Post Beta" in p["content"] for p in items_bau)

    # 2. Keyset cursor pagination test (limit=2)
    res_page1 = await async_client.get("/api/v1/posts?limit=2")
    assert res_page1.status_code == 200
    data1 = res_page1.json()
    assert len(data1["items"]) == 2
    assert data1["has_more"] is True
    assert data1["next_cursor"] is not None

    # Fetch page 2 with next_cursor
    res_page2 = await async_client.get(f"/api/v1/posts?limit=2&cursor={data1['next_cursor']}")
    assert res_page2.status_code == 200
    data2 = res_page2.json()
    assert len(data2["items"]) >= 1

    # Ensure no overlap between page 1 and page 2
    page1_ids = {p["id"] for p in data1["items"]}
    page2_ids = {p["id"] for p in data2["items"]}
    assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_reporting_endpoint(async_client: AsyncClient, social_test_users):
    """Verify reporting endpoint records report and creates audit log."""
    alice = social_test_users["alice"]
    bob = social_test_users["bob"]

    # Create post to report
    res_post = await async_client.post(
        "/api/v1/posts",
        json={"content": "A post to test the safety reporting mechanism."},
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    target_post_id = res_post.json()["id"]

    # Alice reports post
    res_report = await async_client.post(
        "/api/v1/reports",
        json={
            "target_type": "POST",
            "target_id": target_post_id,
            "reason": "Suspicious commercial advertising link.",
        },
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert res_report.status_code == 201
    data = res_report.json()
    assert data["target_type"] == "POST"
    assert data["target_id"] == target_post_id
    assert data["status"] == "PENDING"

