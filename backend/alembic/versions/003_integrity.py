"""003_integrity

Revision ID: 003
Revises: 002
Create Date: 2026-11-18 07:12:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Connection Requests (Consent-Gated)
    op.create_table(
        "connection_requests",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("sender_persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("sender_persona_id", "recipient_persona_id", name="uq_sender_recipient_connection"),
        sa.CheckConstraint("sender_persona_id <> recipient_persona_id", name="chk_no_self_connection_request"),
    )
    op.create_index("ix_connection_requests_sender_persona_id", "connection_requests", ["sender_persona_id"])
    op.create_index("ix_connection_requests_recipient_persona_id", "connection_requests", ["recipient_persona_id"])
    op.create_index("ix_connection_requests_status", "connection_requests", ["status"])

    # 2. Matches (Anonymous Compatibility Discovery)
    op.create_table(
        "matches",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("persona_a_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("persona_b_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("compatibility_score", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("persona_a_id", "persona_b_id", name="uq_canonical_match_pair"),
        sa.CheckConstraint("persona_a_id <> persona_b_id", name="chk_no_self_match"),
    )
    op.create_index("ix_matches_persona_a_id", "matches", ["persona_a_id"])
    op.create_index("ix_matches_persona_b_id", "matches", ["persona_b_id"])

    # 3. Conversations & Participants
    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("connection_request_id", sa.Uuid(as_uuid=True), sa.ForeignKey("connection_requests.id", ondelete="SET NULL"), unique=True, nullable=True),
        sa.Column("match_id", sa.Uuid(as_uuid=True), sa.ForeignKey("matches.id", ondelete="SET NULL"), unique=True, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "conversation_participants",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", sa.Uuid(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("conversation_id", "persona_id", name="uq_conversation_participant"),
    )
    op.create_index("ix_conversation_participants_conversation_id", "conversation_participants", ["conversation_id"])
    op.create_index("ix_conversation_participants_persona_id", "conversation_participants", ["persona_id"])

    # 4. Messages (Mutual Consent Direct Messaging)
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", sa.Uuid(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_sender_persona_id", "messages", ["sender_persona_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])

    # 5. Blocks (Universal Anti-Harassment)
    op.create_table(
        "blocks",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("blocker_persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("blocked_persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("blocker_persona_id", "blocked_persona_id", name="uq_persona_block"),
        sa.CheckConstraint("blocker_persona_id <> blocked_persona_id", name="chk_no_self_block"),
    )
    op.create_index("ix_blocks_blocker_persona_id", "blocks", ["blocker_persona_id"])
    op.create_index("ix_blocks_blocked_persona_id", "blocks", ["blocked_persona_id"])

    # 6. Reports (Content & Persona Safety)
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("reporter_persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_type", sa.String(length=30), nullable=False),
        sa.Column("target_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_reports_reporter_persona_id", "reports", ["reporter_persona_id"])
    op.create_index("ix_reports_target_type", "reports", ["target_type"])
    op.create_index("ix_reports_target_id", "reports", ["target_id"])
    op.create_index("ix_reports_status", "reports", ["status"])

    # 7. Moderation Actions & Strikes
    op.create_table(
        "moderation_actions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("target_type", sa.String(length=30), nullable=False),
        sa.Column("target_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(length=30), nullable=False),
        sa.Column("moderator_id", sa.Uuid(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("strike_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_moderation_actions_target_type", "moderation_actions", ["target_type"])
    op.create_index("ix_moderation_actions_target_id", "moderation_actions", ["target_id"])
    op.create_index("ix_moderation_actions_action_type", "moderation_actions", ["action_type"])

    # 8. Appeals
    op.create_table(
        "appeals",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("moderation_action_id", sa.Uuid(as_uuid=True), sa.ForeignKey("moderation_actions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("appellant_persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("reviewed_by", sa.Uuid(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_appeals_moderation_action_id", "appeals", ["moderation_action_id"])
    op.create_index("ix_appeals_appellant_persona_id", "appeals", ["appellant_persona_id"])
    op.create_index("ix_appeals_status", "appeals", ["status"])


def downgrade() -> None:
    op.drop_table("appeals")
    op.drop_table("moderation_actions")
    op.drop_table("reports")
    op.drop_table("blocks")
    op.drop_table("messages")
    op.drop_table("conversation_participants")
    op.drop_table("conversations")
    op.drop_table("matches")
    op.drop_table("connection_requests")
