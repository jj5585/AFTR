import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import create_test_jwt, hash_token, hash_recipient_email
from backend.app.models.account import Account, AccountStatus
from backend.app.models.persona import Persona
from backend.app.models.invitation import Invitation, InvitationStatus
from backend.app.services.age_assurance import AgeAssuranceEngine


@pytest.fixture
async def setup_alice_account(db_session: AsyncSession):
    """Seed Alice with an active account, 3 quota, and an anonymous persona."""
    alice_uuid = uuid.uuid4()
    account = Account(
        supabase_user_id=alice_uuid,
        email_hash=hash_recipient_email("alice@campus.edu"),
        is_age_verified=True,
        birth_year=2002,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
    )
    db_session.add(account)
    await db_session.flush()

    persona = Persona(
        account_id=account.id,
        display_name="ShadowFox",
        avatar_seed="fox-avatar",
        bio="Alice's anonymous persona",
        is_active=True,
    )
    db_session.add(persona)
    await db_session.commit()

    token = create_test_jwt(alice_uuid, "alice@campus.edu")
    return {"account": account, "persona": persona, "token": token, "uuid": alice_uuid}


@pytest.mark.asyncio
async def test_create_invitation_success(async_client: AsyncClient, setup_alice_account: dict):
    headers = {"Authorization": f"Bearer {setup_alice_account['token']}"}
    response = await async_client.post(
        "/api/v1/invitations",
        json={"recipient_email": "friend@university.edu"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert "token" in data
    assert "invite_url" in data
    assert data["status"] == "PENDING"
    assert "expires_at" in data


@pytest.mark.asyncio
async def test_invitation_quota_exhaustion(async_client: AsyncClient, setup_alice_account: dict, db_session: AsyncSession):
    """Alice starts with 3 quota. After issuing 3 invites, 4th must fail."""
    headers = {"Authorization": f"Bearer {setup_alice_account['token']}"}

    for i in range(3):
        res = await async_client.post(
            "/api/v1/invitations",
            json={"recipient_email": f"friend{i}@example.com"},
            headers=headers,
        )
        assert res.status_code == 201

    # 4th invitation must be rejected
    res_exhausted = await async_client.post(
        "/api/v1/invitations",
        json={"recipient_email": "friend_extra@example.com"},
        headers=headers,
    )
    assert res_exhausted.status_code == 400
    assert "quota exhausted" in res_exhausted.json()["detail"].lower()


@pytest.mark.asyncio
async def test_prevent_self_invitation(async_client: AsyncClient, setup_alice_account: dict):
    """User cannot invite their own email."""
    headers = {"Authorization": f"Bearer {setup_alice_account['token']}"}
    response = await async_client.post(
        "/api/v1/invitations",
        json={"recipient_email": "alice@campus.edu"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "own registered email" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_validate_invitation_all_states(async_client: AsyncClient, db_session: AsyncSession, setup_alice_account: dict):
    """Test every invitation state on /validate: VALID, NOT_FOUND, EXPIRED, REVOKED, ALREADY_REDEEMED."""
    now = datetime.now(timezone.utc)
    acc = setup_alice_account["account"]

    # 1. NOT_FOUND
    res_nf = await async_client.post("/api/v1/invitations/validate", json={"token": "completely-fake-token-12345"})
    assert res_nf.status_code == 200
    assert res_nf.json()["status"] == "NOT_FOUND"
    assert res_nf.json()["is_valid"] is False

    # 2. VALID
    inv_valid = Invitation(
        inviter_account_id=acc.id,
        token_hash=hash_token("test-token-valid-state-1234"),
        recipient_hash=hash_recipient_email("bob@example.com"),
        status=InvitationStatus.PENDING,
        created_at=now,
        expires_at=now + timedelta(hours=72),
    )
    db_session.add(inv_valid)

    # 3. EXPIRED
    inv_expired = Invitation(
        inviter_account_id=acc.id,
        token_hash=hash_token("test-token-expired-state-1234"),
        recipient_hash=hash_recipient_email("bob@example.com"),
        status=InvitationStatus.EXPIRED,
        created_at=now - timedelta(hours=75),
        expires_at=now - timedelta(hours=3),
    )
    db_session.add(inv_expired)

    # 4. REVOKED
    inv_revoked = Invitation(
        inviter_account_id=acc.id,
        token_hash=hash_token("test-token-revoked-state-1234"),
        recipient_hash=hash_recipient_email("bob@example.com"),
        status=InvitationStatus.REVOKED,
        created_at=now - timedelta(hours=10),
        expires_at=now + timedelta(hours=62),
        revoked_at=now - timedelta(hours=1),
    )
    db_session.add(inv_revoked)

    # Create separate redeemer account for used invitation test to satisfy chk_no_self_invitation
    bob_account = Account(
        supabase_user_id=uuid.uuid4(),
        email_hash="bob-redeemer-email-hash",
        is_age_verified=True,
    )
    db_session.add(bob_account)
    await db_session.flush()

    # 5. ALREADY_REDEEMED
    inv_used = Invitation(
        inviter_account_id=acc.id,
        token_hash=hash_token("test-token-used-state-1234"),
        recipient_hash=hash_recipient_email("bob@example.com"),
        status=InvitationStatus.USED,
        created_at=now - timedelta(hours=20),
        expires_at=now + timedelta(hours=52),
        used_by_account_id=bob_account.id,
        used_at=now - timedelta(hours=5),
    )
    db_session.add(inv_used)
    await db_session.commit()

    # Validate VALID
    res_val = await async_client.post("/api/v1/invitations/validate", json={"token": "test-token-valid-state-1234"})
    assert res_val.json()["status"] == "VALID"
    assert res_val.json()["is_valid"] is True

    # Validate EXPIRED
    res_exp = await async_client.post("/api/v1/invitations/validate", json={"token": "test-token-expired-state-1234"})
    assert res_exp.json()["status"] == "EXPIRED"
    assert res_exp.json()["is_valid"] is False

    # Validate REVOKED
    res_rev = await async_client.post("/api/v1/invitations/validate", json={"token": "test-token-revoked-state-1234"})
    assert res_rev.json()["status"] == "REVOKED"
    assert res_rev.json()["is_valid"] is False

    # Validate ALREADY_REDEEMED
    res_usd = await async_client.post("/api/v1/invitations/validate", json={"token": "test-token-used-state-1234"})
    assert res_usd.json()["status"] == "ALREADY_REDEEMED"
    assert res_usd.json()["is_valid"] is False


@pytest.mark.asyncio
async def test_claim_invitation_recipient_binding(async_client: AsyncClient, db_session: AsyncSession, setup_alice_account: dict):
    """Claiming must enforce email matching the invitation recipient binding."""
    now = datetime.now(timezone.utc)
    raw_token = "claim-test-token-12345678"
    inv = Invitation(
        inviter_account_id=setup_alice_account["account"].id,
        token_hash=hash_token(raw_token),
        recipient_hash=hash_recipient_email("intended@target.edu"),
        status=InvitationStatus.PENDING,
        created_at=now,
        expires_at=now + timedelta(hours=72),
    )
    db_session.add(inv)
    await db_session.commit()

    # 1. Claim with mismatching email -> 403 Forbidden
    res_bad = await async_client.post(
        "/api/v1/invitations/claim",
        json={"token": raw_token, "recipient_email": "imposter@target.edu"},
    )
    assert res_bad.status_code == 403
    assert "recipient verification failed" in res_bad.json()["detail"].lower()

    # 2. Claim with matching email -> 200 OK with claim ticket
    res_ok = await async_client.post(
        "/api/v1/invitations/claim",
        json={"token": raw_token, "recipient_email": "intended@target.edu"},
    )
    assert res_ok.status_code == 200
    data = res_ok.json()
    assert data["success"] is True
    assert "claim_ticket" in data


@pytest.mark.asyncio
async def test_revoke_invitation(async_client: AsyncClient, setup_alice_account: dict):
    headers = {"Authorization": f"Bearer {setup_alice_account['token']}"}

    # Create invitation
    res_create = await async_client.post(
        "/api/v1/invitations",
        json={"recipient_email": "to_revoke@example.com"},
        headers=headers,
    )
    inv_id = res_create.json()["id"]

    # Revoke invitation
    res_revoke = await async_client.delete(f"/api/v1/invitations/{inv_id}", headers=headers)
    assert res_revoke.status_code == 200
    assert "revoked" in res_revoke.json()["message"].lower()

    # Validate token is now REVOKED
    raw_token = res_create.json()["token"]
    res_val = await async_client.post("/api/v1/invitations/validate", json={"token": raw_token})
    assert res_val.json()["status"] == "REVOKED"


@pytest.mark.asyncio
async def test_full_onboarding_and_redeem_flow(async_client: AsyncClient, setup_alice_account: dict):
    """
    Test complete lifecycle:
    1. Alice creates invitation for Bob.
    2. Bob validates invitation.
    3. Bob claims invitation with his email.
    4. Bob undergoes Age Assurance (18+ verified).
    5. Bob redeems invitation and establishes anonymous persona.
    6. Bob accesses protected AFTR routes.
    """
    alice_headers = {"Authorization": f"Bearer {setup_alice_account['token']}"}

    # 1. Issue invite
    res_issue = await async_client.post(
        "/api/v1/invitations",
        json={"recipient_email": "bob@somewhere.org"},
        headers=alice_headers,
    )
    raw_token = res_issue.json()["token"]

    # 2. Validate
    res_val = await async_client.post("/api/v1/invitations/validate", json={"token": raw_token})
    assert res_val.json()["status"] == "VALID"

    # 3. Claim
    res_claim = await async_client.post(
        "/api/v1/invitations/claim",
        json={"token": raw_token, "recipient_email": "bob@somewhere.org"},
    )
    claim_ticket = res_claim.json()["claim_ticket"]

    # 4. Age Assurance (18+ check)
    # Underage check (born 2015 -> ~11 years old)
    res_underage = await async_client.post(
        "/api/v1/auth/age/verify",
        json={
            "email": "bob@somewhere.org",
            "birth_date": "2015-05-15",
            "evidence_type": "GOVERNMENT_ID_VERIFICATION",
        },
    )
    assert res_underage.status_code == 400
    assert "must be at least 18" in res_underage.json()["detail"].lower()

    # Legitimate Adult check (born 2001 -> ~25 years old)
    res_adult = await async_client.post(
        "/api/v1/auth/age/verify",
        json={
            "email": "bob@somewhere.org",
            "birth_date": "2001-08-20",
            "evidence_type": "GOVERNMENT_ID_VERIFICATION",
        },
    )
    assert res_adult.status_code == 200
    age_proof = res_adult.json()["proof_token"]

    # 5. Redeem & Setup Anonymous Persona
    bob_supabase_uuid = uuid.uuid4()
    res_redeem = await async_client.post(
        "/api/v1/invitations/redeem",
        json={
            "claim_ticket": claim_ticket,
            "age_proof_token": age_proof,
            "supabase_user_id": str(bob_supabase_uuid),
            "display_name": "NeonRaven",
            "avatar_seed": "raven-dark-avatar",
            "declared_campus": "Pacific State University",
            "bio": "Curious explorer of campus nightlife.",
            "accepted_policy": True,
        },
    )
    assert res_redeem.status_code == 200
    redeem_data = res_redeem.json()
    assert redeem_data["success"] is True
    assert redeem_data["display_name"] == "NeonRaven"
    assert redeem_data["invite_quota"] == 3

    # 6. Bob can now authenticate with his Supabase JWT and access /auth/me
    bob_token = create_test_jwt(bob_supabase_uuid, "bob@somewhere.org")
    bob_headers = {"Authorization": f"Bearer {bob_token}"}
    res_me = await async_client.get("/api/v1/auth/me", headers=bob_headers)
    assert res_me.status_code == 200
    me_data = res_me.json()
    assert me_data["is_age_verified"] is True
    assert me_data["persona"]["display_name"] == "NeonRaven"
    assert me_data["persona"]["declared_campus"] == "Pacific State University"

    # Attempting to re-redeem the same token must fail
    res_double = await async_client.post(
        "/api/v1/invitations/redeem",
        json={
            "claim_ticket": claim_ticket,
            "age_proof_token": age_proof,
            "supabase_user_id": str(uuid.uuid4()),
            "display_name": "DoubleRedeemer",
            "avatar_seed": "seed-double",
            "accepted_policy": True,
        },
    )
    assert res_double.status_code == 400
