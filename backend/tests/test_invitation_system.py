import asyncio
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.account import Account, AccountStatus
from backend.app.models.invitation import Invitation, InvitationStatus


@pytest.mark.asyncio
async def test_invitation_token_uniqueness(db_session: AsyncSession):
    """Tokens must be unique; duplicate token hashes must be rejected."""
    acc1 = Account(supabase_user_id=uuid.uuid4(), email_hash="hash-tok-1", is_age_verified=True)
    acc2 = Account(supabase_user_id=uuid.uuid4(), email_hash="hash-tok-2", is_age_verified=True)
    db_session.add_all([acc1, acc2])
    await db_session.flush()

    shared_token_hash = "shared-unique-token-hash-12345"
    now = datetime.now(timezone.utc)

    inv1 = Invitation(
        inviter_account_id=acc1.id,
        token_hash=shared_token_hash,
        recipient_hash="recipient-1-hash",
        status=InvitationStatus.PENDING,
        expires_at=now + timedelta(hours=72),
    )
    db_session.add(inv1)
    await db_session.flush()

    # Attempt duplicate token hash
    inv2 = Invitation(
        inviter_account_id=acc2.id,
        token_hash=shared_token_hash,
        recipient_hash="recipient-2-hash",
        status=InvitationStatus.PENDING,
        expires_at=now + timedelta(hours=72),
    )
    db_session.add(inv2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_invitation_expiry_check_constraint(db_session: AsyncSession):
    """
    Check constraint chk_invitation_expiry_future enforces expires_at > created_at.
    """
    acc = Account(supabase_user_id=uuid.uuid4(), email_hash="hash-exp-test", is_age_verified=True)
    db_session.add(acc)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    # Invalid: expires_at is set in the past relative to created_at
    invalid_inv = Invitation(
        inviter_account_id=acc.id,
        token_hash="token-hash-invalid-past-expiry",
        recipient_hash="recipient-hash-exp",
        status=InvitationStatus.PENDING,
        created_at=now,
        expires_at=now - timedelta(seconds=10),
    )
    db_session.add(invalid_inv)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_invitation_expiry_detection(db_session: AsyncSession):
    """Expired invitations cannot be used."""
    acc = Account(supabase_user_id=uuid.uuid4(), email_hash="hash-exp-detect", is_age_verified=True)
    db_session.add(acc)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    expired_inv = Invitation(
        inviter_account_id=acc.id,
        token_hash="token-hash-expired-detect",
        recipient_hash="recipient-hash-detect",
        status=InvitationStatus.EXPIRED,
        created_at=now - timedelta(hours=75),
        expires_at=now - timedelta(hours=3),
    )
    db_session.add(expired_inv)
    await db_session.flush()

    # Attempting to verify or redeem
    res = await db_session.execute(
        select(Invitation).where(Invitation.token_hash == "token-hash-expired-detect")
    )
    fetched = res.scalar_one()
    is_valid = fetched.status == InvitationStatus.PENDING and fetched.expires_at > datetime.now(timezone.utc)
    assert is_valid is False
    assert fetched.status == InvitationStatus.EXPIRED
    await db_session.rollback()


@pytest.mark.asyncio
async def test_invitation_single_use_atomic_transition(db_session: AsyncSession):
    """
    Atomic conditional update ensures an invitation transitions from PENDING to USED exactly once.
    """
    inviter = Account(supabase_user_id=uuid.uuid4(), email_hash="hash-inviter-race", is_age_verified=True)
    redeemer1 = Account(supabase_user_id=uuid.uuid4(), email_hash="hash-redeemer-1", is_age_verified=True)
    redeemer2 = Account(supabase_user_id=uuid.uuid4(), email_hash="hash-redeemer-2", is_age_verified=True)
    db_session.add_all([inviter, redeemer1, redeemer2])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    inv = Invitation(
        inviter_account_id=inviter.id,
        token_hash="token-hash-single-use-test",
        recipient_hash="recipient-hash-race",
        status=InvitationStatus.PENDING,
        expires_at=now + timedelta(hours=72),
    )
    db_session.add(inv)
    await db_session.flush()

    # 1. First redemption attempt: Should succeed
    res1 = await db_session.execute(
        update(Invitation)
        .where(
            Invitation.id == inv.id,
            Invitation.status == InvitationStatus.PENDING,
            Invitation.expires_at > datetime.now(timezone.utc),
        )
        .values(
            status=InvitationStatus.USED,
            used_by_account_id=redeemer1.id,
            used_at=datetime.now(timezone.utc),
        )
    )
    assert res1.rowcount == 1  # 1 row updated

    # 2. Concurrent/Second redemption attempt on the same token: Must affect 0 rows
    res2 = await db_session.execute(
        update(Invitation)
        .where(
            Invitation.id == inv.id,
            Invitation.status == InvitationStatus.PENDING,
            Invitation.expires_at > datetime.now(timezone.utc),
        )
        .values(
            status=InvitationStatus.USED,
            used_by_account_id=redeemer2.id,
            used_at=datetime.now(timezone.utc),
        )
    )
    assert res2.rowcount == 0  # Replay/race successfully defeated

    # Verify final state
    updated_inv = (await db_session.execute(select(Invitation).where(Invitation.id == inv.id))).scalar_one()
    assert updated_inv.status == InvitationStatus.USED
    assert updated_inv.used_by_account_id == redeemer1.id
    await db_session.rollback()


@pytest.mark.asyncio
async def test_invitation_used_integrity_constraint(db_session: AsyncSession):
    """
    State machine integrity constraint: status='USED' requires used_by_account_id and used_at.
    """
    acc = Account(supabase_user_id=uuid.uuid4(), email_hash="hash-used-integ", is_age_verified=True)
    db_session.add(acc)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    # Attempt to insert status=USED without used_by_account_id
    invalid_used = Invitation(
        inviter_account_id=acc.id,
        token_hash="token-hash-invalid-used-without-user",
        recipient_hash="recip-hash",
        status=InvitationStatus.USED,
        expires_at=now + timedelta(hours=72),
        used_by_account_id=None,
        used_at=None,
    )
    db_session.add(invalid_used)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_invitation_revocation(db_session: AsyncSession):
    """Invitations can be revoked before redemption."""
    acc = Account(supabase_user_id=uuid.uuid4(), email_hash="hash-revoke-test", is_age_verified=True)
    db_session.add(acc)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    inv = Invitation(
        inviter_account_id=acc.id,
        token_hash="token-hash-to-be-revoked",
        recipient_hash="recip-hash-rev",
        status=InvitationStatus.PENDING,
        expires_at=now + timedelta(hours=72),
    )
    db_session.add(inv)
    await db_session.flush()

    # Revoke invitation
    inv.status = InvitationStatus.REVOKED
    inv.revoked_at = datetime.now(timezone.utc)
    await db_session.flush()

    # Confirm revocation
    fetched = (await db_session.execute(select(Invitation).where(Invitation.id == inv.id))).scalar_one()
    assert fetched.status == InvitationStatus.REVOKED
    assert fetched.revoked_at is not None
    await db_session.rollback()
