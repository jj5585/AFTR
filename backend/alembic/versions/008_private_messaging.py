"""008_private_messaging

Revision ID: 008
Revises: 007
Create Date: 2026-11-18 08:08:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update conversations
    op.add_column(
        "conversations",
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "blocked_by_persona_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("personas.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # 2. Update conversation_participants
    op.add_column(
        "conversation_participants",
        sa.Column("conversation_pseudonym", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "conversation_participants",
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 3. Update messages
    op.add_column(
        "messages",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "messages",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index(
        "ix_messages_conv_created",
        "messages",
        ["conversation_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_messages_conv_created", table_name="messages")
    op.drop_column("messages", "is_encrypted")
    op.drop_column("messages", "deleted_at")
    op.drop_column("messages", "is_deleted")

    op.drop_column("conversation_participants", "last_read_at")
    op.drop_column("conversation_participants", "conversation_pseudonym")

    op.drop_column("conversations", "blocked_by_persona_id")
    op.drop_column("conversations", "last_message_at")
