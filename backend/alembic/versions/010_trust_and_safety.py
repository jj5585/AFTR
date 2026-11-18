"""010_trust_and_safety

Revision ID: 010
Revises: 009
Create Date: 2026-11-18 09:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update accounts table with role and MFA
    op.add_column(
        "accounts",
        sa.Column("role", sa.String(length=30), nullable=False, server_default="USER"),
    )
    op.add_column(
        "accounts",
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "accounts",
        sa.Column("mfa_secret", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_accounts_role", "accounts", ["role"])

    # 2. Update comments table with moderation_status
    op.add_column(
        "comments",
        sa.Column("moderation_status", sa.String(length=20), nullable=False, server_default="PUBLISHED"),
    )
    op.create_index("ix_comments_moderation_status", "comments", ["moderation_status"])

    # 3. Update reports table with resolution fields
    op.add_column(
        "reports",
        sa.Column(
            "resolved_by",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("accounts.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "reports",
        sa.Column("resolution_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "reports",
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 4. Update moderation_actions table with target_persona_id
    op.add_column(
        "moderation_actions",
        sa.Column(
            "target_persona_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("personas.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_moderation_actions_target_persona", "moderation_actions", ["target_persona_id"])

    # 5. Update appeals table with resolution_notes
    op.add_column(
        "appeals",
        sa.Column("resolution_notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("appeals", "resolution_notes")
    op.drop_index("ix_moderation_actions_target_persona", table_name="moderation_actions")
    op.drop_column("moderation_actions", "target_persona_id")
    op.drop_column("reports", "resolved_at")
    op.drop_column("reports", "resolution_notes")
    op.drop_column("reports", "resolved_by")
    op.drop_index("ix_comments_moderation_status", table_name="comments")
    op.drop_column("comments", "moderation_status")
    op.drop_index("ix_accounts_role", table_name="accounts")
    op.drop_column("accounts", "mfa_secret")
    op.drop_column("accounts", "mfa_enabled")
    op.drop_column("accounts", "role")
