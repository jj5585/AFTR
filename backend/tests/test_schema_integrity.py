import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.account import Account, AccountStatus
from backend.app.models.persona import Persona, CampusAffiliation
from backend.app.models.social import Post, PostType
from backend.app.models.connection import (
    ConnectionRequest,
    ConnectionRequestStatus,
    Conversation,
    ConversationParticipant,
    Message,
)
from backend.app.models.moderation import Block


@pytest.mark.asyncio
async def test_foreign_key_constraint_invalid_account(db_session: AsyncSession):
    """Attempting to create a persona with non-existent account must fail."""
    non_existent_account_id = uuid.uuid4()
    persona = Persona(
        account_id=non_existent_account_id,
        display_name="OrphanPersona",
        avatar_seed="seed-orphan",
    )
    db_session.add(persona)

    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_cascade_delete_account_deletes_personas(db_session: AsyncSession):
    """Deleting an account must cascade-delete all its associated personas."""
    account = Account(
        supabase_user_id=uuid.uuid4(),
        email_hash="hash-cascade-test-1",
        is_age_verified=True,
        invite_quota=3,
    )
    db_session.add(account)
    await db_session.flush()

    persona = Persona(
        account_id=account.id,
        display_name="CascadeTester",
        avatar_seed="seed-cascade",
    )
    db_session.add(persona)
    await db_session.flush()

    # Verify persona exists
    persona_id = persona.id
    res = await db_session.execute(select(Persona).where(Persona.id == persona_id))
    assert res.scalar_one_or_none() is not None

    # Delete account
    await db_session.delete(account)
    await db_session.flush()

    # Persona should be gone
    res = await db_session.execute(select(Persona).where(Persona.id == persona_id))
    assert res.scalar_one_or_none() is None
    await db_session.rollback()


@pytest.mark.asyncio
async def test_account_isolation_from_social_persona(db_session: AsyncSession):
    """
    Social data (Persona, Post) must never expose Supabase user UUID or real email.
    """
    supabase_id = uuid.uuid4()
    account = Account(
        supabase_user_id=supabase_id,
        email_hash="isolated-email-hash-1234",
        is_age_verified=True,
    )
    db_session.add(account)
    await db_session.flush()

    persona = Persona(
        account_id=account.id,
        display_name="GhostScholar",
        avatar_seed="ghost-scholar-seed",
    )
    db_session.add(persona)
    await db_session.flush()

    post = Post(
        persona_id=persona.id,
        content="Testing privacy isolation in social layers.",
        post_type=PostType.CONFESSION,
    )
    db_session.add(post)
    await db_session.flush()

    # Querying post with its persona
    res = await db_session.execute(
        select(Post, Persona.display_name, Persona.avatar_seed)
        .join(Persona, Post.persona_id == Persona.id)
        .where(Post.id == post.id)
    )
    row = res.one()
    queried_post, display_name, avatar_seed = row

    # Assert social layer properties
    assert display_name == "GhostScholar"
    assert avatar_seed == "ghost-scholar-seed"
    # Ensure post does not hold supabase_user_id column
    assert not hasattr(queried_post, "supabase_user_id")
    assert not hasattr(queried_post, "email")
    await db_session.rollback()


@pytest.mark.asyncio
async def test_persona_ownership(db_session: AsyncSession):
    """Verify persona belongs strictly to owning account."""
    acc1 = Account(supabase_user_id=uuid.uuid4(), email_hash="hash-owner-1", is_age_verified=True)
    acc2 = Account(supabase_user_id=uuid.uuid4(), email_hash="hash-owner-2", is_age_verified=True)
    db_session.add_all([acc1, acc2])
    await db_session.flush()

    p1 = Persona(account_id=acc1.id, display_name="OwnerP1", avatar_seed="seed-p1")
    db_session.add(p1)
    await db_session.flush()

    # Verify ownership
    assert p1.account_id == acc1.id
    assert p1.account_id != acc2.id
    await db_session.rollback()


@pytest.mark.asyncio
async def test_conversation_membership_and_duplicate_prevention(db_session: AsyncSession):
    """
    Cannot add the same persona twice to the same conversation.
    """
    acc = Account(supabase_user_id=uuid.uuid4(), email_hash="hash-conv-acc", is_age_verified=True)
    db_session.add(acc)
    await db_session.flush()

    p1 = Persona(account_id=acc.id, display_name="Member1", avatar_seed="seed-m1")
    p2 = Persona(account_id=acc.id, display_name="Member2", avatar_seed="seed-m2")
    db_session.add_all([p1, p2])
    await db_session.flush()

    conv = Conversation()
    db_session.add(conv)
    await db_session.flush()

    part1 = ConversationParticipant(conversation_id=conv.id, persona_id=p1.id)
    db_session.add(part1)
    await db_session.flush()

    # Adding duplicate participant for same persona in same conversation must raise IntegrityError
    dup_part = ConversationParticipant(conversation_id=conv.id, persona_id=p1.id)
    db_session.add(dup_part)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_no_self_connection_request(db_session: AsyncSession):
    """Persona cannot send a connection request to themselves."""
    acc = Account(supabase_user_id=uuid.uuid4(), email_hash="hash-self-conn", is_age_verified=True)
    db_session.add(acc)
    await db_session.flush()

    p = Persona(account_id=acc.id, display_name="SelfConnector", avatar_seed="seed-sc")
    db_session.add(p)
    await db_session.flush()

    self_req = ConnectionRequest(
        sender_persona_id=p.id,
        recipient_persona_id=p.id,
        status=ConnectionRequestStatus.PENDING,
    )
    db_session.add(self_req)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_no_self_block(db_session: AsyncSession):
    """Persona cannot block themselves."""
    acc = Account(supabase_user_id=uuid.uuid4(), email_hash="hash-self-block", is_age_verified=True)
    db_session.add(acc)
    await db_session.flush()

    p = Persona(account_id=acc.id, display_name="SelfBlocker", avatar_seed="seed-sb")
    db_session.add(p)
    await db_session.flush()

    self_block = Block(
        blocker_persona_id=p.id,
        blocked_persona_id=p.id,
    )
    db_session.add(self_block)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()
