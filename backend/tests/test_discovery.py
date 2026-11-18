import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.security import create_test_jwt
from backend.app.core.encryption import decrypt_message_content
from backend.app.models.account import Account, AccountStatus
from backend.app.models.persona import Persona, CampusAffiliation, Interest, PersonaInterest
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
async def discovery_test_users(db_session: AsyncSession):
    """
    Setup 3 test accounts and personas:
    1. Alice (ShadowFox) - Bay Area University - Intention: CASUAL
    2. Bob (NeonGhost) - West Coast College - Intention: CASUAL
    3. Charlie (MidnightEcho) - Bay Area University - Intention: SERIOUS
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
        is_discoverable=True,
        relationship_intention="CASUAL",
    )
    p_bob = Persona(
        account_id=acc_bob.id,
        display_name="NeonGhost",
        avatar_seed="ghost-seed",
        bio="Philosophy & beats.",
        is_active=True,
        is_discoverable=True,
        relationship_intention="CASUAL",
    )
    p_charlie = Persona(
        account_id=acc_charlie.id,
        display_name="MidnightEcho",
        avatar_seed="echo-seed",
        bio="Night thoughts.",
        is_active=True,
        is_discoverable=True,
        relationship_intention="SERIOUS",
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
    aff_charlie = CampusAffiliation(
        persona_id=p_charlie.id,
        campus_name="Bay Area University",
        campus_code="BAU",
        is_primary=True,
    )
    db_session.add_all([aff_alice, aff_bob, aff_charlie])
    await db_session.flush()

    token_alice = create_test_jwt(alice_sub, "alice@example.com")
    token_bob = create_test_jwt(bob_sub, "bob@example.com")
    token_charlie = create_test_jwt(charlie_sub, "charlie@example.com")

    return {
        "alice": {"account": acc_alice, "persona": p_alice, "token": token_alice},
        "bob": {"account": acc_bob, "persona": p_bob, "token": token_bob},
        "charlie": {"account": acc_charlie, "persona": p_charlie, "token": token_charlie},
    }


@pytest.mark.asyncio
async def test_get_interests_taxonomy(
    async_client: AsyncClient,
    discovery_test_users: dict,
):
    """Verify that interest taxonomy is seeded and returned."""
    token = discovery_test_users["alice"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.get("/api/v1/discovery/interests", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "interests" in data
    assert len(data["interests"]) >= 10
    names = [i["name"] for i in data["interests"]]
    assert "Night Owl" in names
    assert "Late Talks" in names


@pytest.mark.asyncio
async def test_discovery_preferences_update_and_get(
    async_client: AsyncClient,
    discovery_test_users: dict,
):
    """Verify caller can update discoverability, intentions, interests, and private preferences."""
    token = discovery_test_users["alice"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch interests first to get UUIDs
    int_res = await async_client.get("/api/v1/discovery/interests", headers=headers)
    assert int_res.status_code == 200
    all_interests = int_res.json()["interests"]
    chosen_ids = [all_interests[0]["id"], all_interests[1]["id"]]

    # Update preferences
    update_payload = {
        "is_discoverable": True,
        "relationship_intention": "CASUAL",
        "min_age_preference": 20,
        "max_age_preference": 28,
        "dating_preferences": {"open_to_vibes": True, "secret_interests": ["jazz"]},
        "interest_ids": chosen_ids,
    }
    put_res = await async_client.put(
        "/api/v1/discovery/preferences",
        headers=headers,
        json=update_payload,
    )
    assert put_res.status_code == 200
    pref_data = put_res.json()
    assert pref_data["is_discoverable"] is True
    assert pref_data["relationship_intention"] == "CASUAL"
    assert pref_data["min_age_preference"] == 20
    assert pref_data["max_age_preference"] == 28
    assert pref_data["dating_preferences"] == {"open_to_vibes": True, "secret_interests": ["jazz"]}
    assert len(pref_data["interests"]) == 2

    # Get preferences
    get_res = await async_client.get("/api/v1/discovery/preferences", headers=headers)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["relationship_intention"] == "CASUAL"
    assert len(get_data["interests"]) == 2


@pytest.mark.asyncio
async def test_discovery_feed_card_generation_and_zero_identity_leakage(
    async_client: AsyncClient,
    discovery_test_users: dict,
):
    """
    Verify anonymous discovery cards:
    - Zero identity leakage (no emails, auth IDs, or real names)
    - Sensitive dating_preferences_json is never returned
    - Cards contain compatibility score, public pseudonym, and declared campus
    """
    token_alice = discovery_test_users["alice"]["token"]
    headers_alice = {"Authorization": f"Bearer {token_alice}"}

    res = await async_client.get("/api/v1/discovery/feed", headers=headers_alice)
    assert res.status_code == 200
    feed = res.json()
    assert "items" in feed
    items = feed["items"]

    # Alice should not see herself
    alice_persona_id = str(discovery_test_users["alice"]["persona"].id)
    seen_ids = [card["persona"]["id"] for card in items]
    assert alice_persona_id not in seen_ids

    # Should see Bob and Charlie
    bob_persona_id = str(discovery_test_users["bob"]["persona"].id)
    charlie_persona_id = str(discovery_test_users["charlie"]["persona"].id)
    assert bob_persona_id in seen_ids
    assert charlie_persona_id in seen_ids

    # Check anonymity & card schema on all items
    for card in items:
        persona = card["persona"]
        assert "display_name" in persona
        assert "avatar_seed" in persona
        assert "declared_campus" in persona
        assert card["compatibility_score"] >= 50.0

        # CRITICAL PRIVACY CHECKS: Identity data must NOT leak
        assert "email" not in persona
        assert "email_hash" not in persona
        assert "supabase_user_id" not in persona
        assert "account_id" not in persona
        assert "dating_preferences" not in card
        assert "dating_preferences_json" not in card


@pytest.mark.asyncio
async def test_opt_in_discoverability_rule(
    async_client: AsyncClient,
    discovery_test_users: dict,
):
    """
    Rule: Users must opt into discoverability.
    - If a user sets is_discoverable=False, they are hidden from other feeds.
    - If caller is not discoverable, accessing the discovery feed is 403 Forbidden.
    """
    token_bob = discovery_test_users["bob"]["token"]
    token_alice = discovery_test_users["alice"]["token"]

    # Bob toggles is_discoverable = False
    await async_client.put(
        "/api/v1/discovery/preferences",
        headers={"Authorization": f"Bearer {token_bob}"},
        json={"is_discoverable": False},
    )

    # Alice queries feed -> Bob should not appear
    res = await async_client.get(
        "/api/v1/discovery/feed",
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert res.status_code == 200
    items = res.json()["items"]
    seen_ids = [card["persona"]["id"] for card in items]
    bob_id = str(discovery_test_users["bob"]["persona"].id)
    assert bob_id not in seen_ids

    # Now Bob tries to view discovery feed while not discoverable
    res_bob = await async_client.get(
        "/api/v1/discovery/feed",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert res_bob.status_code == 403
    assert "opt into discoverability" in res_bob.json()["detail"].lower()


@pytest.mark.asyncio
async def test_discovery_filtering(
    async_client: AsyncClient,
    discovery_test_users: dict,
):
    """Test filtering discovery cards by optional campus and relationship intention."""
    token_alice = discovery_test_users["alice"]["token"]
    headers = {"Authorization": f"Bearer {token_alice}"}

    # Filter by intention = SERIOUS (Charlie has SERIOUS, Bob has CASUAL)
    res_intention = await async_client.get(
        "/api/v1/discovery/feed?intention=SERIOUS",
        headers=headers,
    )
    assert res_intention.status_code == 200
    items = res_intention.json()["items"]
    for card in items:
        assert card["relationship_intention"] == "SERIOUS"

    # Filter by campus = West Coast College (Bob is at West Coast College)
    res_campus = await async_client.get(
        "/api/v1/discovery/feed?campus=West+Coast",
        headers=headers,
    )
    assert res_campus.status_code == 200
    items = res_campus.json()["items"]
    for card in items:
        assert "West Coast" in card["persona"]["declared_campus"]


@pytest.mark.asyncio
async def test_connection_request_lifecycle(
    async_client: AsyncClient,
    discovery_test_users: dict,
    db_session: AsyncSession,
):
    """
    Test complete bilateral connection request flow:
    1. Alice sends connection request to Bob with intro note.
    2. Request is created with PENDING status.
    3. Bob sees incoming request; Alice sees outgoing request.
    4. Bob accepts request.
    5. Request becomes ACCEPTED.
    6. Canonical Match record is generated.
    7. Private Conversation is unlocked with ConversationParticipant rows for both.
    8. Initial intro note is saved as the first Message.
    9. Both Alice and Bob see each other in their mutual matches.
    """
    token_alice = discovery_test_users["alice"]["token"]
    token_bob = discovery_test_users["bob"]["token"]
    bob_persona_id = str(discovery_test_users["bob"]["persona"].id)

    # 1. Alice sends request to Bob
    req_res = await async_client.post(
        "/api/v1/connections/request",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={
            "recipient_persona_id": bob_persona_id,
            "note": "Loved your philosophy post earlier!",
        },
    )
    assert req_res.status_code == 201
    req_data = req_res.json()
    assert req_data["status"] == "PENDING"
    assert req_data["note"] == "Loved your philosophy post earlier!"
    req_id = req_data["id"]

    # 2. Check requests list
    # Bob's incoming
    bob_reqs = await async_client.get(
        "/api/v1/connections/requests",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert bob_reqs.status_code == 200
    assert len(bob_reqs.json()["incoming"]) == 1
    assert bob_reqs.json()["incoming"][0]["id"] == req_id

    # Alice's outgoing
    alice_reqs = await async_client.get(
        "/api/v1/connections/requests",
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert alice_reqs.status_code == 200
    assert len(alice_reqs.json()["outgoing"]) == 1
    assert alice_reqs.json()["outgoing"][0]["id"] == req_id

    # 3. Bob accepts request
    accept_res = await async_client.post(
        f"/api/v1/connections/requests/{req_id}/accept",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert accept_res.status_code == 200
    accept_data = accept_res.json()
    assert accept_data["request"]["status"] == "ACCEPTED"
    assert "match" in accept_data
    assert accept_data["match"]["conversation_id"] is not None

    conv_id = accept_data["match"]["conversation_id"]

    # 4. Verify conversation and message in DB
    conv_stmt = select(Conversation).where(Conversation.id == uuid.UUID(conv_id))
    conv = (await db_session.execute(conv_stmt)).scalar_one_or_none()
    assert conv is not None
    assert conv.is_active is True

    # Verify participants
    part_stmt = select(ConversationParticipant).where(ConversationParticipant.conversation_id == conv.id)
    participants = list((await db_session.execute(part_stmt)).scalars().all())
    assert len(participants) == 2
    participant_ids = {p.persona_id for p in participants}
    assert discovery_test_users["alice"]["persona"].id in participant_ids
    assert discovery_test_users["bob"]["persona"].id in participant_ids

    # Verify intro note was delivered to conversation
    msg_stmt = select(Message).where(Message.conversation_id == conv.id)
    msgs = list((await db_session.execute(msg_stmt)).scalars().all())
    assert len(msgs) == 1
    assert msgs[0].is_encrypted is True
    assert decrypt_message_content(msgs[0].content) == "Loved your philosophy post earlier!"

    # 5. Verify mutual matches endpoint for both users
    alice_matches = await async_client.get(
        "/api/v1/connections/matches",
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert alice_matches.status_code == 200
    assert len(alice_matches.json()["matches"]) == 1
    assert alice_matches.json()["matches"][0]["matched_persona"]["id"] == bob_persona_id

    bob_matches = await async_client.get(
        "/api/v1/connections/matches",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert bob_matches.status_code == 200
    assert len(bob_matches.json()["matches"]) == 1
    assert bob_matches.json()["matches"][0]["matched_persona"]["id"] == str(
        discovery_test_users["alice"]["persona"].id
    )


@pytest.mark.asyncio
async def test_connection_request_reject(
    async_client: AsyncClient,
    discovery_test_users: dict,
):
    """Verify rejecting an incoming connection request."""
    token_alice = discovery_test_users["alice"]["token"]
    token_charlie = discovery_test_users["charlie"]["token"]
    charlie_persona_id = str(discovery_test_users["charlie"]["persona"].id)

    # Alice sends request to Charlie
    req_res = await async_client.post(
        "/api/v1/connections/request",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"recipient_persona_id": charlie_persona_id},
    )
    assert req_res.status_code == 201
    req_id = req_res.json()["id"]

    # Charlie rejects request
    rej_res = await async_client.post(
        f"/api/v1/connections/requests/{req_id}/reject",
        headers={"Authorization": f"Bearer {token_charlie}"},
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "REJECTED"

    # Verify no matches created
    matches_res = await async_client.get(
        "/api/v1/connections/matches",
        headers={"Authorization": f"Bearer {token_charlie}"},
    )
    assert matches_res.status_code == 200
    assert len(matches_res.json()["matches"]) == 0


@pytest.mark.asyncio
async def test_connection_request_withdraw(
    async_client: AsyncClient,
    discovery_test_users: dict,
):
    """Verify sender can withdraw their pending connection request."""
    token_bob = discovery_test_users["bob"]["token"]
    charlie_persona_id = str(discovery_test_users["charlie"]["persona"].id)

    # Bob sends request to Charlie
    req_res = await async_client.post(
        "/api/v1/connections/request",
        headers={"Authorization": f"Bearer {token_bob}"},
        json={"recipient_persona_id": charlie_persona_id, "note": "Hey!"},
    )
    assert req_res.status_code == 201
    req_id = req_res.json()["id"]

    # Bob withdraws request
    with_res = await async_client.post(
        f"/api/v1/connections/requests/{req_id}/withdraw",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert with_res.status_code == 200
    assert with_res.json()["status"] == "WITHDRAWN"


@pytest.mark.asyncio
async def test_anti_self_and_duplicate_connection(
    async_client: AsyncClient,
    discovery_test_users: dict,
):
    """Verify anti-self connection and duplicate connection request guards."""
    token_alice = discovery_test_users["alice"]["token"]
    alice_id = str(discovery_test_users["alice"]["persona"].id)
    bob_id = str(discovery_test_users["bob"]["persona"].id)

    # Self connection attempt
    self_res = await async_client.post(
        "/api/v1/connections/request",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"recipient_persona_id": alice_id},
    )
    assert self_res.status_code == 400
    assert "yourself" in self_res.json()["detail"].lower()

    # Send request to Bob
    req1 = await async_client.post(
        "/api/v1/connections/request",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"recipient_persona_id": bob_id},
    )
    assert req1.status_code == 201

    # Send duplicate request to Bob
    req2 = await async_client.post(
        "/api/v1/connections/request",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"recipient_persona_id": bob_id},
    )
    assert req2.status_code == 400
    assert "already" in req2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_bilateral_block_isolation_on_discovery_and_connections(
    async_client: AsyncClient,
    discovery_test_users: dict,
    db_session: AsyncSession,
):
    """
    Verify complete bilateral block isolation:
    - Blocked users never appear in discovery cards for either blocker or blockee.
    - Blocked users cannot send connection requests to each other in either direction.
    """
    token_alice = discovery_test_users["alice"]["token"]
    token_bob = discovery_test_users["bob"]["token"]
    alice_id = discovery_test_users["alice"]["persona"].id
    bob_id = discovery_test_users["bob"]["persona"].id

    # Alice blocks Bob
    block = Block(
        blocker_persona_id=alice_id,
        blocked_persona_id=bob_id,
        reason="Disliked conversation",
    )
    db_session.add(block)
    await db_session.commit()

    # Alice queries discovery feed -> Bob does NOT appear
    res_alice = await async_client.get(
        "/api/v1/discovery/feed",
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert res_alice.status_code == 200
    alice_feed_ids = [c["persona"]["id"] for c in res_alice.json()["items"]]
    assert str(bob_id) not in alice_feed_ids

    # Bob queries discovery feed -> Alice does NOT appear
    res_bob = await async_client.get(
        "/api/v1/discovery/feed",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert res_bob.status_code == 200
    bob_feed_ids = [c["persona"]["id"] for c in res_bob.json()["items"]]
    assert str(alice_id) not in bob_feed_ids

    # Bob tries to send connection request to Alice -> 403 Forbidden
    conn_bob_to_alice = await async_client.post(
        "/api/v1/connections/request",
        headers={"Authorization": f"Bearer {token_bob}"},
        json={"recipient_persona_id": str(alice_id)},
    )
    assert conn_bob_to_alice.status_code == 403

    # Alice tries to send connection request to Bob -> 403 Forbidden
    conn_alice_to_bob = await async_client.post(
        "/api/v1/connections/request",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"recipient_persona_id": str(bob_id)},
    )
    assert conn_alice_to_bob.status_code == 403
