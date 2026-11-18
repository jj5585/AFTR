import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.security import create_test_jwt
from backend.app.models.base import ensure_utc
from backend.app.models.account import Account, AccountStatus
from backend.app.models.persona import Persona, CampusAffiliation
from backend.app.models.social import Story, StoryComment, Reaction
from backend.app.models.event import Event, EventAttendee, AttendeeStatus
from backend.app.models.moderation import Block


@pytest.fixture
async def stories_events_test_users(db_session: AsyncSession):
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
        email_hash="hash_alice_se@example.com",
        is_age_verified=True,
        birth_year=2001,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
    )
    acc_bob = Account(
        supabase_user_id=bob_sub,
        email_hash="hash_bob_se@example.com",
        is_age_verified=True,
        birth_year=2000,
        invite_quota=3,
        status=AccountStatus.ACTIVE,
    )
    acc_charlie = Account(
        supabase_user_id=charlie_sub,
        email_hash="hash_charlie_se@example.com",
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

    token_alice = create_test_jwt(alice_sub, "alice@example.com")
    token_bob = create_test_jwt(bob_sub, "bob@example.com")
    token_charlie = create_test_jwt(charlie_sub, "charlie@example.com")

    return {
        "alice": {"account": acc_alice, "persona": p_alice, "token": token_alice},
        "bob": {"account": acc_bob, "persona": p_bob, "token": token_bob},
        "charlie": {"account": acc_charlie, "persona": p_charlie, "token": token_charlie},
    }


# ==========================================
# Story Tests
# ==========================================

@pytest.mark.asyncio
async def test_create_and_fetch_stories(
    async_client: AsyncClient,
    stories_events_test_users: dict,
):
    """
    Verify:
    1. Alice publishes a 24-hour anonymous story.
    2. Expiration is set to 24 hours in the future.
    3. Stories feed returns story with zero real identity leakage.
    """
    token_alice = stories_events_test_users["alice"]["token"]
    headers = {"Authorization": f"Bearer {token_alice}"}

    create_res = await async_client.post(
        "/api/v1/stories",
        headers=headers,
        json={
            "content": "Looking at the foggy bay at 2am with lo-fi beats playing.",
            "category": "night-thoughts",
            "allow_comments": True,
            "visibility": "PUBLIC",
        },
    )
    assert create_res.status_code == 201
    story = create_res.json()
    assert story["category"] == "night-thoughts"
    assert story["allow_comments"] is True
    assert story["is_own"] is True

    # Check 24-hour expiration
    exp = ensure_utc(datetime.fromisoformat(story["expires_at"].replace("Z", "+00:00")))
    now = datetime.now(timezone.utc)
    diff = exp - now
    assert 23.5 <= diff.total_seconds() / 3600 <= 24.5

    # Bob views stories feed
    token_bob = stories_events_test_users["bob"]["token"]
    feed_res = await async_client.get(
        "/api/v1/stories",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert feed_res.status_code == 200
    feed = feed_res.json()
    assert len(feed["items"]) >= 1

    s0 = next(s for s in feed["items"] if s["id"] == story["id"])
    assert s0["content"] == "Looking at the foggy bay at 2am with lo-fi beats playing."
    assert s0["is_own"] is False
    assert "email" not in s0["persona"]
    assert "email_hash" not in s0["persona"]


@pytest.mark.asyncio
async def test_story_comments_and_disable_comments(
    async_client: AsyncClient,
    stories_events_test_users: dict,
):
    """
    Verify:
    1. Bob comments on Alice's story with comments allowed.
    2. Alice publishes a story with allow_comments=False.
    3. Bob attempting to comment is rejected with 403 Forbidden.
    """
    token_alice = stories_events_test_users["alice"]["token"]
    token_bob = stories_events_test_users["bob"]["token"]

    # Alice publishes open story
    s1_res = await async_client.post(
        "/api/v1/stories",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"content": "Open for reflections tonight.", "allow_comments": True},
    )
    s1_id = s1_res.json()["id"]

    # Bob comments
    comm_res = await async_client.post(
        f"/api/v1/stories/{s1_id}/comments",
        headers={"Authorization": f"Bearer {token_bob}"},
        json={"content": "Same vibe here in the library."},
    )
    assert comm_res.status_code == 201
    assert comm_res.json()["content"] == "Same vibe here in the library."

    # Alice publishes closed story
    s2_res = await async_client.post(
        "/api/v1/stories",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"content": "Private midnight reflection only.", "allow_comments": False},
    )
    s2_id = s2_res.json()["id"]

    # Bob attempts to comment -> 403 Forbidden
    comm_fail = await async_client.post(
        f"/api/v1/stories/{s2_id}/comments",
        headers={"Authorization": f"Bearer {token_bob}"},
        json={"content": "Can I comment?"},
    )
    assert comm_fail.status_code == 403
    assert "disabled" in comm_fail.json()["detail"].lower()


@pytest.mark.asyncio
async def test_story_reactions_toggle(
    async_client: AsyncClient,
    stories_events_test_users: dict,
):
    """Verify toggling anonymous reactions on stories."""
    token_alice = stories_events_test_users["alice"]["token"]
    token_bob = stories_events_test_users["bob"]["token"]

    s_res = await async_client.post(
        "/api/v1/stories",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"content": "Late coffee run anyone?"},
    )
    s_id = s_res.json()["id"]

    # Bob reacts -> ADDED
    r1 = await async_client.post(
        f"/api/v1/stories/{s_id}/reactions?reaction_type=UPVOTE",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert r1.status_code == 200
    assert r1.json()["action"] == "ADDED"
    assert r1.json()["reactions_count"] == 1

    # Bob reacts again -> REMOVED (toggle off)
    r2 = await async_client.post(
        f"/api/v1/stories/{s_id}/reactions?reaction_type=UPVOTE",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert r2.status_code == 200
    assert r2.json()["action"] == "REMOVED"
    assert r2.json()["reactions_count"] == 0


@pytest.mark.asyncio
async def test_story_moderation_and_author_deletion(
    async_client: AsyncClient,
    stories_events_test_users: dict,
):
    """
    Verify:
    1. PII or phone numbers in stories trigger Privacy Shield flag.
    2. Non-authors cannot delete story (403 Forbidden).
    3. Author can delete story.
    """
    token_alice = stories_events_test_users["alice"]["token"]
    token_bob = stories_events_test_users["bob"]["token"]

    # Moderation rejection: phone number
    mod_fail = await async_client.post(
        "/api/v1/stories",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"content": "Call my phone at 415-555-2671 right now!"},
    )
    assert mod_fail.status_code == 400
    assert "Privacy Shield" in mod_fail.json()["detail"]

    # Alice publishes valid story
    s_res = await async_client.post(
        "/api/v1/stories",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"content": "A story to be deleted soon."},
    )
    s_id = s_res.json()["id"]

    # Bob attempts to delete -> 403 Forbidden
    del_bob = await async_client.delete(
        f"/api/v1/stories/{s_id}",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert del_bob.status_code == 403

    # Alice deletes own story -> 200 OK
    del_alice = await async_client.delete(
        f"/api/v1/stories/{s_id}",
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert del_alice.status_code == 200
    assert del_alice.json()["status"] == "DELETED"


# ==========================================
# Event Tests & Safety Rules
# ==========================================

@pytest.mark.asyncio
async def test_create_event_safety_and_public_venue_enforcement(
    async_client: AsyncClient,
    stories_events_test_users: dict,
):
    """
    SAFETY RULES:
    1. No live location sharing / GPS coordinates prohibited.
    2. No private home addresses or dorm rooms.
    3. Public venue requirement (e.g. Campus Student Union, Tavern, Quad).
    4. Future date required.
    """
    token_alice = stories_events_test_users["alice"]["token"]
    headers = {"Authorization": f"Bearer {token_alice}"}
    future_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    # Valid public venue -> 201 Created
    valid_res = await async_client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "Midnight Architecture Sketching",
            "description": "Meetup for adult students interested in urban design and coffee.",
            "location_name": "Campus Student Union Cafe, North Terrace",
            "event_time": future_time,
            "max_attendees": 15,
        },
    )
    assert valid_res.status_code == 201
    data = valid_res.json()
    assert data["title"] == "Midnight Architecture Sketching"
    assert data["attendees_count"] == 1  # Organizer auto-going
    assert data["is_organizer"] is True

    # Safety violation 1: GPS coordinates -> 400 Bad Request
    gps_res = await async_client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "Secret Gathering",
            "description": "Meet at exact coordinates.",
            "location_name": "37.7749, -122.4194",
            "event_time": future_time,
        },
    )
    assert gps_res.status_code == 400
    assert "GPS coordinates are prohibited" in gps_res.json()["detail"]

    # Safety violation 2: Private residence / dorm room -> 400 Bad Request
    home_res = await async_client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "House Party",
            "description": "Come over to my dorm room.",
            "location_name": "My apartment #4B, Elm St",
            "event_time": future_time,
        },
    )
    assert home_res.status_code == 400
    assert "public venue" in home_res.json()["detail"].lower()

    # Safety violation 3: Past time -> 400 Bad Request
    past_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    past_res = await async_client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "Past Meetup",
            "description": "Already happened.",
            "location_name": "Library Plaza",
            "event_time": past_time,
        },
    )
    assert past_res.status_code == 400
    assert "future" in past_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_event_capacity_and_rsvp_lifecycle(
    async_client: AsyncClient,
    stories_events_test_users: dict,
):
    """
    Verify:
    1. Event with max_attendees = 2 (Alice organizer is #1).
    2. Bob RSVPs GOING -> attendees_count = 2 (Capacity full).
    3. Charlie attempts GOING -> 400 Bad Request (Capacity reached).
    4. Charlie RSVPs INTERESTED -> 200 OK.
    5. Bob withdraws RSVP -> attendees_count = 1.
    6. Charlie can now RSVP GOING -> 200 OK.
    """
    token_alice = stories_events_test_users["alice"]["token"]
    token_bob = stories_events_test_users["bob"]["token"]
    token_charlie = stories_events_test_users["charlie"]["token"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    # Alice creates event with capacity 2
    ev_res = await async_client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={
            "title": "Acoustic Jam Session",
            "description": "Intimate acoustic guitar session at the amphitheater.",
            "location_name": "Campus Central Amphitheater",
            "event_time": future_time,
            "max_attendees": 2,
        },
    )
    assert ev_res.status_code == 201
    ev_id = ev_res.json()["id"]

    # Bob RSVPs GOING
    bob_rsvp = await async_client.post(
        f"/api/v1/events/{ev_id}/rsvp",
        headers={"Authorization": f"Bearer {token_bob}"},
        json={"status": "GOING"},
    )
    assert bob_rsvp.status_code == 200
    assert bob_rsvp.json()["attendees_count"] == 2
    assert bob_rsvp.json()["user_rsvp_status"] == "GOING"

    # Charlie attempts GOING -> 400 Bad Request (Full)
    charlie_fail = await async_client.post(
        f"/api/v1/events/{ev_id}/rsvp",
        headers={"Authorization": f"Bearer {token_charlie}"},
        json={"status": "GOING"},
    )
    assert charlie_fail.status_code == 400
    assert "maximum attendance capacity" in charlie_fail.json()["detail"].lower()

    # Charlie RSVPs INTERESTED -> OK
    charlie_int = await async_client.post(
        f"/api/v1/events/{ev_id}/rsvp",
        headers={"Authorization": f"Bearer {token_charlie}"},
        json={"status": "INTERESTED"},
    )
    assert charlie_int.status_code == 200
    assert charlie_int.json()["interested_count"] == 1
    assert charlie_int.json()["user_rsvp_status"] == "INTERESTED"

    # Bob withdraws RSVP
    bob_with = await async_client.delete(
        f"/api/v1/events/{ev_id}/rsvp",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert bob_with.status_code == 200
    assert bob_with.json()["attendees_count"] == 1
    assert bob_with.json()["user_rsvp_status"] is None

    # Charlie can now RSVP GOING
    charlie_going = await async_client.post(
        f"/api/v1/events/{ev_id}/rsvp",
        headers={"Authorization": f"Bearer {token_charlie}"},
        json={"status": "GOING"},
    )
    assert charlie_going.status_code == 200
    assert charlie_going.json()["attendees_count"] == 2
    assert charlie_going.json()["user_rsvp_status"] == "GOING"


@pytest.mark.asyncio
async def test_event_organizer_controls_and_cancellation(
    async_client: AsyncClient,
    stories_events_test_users: dict,
):
    """
    Verify:
    1. Non-organizers cannot cancel or update event (403 Forbidden).
    2. Organizer can cancel event.
    3. RSVPing to cancelled event is rejected with 400 Bad Request.
    """
    token_alice = stories_events_test_users["alice"]["token"]
    token_bob = stories_events_test_users["bob"]["token"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()

    ev_res = await async_client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={
            "title": "Weekend Poetry Reading",
            "description": "Reading contemporary poetry in the evening.",
            "location_name": "The Daily Grind Books & Cafe",
            "event_time": future_time,
        },
    )
    ev_id = ev_res.json()["id"]

    # Bob attempts to cancel -> 403 Forbidden
    cancel_bob = await async_client.post(
        f"/api/v1/events/{ev_id}/cancel",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert cancel_bob.status_code == 403

    # Alice cancels event -> 200 OK
    cancel_alice = await async_client.post(
        f"/api/v1/events/{ev_id}/cancel",
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert cancel_alice.status_code == 200
    assert cancel_alice.json()["is_cancelled"] is True

    # Bob tries to RSVP to cancelled event -> 400 Bad Request
    rsvp_fail = await async_client.post(
        f"/api/v1/events/{ev_id}/rsvp",
        headers={"Authorization": f"Bearer {token_bob}"},
        json={"status": "GOING"},
    )
    assert rsvp_fail.status_code == 400
    assert "cancelled" in rsvp_fail.json()["detail"].lower()


@pytest.mark.asyncio
async def test_stories_and_events_bilateral_block_isolation(
    async_client: AsyncClient,
    stories_events_test_users: dict,
    db_session: AsyncSession,
):
    """
    Verify bilateral block isolation across stories and events:
    - Blocked users' stories do not appear in feed.
    - Blocked users' events do not appear in event list.
    - Blocked users cannot RSVP to blocker's events.
    """
    token_alice = stories_events_test_users["alice"]["token"]
    token_bob = stories_events_test_users["bob"]["token"]
    alice_id = stories_events_test_users["alice"]["persona"].id
    bob_id = stories_events_test_users["bob"]["persona"].id

    # Alice publishes story and creates event
    s_res = await async_client.post(
        "/api/v1/stories",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"content": "Alice's secret thoughts..."},
    )
    s_id = s_res.json()["id"]

    future_time = (datetime.now(timezone.utc) + timedelta(days=4)).isoformat()
    ev_res = await async_client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={
            "title": "Private Philosophy Salon",
            "description": "Discussions on existentialism.",
            "location_name": "Faculty Club Lounge",
            "event_time": future_time,
        },
    )
    ev_id = ev_res.json()["id"]

    # Alice blocks Bob
    block = Block(
        blocker_persona_id=alice_id,
        blocked_persona_id=bob_id,
        reason="Harassment",
    )
    db_session.add(block)
    await db_session.commit()

    # Bob queries stories feed -> Alice's story omitted
    bob_stories = await async_client.get(
        "/api/v1/stories",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert bob_stories.status_code == 200
    story_ids = [s["id"] for s in bob_stories.json()["items"]]
    assert s_id not in story_ids

    # Bob queries events list -> Alice's event omitted
    bob_events = await async_client.get(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert bob_events.status_code == 200
    event_ids = [e["id"] for e in bob_events.json()["items"]]
    assert ev_id not in event_ids

    # Bob tries to RSVP to Alice's event -> 403 Forbidden
    rsvp_blocked = await async_client.post(
        f"/api/v1/events/{ev_id}/rsvp",
        headers={"Authorization": f"Bearer {token_bob}"},
        json={"status": "GOING"},
    )
    assert rsvp_blocked.status_code == 403
