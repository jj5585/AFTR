import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.security import create_test_jwt, get_totp_code
from backend.app.models.account import Account, AccountStatus
from backend.app.models.persona import Persona, CampusAffiliation
from backend.app.models.social import Post, Story, Comment
from backend.app.models.moderation import ModerationAction, ModerationActionType, Appeal, AppealStatus, Report, Block


@pytest.fixture
async def trust_safety_test_users(db_session: AsyncSession):
    """
    Setup 4 accounts:
    1. Regular Member (Alice / ShadowFox) - role: USER
    2. Moderator (Eve / CampusMod) - role: MODERATOR
    3. Security Administrator (Dave / SecAdmin) - role: SECURITY_ADMIN
    4. Violating User (Mallory / BadActor) - role: USER
    """
    sub_alice = uuid.uuid4()
    sub_mod = uuid.uuid4()
    sub_sec = uuid.uuid4()
    sub_bad = uuid.uuid4()

    acc_alice = Account(
        supabase_user_id=sub_alice,
        email_hash="hash_alice_ts@example.com",
        is_age_verified=True,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
        role="USER",
    )
    acc_mod = Account(
        supabase_user_id=sub_mod,
        email_hash="hash_mod_ts@example.com",
        is_age_verified=True,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
        role="MODERATOR",
    )
    acc_sec = Account(
        supabase_user_id=sub_sec,
        email_hash="hash_sec_ts@example.com",
        is_age_verified=True,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
        role="SECURITY_ADMIN",
    )
    acc_bad = Account(
        supabase_user_id=sub_bad,
        email_hash="hash_bad_ts@example.com",
        is_age_verified=True,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
        role="USER",
    )

    db_session.add_all([acc_alice, acc_mod, acc_sec, acc_bad])
    await db_session.flush()

    p_alice = Persona(account_id=acc_alice.id, display_name="ShadowFox", avatar_seed="seed-alice", is_active=True)
    p_mod = Persona(account_id=acc_mod.id, display_name="CampusMod", avatar_seed="seed-mod", is_active=True)
    p_sec = Persona(account_id=acc_sec.id, display_name="SecAdmin", avatar_seed="seed-sec", is_active=True)
    p_bad = Persona(account_id=acc_bad.id, display_name="BadActor", avatar_seed="seed-bad", is_active=True)

    db_session.add_all([p_alice, p_mod, p_sec, p_bad])
    await db_session.flush()

    aff_alice = CampusAffiliation(persona_id=p_alice.id, campus_name="Bay Area University", is_primary=True)
    db_session.add(aff_alice)
    await db_session.commit()

    return {
        "alice": {"account": acc_alice, "persona": p_alice, "token": create_test_jwt(sub_alice, "alice@test.edu")},
        "mod": {"account": acc_mod, "persona": p_mod, "token": create_test_jwt(sub_mod, "mod@test.edu")},
        "sec": {"account": acc_sec, "persona": p_sec, "token": create_test_jwt(sub_sec, "sec@test.edu")},
        "bad": {"account": acc_bad, "persona": p_bad, "token": create_test_jwt(sub_bad, "bad@test.edu")},
    }


# --- 1. Automated Abuse Detection Tests ---

@pytest.mark.asyncio
async def test_spam_detection(async_client: AsyncClient, trust_safety_test_users):
    """Test commercial spam, crypto scams, telegram handles, and cash solicitation rejection."""
    alice = trust_safety_test_users["alice"]
    headers = {"Authorization": f"Bearer {alice['token']}"}

    # Crypto pump
    res1 = await async_client.post(
        "/api/v1/posts",
        json={"content": "Check this crypto pump 100x guaranteed ROI join now!", "tag": "questions", "is_sensitive": False},
        headers=headers,
    )
    assert res1.status_code == 400
    assert "crypto" in res1.json()["detail"].lower() or "spam" in res1.json()["detail"].lower()

    # Telegram link
    res2 = await async_client.post(
        "/api/v1/posts",
        json={"content": "HMU on telegram t.me/darknetdeals for exclusive party links", "tag": "dating", "is_sensitive": False},
        headers=headers,
    )
    assert res2.status_code == 400
    assert "spam" in res2.json()["detail"].lower() or "telegram" in res2.json()["detail"].lower()

    # Cashapp solicitation
    res3 = await async_client.post(
        "/api/v1/posts",
        json={"content": "Bro broke send money to cashapp $moneyman quick", "tag": "campus life", "is_sensitive": False},
        headers=headers,
    )
    assert res3.status_code == 400
    assert "cash" in res3.json()["detail"].lower() or "spam" in res3.json()["detail"].lower()


@pytest.mark.asyncio
async def test_harassment_and_hate_speech_detection(async_client: AsyncClient, trust_safety_test_users):
    """Test targeted bullying and prohibited hate speech rejection."""
    alice = trust_safety_test_users["alice"]
    headers = {"Authorization": f"Bearer {alice['token']}"}

    # Harassment
    res1 = await async_client.post(
        "/api/v1/posts",
        json={"content": "You are worthless nobody loves you go drown in a ditch", "tag": "confessions", "is_sensitive": False},
        headers=headers,
    )
    assert res1.status_code == 400
    assert "harassment" in res1.json()["detail"].lower() or "standards" in res1.json()["detail"].lower()

    # Hate speech
    res2 = await async_client.post(
        "/api/v1/posts",
        json={"content": "All of them are subhuman scum of the earth get out", "tag": "campus life", "is_sensitive": False},
        headers=headers,
    )
    assert res2.status_code == 400
    assert "hate speech" in res2.json()["detail"].lower() or "standards" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_doxxing_and_dorm_identifier_detection(async_client: AsyncClient, trust_safety_test_users):
    """Test anti-doxxing: emails, phone numbers, student IDs, and dorm numbers."""
    alice = trust_safety_test_users["alice"]
    headers = {"Authorization": f"Bearer {alice['token']}"}

    # Dorm room
    res1 = await async_client.post(
        "/api/v1/posts",
        json={"content": "Come hang out in dorm room #304 after midnight", "tag": "dating", "is_sensitive": False},
        headers=headers,
    )
    assert res1.status_code == 400
    assert "privacy shield" in res1.json()["detail"].lower()

    # Phone number
    res2 = await async_client.post(
        "/api/v1/posts",
        json={"content": "Text me on 415-555-0199 tonight", "tag": "dating", "is_sensitive": False},
        headers=headers,
    )
    assert res2.status_code == 400
    assert "phone" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_threats_and_violence_detection(async_client: AsyncClient, trust_safety_test_users):
    """Test threats of violence and self-harm encouragement."""
    alice = trust_safety_test_users["alice"]
    headers = {"Authorization": f"Bearer {alice['token']}"}

    # Violent threat
    res1 = await async_client.post(
        "/api/v1/posts",
        json={"content": "I will murder you if I see you near the quad", "tag": "confessions", "is_sensitive": False},
        headers=headers,
    )
    assert res1.status_code == 400
    assert "threat" in res1.json()["detail"].lower() or "violence" in res1.json()["detail"].lower()

    # Suicide encouragement
    res2 = await async_client.post(
        "/api/v1/posts",
        json={"content": "Just commit suicide nobody cares anyway", "tag": "confessions", "is_sensitive": False},
        headers=headers,
    )
    assert res2.status_code == 400
    assert "suicide" in res2.json()["detail"].lower() or "harm" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_non_consensual_and_prohibited_sexual_content(async_client: AsyncClient, trust_safety_test_users):
    """Test non-consensual content, revenge porn, and minor dating rejection."""
    alice = trust_safety_test_users["alice"]
    headers = {"Authorization": f"Bearer {alice['token']}"}

    # Revenge porn
    res1 = await async_client.post(
        "/api/v1/posts",
        json={"content": "I have leaked her nudes check them out", "tag": "experiences", "is_sensitive": False},
        headers=headers,
    )
    assert res1.status_code == 400
    assert "non-consensual" in res1.json()["detail"].lower() or "safety shield" in res1.json()["detail"].lower()

    # Sextortion
    res2 = await async_client.post(
        "/api/v1/posts",
        json={"content": "Pay me or I send your nudes to your friends", "tag": "confessions", "is_sensitive": False},
        headers=headers,
    )
    assert res2.status_code == 400
    assert "extortion" in res2.json()["detail"].lower()

    # Underage / Minor
    res3 = await async_client.post(
        "/api/v1/posts",
        json={"content": "Any high schooler or minor dating around here?", "tag": "dating", "is_sensitive": False},
        headers=headers,
    )
    assert res3.status_code == 400
    assert "underage" in res3.json()["detail"].lower() or "minor" in res3.json()["detail"].lower()


# --- 2. Human Review Queue & Pre-Publication Feed Isolation ---

@pytest.mark.asyncio
async def test_human_review_queue_and_feed_isolation(async_client: AsyncClient, trust_safety_test_users, db_session: AsyncSession):
    """
    CRITICAL RULE TEST:
    'Do not publish content that requires human review before its status has been resolved.'
    1. Submit borderline content (e.g. 'named and shamed / watch out for this guy').
    2. Verify post is stored with moderation_status = 'PENDING_REVIEW'.
    3. Verify public feed GET /api/v1/posts DOES NOT return this post.
    4. Verify moderator GET /api/v1/admin/moderation/queue returns this post.
    5. Moderator calls POST /api/v1/admin/moderation/POST/{id}/decision with action='APPROVE'.
    6. Verify public feed GET /api/v1/posts NOW returns the approved post!
    """
    alice = trust_safety_test_users["alice"]
    mod = trust_safety_test_users["mod"]
    alice_headers = {"Authorization": f"Bearer {alice['token']}"}
    mod_headers = {"Authorization": f"Bearer {mod['token']}"}

    # Step 1: Create borderline post
    post_res = await async_client.post(
        "/api/v1/posts",
        json={
            "content": "Named and shamed: watch out for this guy at the library party",
            "tag": "campus life",
            "is_sensitive": False,
        },
        headers=alice_headers,
    )
    assert post_res.status_code == 201
    post_id = post_res.json()["id"]

    # Step 2: Verify in DB that status is PENDING_REVIEW
    p_row = (await db_session.execute(select(Post).where(Post.id == uuid.UUID(post_id)))).scalar_one()
    assert p_row.moderation_status == "PENDING_REVIEW"

    # Step 3: Public feed query MUST NOT contain this post
    feed_res = await async_client.get("/api/v1/posts", headers=alice_headers)
    assert feed_res.status_code == 200
    feed_post_ids = [p["id"] for p in feed_res.json()["items"]]
    assert post_id not in feed_post_ids, "Content in PENDING_REVIEW was leaked into public feed!"

    # Step 4: Moderator checks moderation review queue
    queue_res = await async_client.get("/api/v1/admin/moderation/queue", headers=mod_headers)
    assert queue_res.status_code == 200
    queue_ids = [item["target_id"] for item in queue_res.json()["items"]]
    assert post_id in queue_ids

    # Step 5: Moderator approves content
    decision_res = await async_client.post(
        f"/api/v1/admin/moderation/POST/{post_id}/decision",
        json={"action": "APPROVE", "reason": "Reviewed and compliant with platform policies"},
        headers=mod_headers,
    )
    assert decision_res.status_code == 200
    assert decision_res.json()["status"] == "PUBLISHED"

    # Step 6: Public feed query NOW returns the post
    feed_res_after = await async_client.get("/api/v1/posts", headers=alice_headers)
    assert feed_res_after.status_code == 200
    feed_post_ids_after = [p["id"] for p in feed_res_after.json()["items"]]
    assert post_id in feed_post_ids_after, "Approved post should now appear in the public feed!"


# --- 3. Administrative Security, Role-Based Access & MFA ---

@pytest.mark.asyncio
async def test_role_based_access_control(async_client: AsyncClient, trust_safety_test_users):
    """
    Test role boundaries:
    - Normal user calling /admin/* -> 403 Forbidden
    - Moderator calling /admin/overview -> 200 OK
    - Moderator attempting ACCOUNT_BANNED -> 403 Forbidden (requires Security Admin)
    - Security Admin calling ACCOUNT_BANNED -> 201 Created
    """
    alice = trust_safety_test_users["alice"]
    mod = trust_safety_test_users["mod"]
    sec = trust_safety_test_users["sec"]
    bad = trust_safety_test_users["bad"]

    alice_headers = {"Authorization": f"Bearer {alice['token']}"}
    mod_headers = {"Authorization": f"Bearer {mod['token']}"}
    sec_headers = {"Authorization": f"Bearer {sec['token']}"}

    # 1. Normal user blocked from admin endpoints
    res_overview = await async_client.get("/api/v1/admin/overview", headers=alice_headers)
    assert res_overview.status_code == 403

    # 2. Moderator can access overview
    res_mod_overview = await async_client.get("/api/v1/admin/overview", headers=mod_headers)
    assert res_mod_overview.status_code == 200
    assert "pending_reports_count" in res_mod_overview.json()

    # 3. Moderator cannot execute account bans
    res_mod_ban = await async_client.post(
        "/api/v1/admin/restrictions",
        json={
            "target_persona_id": str(bad["persona"].id),
            "action_type": "ACCOUNT_BANNED",
            "reason": "Severe repeated abuse",
            "strike_count": 3,
        },
        headers=mod_headers,
    )
    assert res_mod_ban.status_code == 403
    assert "security administrator" in res_mod_ban.json()["detail"].lower()

    # 4. Security Admin CAN execute account bans
    res_sec_ban = await async_client.post(
        "/api/v1/admin/restrictions",
        json={
            "target_persona_id": str(bad["persona"].id),
            "action_type": "ACCOUNT_BANNED",
            "reason": "Severe repeated abuse",
            "strike_count": 3,
        },
        headers=sec_headers,
    )
    assert res_sec_ban.status_code == 201
    assert res_sec_ban.json()["action_type"] == "ACCOUNT_BANNED"


@pytest.mark.asyncio
async def test_mfa_stepup_for_security_admin(async_client: AsyncClient, trust_safety_test_users):
    """Test TOTP MFA setup, verification, and step-up authentication guard for sensitive admin operations."""
    sec = trust_safety_test_users["sec"]
    bad = trust_safety_test_users["bad"]
    sec_headers = {"Authorization": f"Bearer {sec['token']}"}

    # Step 1: Initiate MFA setup
    setup_res = await async_client.post("/api/v1/admin/mfa/setup", headers=sec_headers)
    assert setup_res.status_code == 200
    secret = setup_res.json()["secret"]
    assert len(secret) >= 16

    # Step 2: Generate TOTP code and verify
    totp_code = get_totp_code(secret)
    verify_res = await async_client.post("/api/v1/admin/mfa/verify", json={"code": totp_code}, headers=sec_headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["mfa_enabled"] is True

    # Step 3: Attempt ACCOUNT_BANNED without X-Admin-MFA header -> 401 Unauthorized
    ban_without_mfa = await async_client.post(
        "/api/v1/admin/restrictions",
        json={
            "target_persona_id": str(bad["persona"].id),
            "action_type": "ACCOUNT_BANNED",
            "reason": "Security violation",
        },
        headers=sec_headers,
    )
    assert ban_without_mfa.status_code == 401
    assert "mfa" in ban_without_mfa.json()["detail"].lower()

    # Step 4: Perform ACCOUNT_BANNED with valid X-Admin-MFA header -> 201 Created
    fresh_code = get_totp_code(secret)
    mfa_headers = {**sec_headers, "X-Admin-MFA": fresh_code}
    ban_with_mfa = await async_client.post(
        "/api/v1/admin/restrictions",
        json={
            "target_persona_id": str(bad["persona"].id),
            "action_type": "ACCOUNT_BANNED",
            "reason": "Security violation with MFA authorization",
        },
        headers=mfa_headers,
    )
    assert ban_with_mfa.status_code == 201


# --- 4. Appeals Lifecycle ---

@pytest.mark.asyncio
async def test_appeals_lifecycle(async_client: AsyncClient, trust_safety_test_users, db_session: AsyncSession):
    """
    Test user safety appeal process:
    1. Content is taken down by moderation.
    2. User submits appeal via POST /api/v1/appeals.
    3. User checks their appeal status via GET /api/v1/appeals/me.
    4. Moderator reviews and approves appeal via POST /api/v1/admin/appeals/{id}/review.
    5. Content is restored (is_deleted = False, moderation_status = 'PUBLISHED').
    """
    alice = trust_safety_test_users["alice"]
    mod = trust_safety_test_users["mod"]
    alice_headers = {"Authorization": f"Bearer {alice['token']}"}
    mod_headers = {"Authorization": f"Bearer {mod['token']}"}

    # Create post
    p_res = await async_client.post(
        "/api/v1/posts",
        json={"content": "Misunderstood artistic confession from late night studio", "tag": "confessions", "is_sensitive": False},
        headers=alice_headers,
    )
    post_id = p_res.json()["id"]

    # Moderator takes down content
    take_down_res = await async_client.post(
        f"/api/v1/admin/moderation/POST/{post_id}/decision",
        json={"action": "TAKEDOWN", "reason": "Alleged policy breach"},
        headers=mod_headers,
    )
    action_id = take_down_res.json()["moderation_action_id"]
    assert action_id is not None

    # Alice submits appeal
    appeal_res = await async_client.post(
        "/api/v1/appeals",
        json={
            "moderation_action_id": action_id,
            "reason": "This was an innocent artistic piece and contained zero real names or threats.",
        },
        headers=alice_headers,
    )
    assert appeal_res.status_code == 201
    appeal_id = appeal_res.json()["id"]
    assert appeal_res.json()["status"] == "PENDING"

    # Alice views their appeals
    my_appeals_res = await async_client.get("/api/v1/appeals/me", headers=alice_headers)
    assert my_appeals_res.status_code == 200
    assert any(a["id"] == appeal_id for a in my_appeals_res.json())

    # Moderator reviews and approves appeal
    review_res = await async_client.post(
        f"/api/v1/admin/appeals/{appeal_id}/review",
        json={"decision": "APPROVE", "resolution_notes": "Reviewed by senior moderator; restored as compliant."},
        headers=mod_headers,
    )
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "APPROVED"

    # Verify post is restored
    post_row = (await db_session.execute(select(Post).where(Post.id == uuid.UUID(post_id)))).scalar_one()
    assert post_row.is_deleted is False
    assert post_row.moderation_status == "PUBLISHED"


# --- 5. User Safety: Blocks, Account Deletion & Zero Vault Leakage ---

@pytest.mark.asyncio
async def test_block_management_and_account_deletion(async_client: AsyncClient, trust_safety_test_users, db_session: AsyncSession):
    """
    Test user safety features:
    1. Caller blocks persona and inspects GET /api/v1/blocks.
    2. Caller unblocks persona and verifies block is removed.
    3. Caller deletes their account via DELETE /api/v1/auth/account.
    4. Verify account is banned/deleted and subsequent requests rejected with 403.
    """
    alice = trust_safety_test_users["alice"]
    bad = trust_safety_test_users["bad"]
    alice_headers = {"Authorization": f"Bearer {alice['token']}"}

    # 1. Block BadActor
    block_res = await async_client.post(
        "/api/v1/blocks",
        json={"blocked_persona_id": str(bad["persona"].id), "reason": "Toxic behavior"},
        headers=alice_headers,
    )
    assert block_res.status_code == 201

    # 2. View block list
    blocks_res = await async_client.get("/api/v1/blocks", headers=alice_headers)
    assert blocks_res.status_code == 200
    assert any(b["persona_id"] == str(bad["persona"].id) for b in blocks_res.json())

    # 3. Unblock BadActor
    unblock_res = await async_client.delete(f"/api/v1/blocks/{bad['persona'].id}", headers=alice_headers)
    assert unblock_res.status_code == 204

    # 4. Delete account
    del_res = await async_client.delete("/api/v1/auth/account", headers=alice_headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "DELETED"

    # 5. Subsequent request is rejected
    check_me = await async_client.get("/api/v1/auth/me", headers=alice_headers)
    assert check_me.status_code == 403


@pytest.mark.asyncio
async def test_zero_identity_vault_leakage(async_client: AsyncClient, trust_safety_test_users):
    """
    Test that admin endpoints strictly leak ZERO identifiable information:
    - No raw emails or plaintext hashes.
    - No Supabase auth UUIDs.
    - Only display names, quotas, strike counts, and roles.
    """
    sec = trust_safety_test_users["sec"]
    sec_headers = {"Authorization": f"Bearer {sec['token']}"}

    accounts_res = await async_client.get("/api/v1/admin/accounts", headers=sec_headers)
    assert accounts_res.status_code == 200
    data = accounts_res.json()
    assert data["total"] >= 1

    for item in data["items"]:
        # Verify no email fields
        assert "email" not in item
        assert "email_hash" not in item
        assert "supabase_user_id" not in item
        # Verify pseudonym display names are present
        assert "persona_display_names" in item
        assert "strike_count" in item
