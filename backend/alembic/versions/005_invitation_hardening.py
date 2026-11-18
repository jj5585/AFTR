"""005_invitation_hardening

Revision ID: 005
Revises: 004
Create Date: 2026-11-18 07:14:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. State machine integrity constraints on invitations
    op.create_check_constraint(
        "chk_invitation_used_integrity",
        "invitations",
        "(status <> 'USED') OR (used_by_account_id IS NOT NULL AND used_at IS NOT NULL)",
    )

    op.create_check_constraint(
        "chk_invitation_revoked_integrity",
        "invitations",
        "(status <> 'REVOKED') OR (revoked_at IS NOT NULL)",
    )

    op.create_check_constraint(
        "chk_no_self_invitation",
        "invitations",
        "(used_by_account_id IS NULL) OR (used_by_account_id <> inviter_account_id)",
    )

    # 2. Concurrency-safe atomic redemption function (PostgreSQL)
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION aftr_redeem_invitation_atomic(
                p_token_hash VARCHAR(64),
                p_recipient_hash VARCHAR(64),
                p_used_by_account_id UUID
            )
            RETURNS TABLE (
                success BOOLEAN,
                invitation_id UUID,
                error_code VARCHAR(50)
            )
            LANGUAGE plpgsql
            SECURITY DEFINER
            AS $$
            DECLARE
                v_invitation RECORD;
            BEGIN
                -- 1. Locate and lock row for update to prevent concurrent race conditions
                SELECT id, inviter_account_id, status, expires_at, recipient_hash
                INTO v_invitation
                FROM invitations
                WHERE token_hash = p_token_hash
                FOR UPDATE;

                -- Check existence
                IF NOT FOUND THEN
                    RETURN QUERY SELECT false, NULL::UUID, 'INVITATION_NOT_FOUND'::VARCHAR;
                    RETURN;
                END IF;

                -- Check status
                IF v_invitation.status = 'USED' THEN
                    RETURN QUERY SELECT false, v_invitation.id, 'INVITATION_ALREADY_USED'::VARCHAR;
                    RETURN;
                ELSIF v_invitation.status = 'REVOKED' THEN
                    RETURN QUERY SELECT false, v_invitation.id, 'INVITATION_REVOKED'::VARCHAR;
                    RETURN;
                ELSIF v_invitation.status = 'EXPIRED' OR v_invitation.expires_at <= clock_timestamp() THEN
                    -- Mark as expired if not already marked
                    UPDATE invitations SET status = 'EXPIRED', updated_at = clock_timestamp() WHERE id = v_invitation.id;
                    RETURN QUERY SELECT false, v_invitation.id, 'INVITATION_EXPIRED'::VARCHAR;
                    RETURN;
                END IF;

                -- Check recipient binding
                IF v_invitation.recipient_hash <> p_recipient_hash THEN
                    RETURN QUERY SELECT false, v_invitation.id, 'RECIPIENT_MISMATCH'::VARCHAR;
                    RETURN;
                END IF;

                -- Check self-invitation
                IF v_invitation.inviter_account_id = p_used_by_account_id THEN
                    RETURN QUERY SELECT false, v_invitation.id, 'SELF_INVITATION_FORBIDDEN'::VARCHAR;
                    RETURN;
                END IF;

                -- 2. Execute atomic redemption
                UPDATE invitations
                SET
                    status = 'USED',
                    used_by_account_id = p_used_by_account_id,
                    used_at = clock_timestamp(),
                    updated_at = clock_timestamp()
                WHERE id = v_invitation.id;

                RETURN QUERY SELECT true, v_invitation.id, 'SUCCESS'::VARCHAR;
                RETURN;
            END;
            $$;
            """
        )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("DROP FUNCTION IF EXISTS aftr_redeem_invitation_atomic(VARCHAR, VARCHAR, UUID);")

    op.drop_constraint("chk_no_self_invitation", "invitations", type_="check")
    op.drop_constraint("chk_invitation_revoked_integrity", "invitations", type_="check")
    op.drop_constraint("chk_invitation_used_integrity", "invitations", type_="check")
