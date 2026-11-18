"""004_invitation_system

Revision ID: 004
Revises: 003
Create Date: 2026-11-18 07:13:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Invitations Table
    op.create_table(
        "invitations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("inviter_account_id", sa.Uuid(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("recipient_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_by_account_id", sa.Uuid(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("expires_at > created_at", name="chk_invitation_expiry_future"),
    )
    op.create_index("ix_invitations_token_hash", "invitations", ["token_hash"], unique=True)
    op.create_index("ix_invitations_recipient_hash", "invitations", ["recipient_hash"])
    op.create_index("ix_invitations_status", "invitations", ["status"])
    op.create_index("ix_invitations_expires_at", "invitations", ["expires_at"])
    op.create_index("ix_invitations_inviter_account_id", "invitations", ["inviter_account_id"])

    # 2. Non-negative invite quota constraint on accounts
    op.create_check_constraint(
        "chk_account_invite_quota_non_negative",
        "accounts",
        "invite_quota >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("chk_account_invite_quota_non_negative", "accounts", type_="check")
    op.drop_table("invitations")
