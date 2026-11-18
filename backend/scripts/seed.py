"""Development Seed Script for AFTR Platform

Populates development database with test accounts, personas, invitations,
interests, posts, and consent-gated connections.
"""
import asyncio
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import AsyncSessionLocal, engine
from backend.app.models.account import Account, AccountStatus
from backend.app.models.persona import Persona, CampusAffiliation, Interest, PersonaInterest
from backend.app.models.invitation import Invitation, InvitationStatus
from backend.app.models.social import Post, PostType, Comment, Reaction, Story
from backend.app.models.connection import (
    ConnectionRequest,
    ConnectionRequestStatus,
    Conversation,
    ConversationParticipant,
    Message,
)
from backend.app.models.event import Event, EventAttendee, AttendeeStatus
from backend.app.models.moderation import AuditLog


def hash_identifier(identifier: str) -> str:
    """HMAC-SHA256 hash of an identifier (email, phone) using SECRET_KEY."""
    return hmac.new(
        settings.SECRET_KEY.encode(),
        identifier.lower().strip().encode(),
        hashlib.sha256,
    ).hexdigest()


def hash_token(token: str) -> str:
    """SHA-256 hash of random invite token."""
    return hashlib.sha256(token.encode()).hexdigest()


async def seed_data():
    async with AsyncSessionLocal() as session:
        print("🌱 Seeding AFTR Development Database...")

        # 1. Seed Interests
        interest_defs = [
            ("Late Night Talks", "late-night-talks", True),
            ("Campus Romance", "campus-romance", True),
            ("Unfiltered Confessions", "unfiltered-confessions", True),
            ("Mental Health & Stress", "mental-health-stress", True),
            ("Secret Crushes", "secret-crushes", True),
            ("Underground Events", "underground-events", True),
        ]

        existing_interests = await session.execute(select(Interest))
        if not existing_interests.scalars().first():
            interests = [
                Interest(name=name, slug=slug, is_adult=is_adult)
                for name, slug, is_adult in interest_defs
            ]
            session.add_all(interests)
            await session.flush()
            print(f"  ✓ Seeded {len(interests)} interests")
        else:
            interests = (await session.execute(select(Interest))).scalars().all()

        # 2. Seed Accounts
        alice_auth_id = uuid.uuid5(uuid.NAMESPACE_DNS, "alice@example.com")
        bob_auth_id = uuid.uuid5(uuid.NAMESPACE_DNS, "bob@example.com")
        charlie_auth_id = uuid.uuid5(uuid.NAMESPACE_DNS, "charlie@example.com")

        existing_account = await session.execute(
            select(Account).where(Account.supabase_user_id == alice_auth_id)
        )
        if not existing_account.scalars().first():
            account_alice = Account(
                supabase_user_id=alice_auth_id,
                email_hash=hash_identifier("alice@example.com"),
                is_age_verified=True,
                birth_year=2003,
                invite_quota=3,
                status=AccountStatus.ACTIVE,
            )
            account_bob = Account(
                supabase_user_id=bob_auth_id,
                email_hash=hash_identifier("bob@example.com"),
                is_age_verified=True,
                birth_year=2002,
                invite_quota=2,
                status=AccountStatus.ACTIVE,
            )
            account_charlie = Account(
                supabase_user_id=charlie_auth_id,
                email_hash=hash_identifier("charlie@example.com"),
                is_age_verified=True,
                birth_year=2001,
                invite_quota=1,
                status=AccountStatus.ACTIVE,
            )
            session.add_all([account_alice, account_bob, account_charlie])
            await session.flush()
            print("  ✓ Seeded 3 development accounts (Alice, Bob, Charlie)")

            # 3. Seed Anonymous Personas (Strictly decoupled from real identities)
            persona_alice = Persona(
                account_id=account_alice.id,
                display_name="ShadowFox",
                avatar_seed="shadow-fox-midnight-avatar",
                bio="Late night coder. Anonymous student exploring campus thoughts.",
                is_active=True,
            )
            persona_bob = Persona(
                account_id=account_bob.id,
                display_name="NeonGhost",
                avatar_seed="neon-ghost-emerald-avatar",
                bio="Philosophy & coffee addict. Looking for honest connections.",
                is_active=True,
            )
            persona_charlie = Persona(
                account_id=account_charlie.id,
                display_name="MidnightEcho",
                avatar_seed="midnight-echo-violet-avatar",
                bio="Art student by day, anonymous music creator by night.",
                is_active=True,
            )
            session.add_all([persona_alice, persona_bob, persona_charlie])
            await session.flush()
            print("  ✓ Seeded 3 anonymous personas (ShadowFox, NeonGhost, MidnightEcho)")

            # 4. Optional Campus Affiliations (Self-Declared)
            affiliations = [
                CampusAffiliation(
                    persona_id=persona_alice.id,
                    campus_name="Bay Area University",
                    campus_code="BAU",
                    is_primary=True,
                ),
                CampusAffiliation(
                    persona_id=persona_bob.id,
                    campus_name="West Coast College",
                    campus_code="WCC",
                    is_primary=True,
                ),
                CampusAffiliation(
                    persona_id=persona_charlie.id,
                    campus_name="Bay Area University",
                    campus_code="BAU",
                    is_primary=True,
                ),
            ]
            session.add_all(affiliations)

            # 5. Seed Persona Interests
            if interests:
                pi = [
                    PersonaInterest(persona_id=persona_alice.id, interest_id=interests[0].id),
                    PersonaInterest(persona_id=persona_alice.id, interest_id=interests[2].id),
                    PersonaInterest(persona_id=persona_bob.id, interest_id=interests[0].id),
                    PersonaInterest(persona_id=persona_bob.id, interest_id=interests[1].id),
                    PersonaInterest(persona_id=persona_charlie.id, interest_id=interests[2].id),
                    PersonaInterest(persona_id=persona_charlie.id, interest_id=interests[5].id),
                ]
                session.add_all(pi)

            # 6. Seed Invitations
            now = datetime.now(timezone.utc)
            invites = [
                # Pending, valid invitation created by Alice for Dave
                Invitation(
                    inviter_account_id=account_alice.id,
                    token_hash=hash_token("dev-invite-token-alice-to-dave-123456"),
                    recipient_hash=hash_identifier("dave@example.com"),
                    status=InvitationStatus.PENDING,
                    expires_at=now + timedelta(hours=72),
                ),
                # Expired invitation (created 73 hours ago, expired 1 hour ago)
                Invitation(
                    inviter_account_id=account_bob.id,
                    token_hash=hash_token("dev-invite-token-bob-expired-old-1234"),
                    recipient_hash=hash_identifier("eve@example.com"),
                    status=InvitationStatus.EXPIRED,
                    created_at=now - timedelta(hours=73),
                    expires_at=now - timedelta(hours=1),
                ),
                # Used invitation by Charlie (issued by Alice 24h ago, used 2h ago)
                Invitation(
                    inviter_account_id=account_alice.id,
                    token_hash=hash_token("dev-invite-token-alice-to-charlie-claimed"),
                    recipient_hash=hash_identifier("charlie@example.com"),
                    status=InvitationStatus.USED,
                    created_at=now - timedelta(hours=24),
                    expires_at=now + timedelta(hours=48),
                    used_by_account_id=account_charlie.id,
                    used_at=now - timedelta(hours=2),
                ),
            ]
            session.add_all(invites)

            # 7. Seed Posts (Confessions)
            confession1 = Post(
                persona_id=persona_alice.id,
                content="I've been in love with someone in my chemistry study group for two terms. Every time they ask to review notes, my heart races. They have no idea.",
                post_type=PostType.CONFESSION,
                tag="secret-crushes",
                is_sensitive=False,
                view_count=42,
            )
            confession2 = Post(
                persona_id=persona_bob.id,
                content="Walking through the campus quad at 2:30 AM in the fog is the only time I feel completely free from academic burnout.",
                post_type=PostType.CONFESSION,
                tag="mental-health-stress",
                is_sensitive=False,
                view_count=87,
            )
            session.add_all([confession1, confession2])
            await session.flush()

            # Comment on confession
            comment1 = Comment(
                post_id=confession2.id,
                persona_id=persona_charlie.id,
                content="I know exactly what you mean. The quiet on the east courtyard around that time is surreal.",
            )
            session.add_all([comment1])

            # 8. Seed Connection Request & Consent-Based Conversation
            # Connection from Alice (ShadowFox) to Bob (NeonGhost) -> ACCEPTED
            conn_req = ConnectionRequest(
                sender_persona_id=persona_alice.id,
                recipient_persona_id=persona_bob.id,
                status=ConnectionRequestStatus.ACCEPTED,
            )
            session.add(conn_req)
            await session.flush()

            # Conversation unlocked strictly by consent
            conv = Conversation(
                connection_request_id=conn_req.id,
                is_active=True,
            )
            session.add(conv)
            await session.flush()

            part_a = ConversationParticipant(conversation_id=conv.id, persona_id=persona_alice.id)
            part_b = ConversationParticipant(conversation_id=conv.id, persona_id=persona_bob.id)
            session.add_all([part_a, part_b])

            msg1 = Message(
                conversation_id=conv.id,
                sender_persona_id=persona_alice.id,
                content="Hey! Loved your post about late night campus walks.",
            )
            msg2 = Message(
                conversation_id=conv.id,
                sender_persona_id=persona_bob.id,
                content="Thanks! Glad someone relates. Do you usually study late in the science library?",
            )
            session.add_all([msg1, msg2])

            # 9. Seed Public Group Event
            event1 = Event(
                creator_persona_id=persona_charlie.id,
                title="Midnight Rooftop Astronomy & Lo-Fi Session",
                description="Bring a blanket and headphones. Observing the meteor shower from the physics tower terrace.",
                campus_name="Bay Area University",
                location_name="Physics Observatory Terrace (Open Access)",
                event_time=now + timedelta(days=2, hours=4),
                max_attendees=25,
            )
            session.add(event1)
            await session.flush()

            attendee1 = EventAttendee(
                event_id=event1.id,
                persona_id=persona_alice.id,
                status=AttendeeStatus.GOING,
            )
            session.add(attendee1)

            # 10. Audit Log
            audit = AuditLog(
                actor_id=account_alice.id,
                actor_type="ACCOUNT",
                action="DEV_SEED_INITIALIZED",
                ip_hash=hash_identifier("127.0.0.1"),
                details_json='{"note": "Development initial seed created"}',
            )
            session.add(audit)

            await session.commit()
            print("  ✓ Seeded connections, consent conversation, messages, and events")
            print("🎉 Development database successfully seeded!")
        else:
            print("  ℹ️ Development seed data already present. Skipping.")


if __name__ == "__main__":
    asyncio.run(seed_data())
