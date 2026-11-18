import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import create_test_jwt, hash_recipient_email
from backend.app.models.account import Account, AccountStatus
from backend.app.models.persona import Persona, CampusAffiliation


@pytest.fixture
async def setup_test_member(db_session: AsyncSession):
    user_uuid = uuid.uuid4()
    account = Account(
        supabase_user_id=user_uuid,
        email_hash=hash_recipient_email("member@example.com"),
        is_age_verified=True,
        birth_year=2000,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
    )
    db_session.add(account)
    await db_session.flush()

    persona = Persona(
        account_id=account.id,
        display_name="MidnightScholar",
        avatar_seed="scholar-seed",
        bio="Anonymous research persona",
        is_active=True,
    )
    db_session.add(persona)
    await db_session.flush()

    campus = CampusAffiliation(
        persona_id=persona.id,
        campus_name="Bay Area University",
        is_primary=True,
    )
    db_session.add(campus)
    await db_session.commit()

    token = create_test_jwt(user_uuid, "member@example.com")
    return {"account": account, "persona": persona, "token": token, "uuid": user_uuid}


@pytest.mark.asyncio
async def test_age_assurance_workflow(async_client: AsyncClient):
    # 1. Initiate session
    res_init = await async_client.post(
        "/api/v1/auth/age/initiate",
        json={"email": "verifier@example.com"},
    )
    assert res_init.status_code == 200
    data_init = res_init.json()
    assert "session_id" in data_init
    assert data_init["requirements"]["min_age"] == 18

    # 2. Reject underage
    res_under = await async_client.post(
        "/api/v1/auth/age/verify",
        json={
            "email": "verifier@example.com",
            "birth_date": "2012-04-10",
            "evidence_type": "GOVERNMENT_ID_VERIFICATION",
        },
    )
    assert res_under.status_code == 400
    assert "at least 18" in res_under.json()["detail"].lower()

    # 3. Accept adult
    res_adult = await async_client.post(
        "/api/v1/auth/age/verify",
        json={
            "email": "verifier@example.com",
            "birth_date": "2000-01-15",
            "evidence_type": "GOVERNMENT_ID_VERIFICATION",
        },
    )
    assert res_adult.status_code == 200
    assert res_adult.json()["is_verified"] is True
    assert "proof_token" in res_adult.json()


@pytest.mark.asyncio
async def test_auth_me_authenticated(async_client: AsyncClient, setup_test_member: dict):
    headers = {"Authorization": f"Bearer {setup_test_member['token']}"}
    response = await async_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_age_verified"] is True
    assert data["status"] == "ACTIVE"
    assert data["persona"]["display_name"] == "MidnightScholar"
    assert data["persona"]["declared_campus"] == "Bay Area University"
    # Verify no supabase user ID or real email is in response
    assert "supabase_user_id" not in data
    assert "email" not in data


@pytest.mark.asyncio
async def test_auth_me_unauthorized_token(async_client: AsyncClient):
    # No auth header -> 401
    res_no_auth = await async_client.get("/api/v1/auth/me")
    assert res_no_auth.status_code == 401

    # Invalid token -> 401
    res_invalid = await async_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer fake.invalid.token"})
    assert res_invalid.status_code == 401


@pytest.mark.asyncio
async def test_auth_uninvited_account_blocked(async_client: AsyncClient):
    """
    If a user has a Supabase JWT but never completed the invitation gate (no Account row),
    access to protected endpoints must be strictly blocked with HTTP 403.
    """
    uninvited_uuid = uuid.uuid4()
    uninvited_token = create_test_jwt(uninvited_uuid, "uninvited@intruder.com")
    headers = {"Authorization": f"Bearer {uninvited_token}"}

    response = await async_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 403
    assert "invitation required" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_logout_and_password_recovery(async_client: AsyncClient, setup_test_member: dict):
    headers = {"Authorization": f"Bearer {setup_test_member['token']}"}
    res_logout = await async_client.post("/api/v1/auth/logout", headers=headers)
    assert res_logout.status_code == 200

    res_rec = await async_client.post(
        "/api/v1/auth/recover-password",
        json={"email": "member@example.com"},
    )
    assert res_rec.status_code == 200
    assert "password recovery instructions" in res_rec.json()["message"].lower()
