import asyncio
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.app.core.config import settings
from backend.app.models.account import Account, AccountStatus
from backend.app.models.invitation import Invitation, InvitationStatus


@pytest.mark.asyncio
async def test_postgres_concurrent_invitation_redemption_race():
    """
    Simulate 5 concurrent tasks attempting to redeem the exact same invitation
    simultaneously against PostgreSQL. Exactly ONE must succeed and the other
    4 must be rejected atomically.
    """
    # Connect directly to live PostgreSQL container
    pg_url = "postgresql+asyncpg://aftr_user:aftr_password@localhost:5432/aftr_db"
    pg_engine = create_async_engine(pg_url)
    PGSessionLocal = async_sessionmaker(bind=pg_engine, class_=AsyncSession, expire_on_commit=False)

    token_hash = f"race-test-token-{uuid.uuid4().hex}"
    recipient_hash = f"race-test-recip-{uuid.uuid4().hex}"

    async with PGSessionLocal() as session:
        # Create inviter account
        inviter = Account(
            supabase_user_id=uuid.uuid4(),
            email_hash=f"hash-inviter-{uuid.uuid4().hex[:12]}",
            is_age_verified=True,
            invite_quota=3,
        )
        session.add(inviter)
        await session.flush()

        # Create 5 distinct invitee accounts
        invitees = [
            Account(
                supabase_user_id=uuid.uuid4(),
                email_hash=f"hash-invitee-{i}-{uuid.uuid4().hex[:12]}",
                is_age_verified=True,
            )
            for i in range(5)
        ]
        session.add_all(invitees)
        await session.flush()

        # Create pending invitation
        inv = Invitation(
            inviter_account_id=inviter.id,
            token_hash=token_hash,
            recipient_hash=recipient_hash,
            status=InvitationStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
        )
        session.add(inv)
        await session.commit()
        invitee_ids = [invitee.id for invitee in invitees]

    # Concurrent redemption function
    async def attempt_redemption(user_id: uuid.UUID):
        async with PGSessionLocal() as s:
            query = text(
                """
                SELECT success, invitation_id, error_code
                FROM aftr_redeem_invitation_atomic(:token_hash, :recipient_hash, :used_by_id)
                """
            )
            res = await s.execute(
                query,
                {
                    "token_hash": token_hash,
                    "recipient_hash": recipient_hash,
                    "used_by_id": user_id,
                },
            )
            row = res.one()
            await s.commit()
            return row

    # Launch 5 simultaneous redemption tasks
    results = await asyncio.gather(*[attempt_redemption(uid) for uid in invitee_ids])

    successes = [r for r in results if r[0] is True]
    failures = [r for r in results if r[0] is False]

    # Crucial assertion: Exactly 1 success, 4 failures
    assert len(successes) == 1, f"Expected 1 winner, got {len(successes)}"
    assert len(failures) == 4, f"Expected 4 rejected, got {len(failures)}"

    # Winner has error_code 'SUCCESS'
    assert successes[0][2] == "SUCCESS"

    # Losers have error_code 'INVITATION_ALREADY_USED'
    for f in failures:
        assert f[2] == "INVITATION_ALREADY_USED"

    # Verify database state in PostgreSQL
    async with PGSessionLocal() as session:
        inv_record = (
            await session.execute(select(Invitation).where(Invitation.token_hash == token_hash))
        ).scalar_one()
        assert inv_record.status == InvitationStatus.USED
        assert inv_record.used_by_account_id is not None
        assert inv_record.used_at is not None

    await pg_engine.dispose()
