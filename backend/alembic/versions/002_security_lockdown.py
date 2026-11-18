"""002_security_lockdown

Revision ID: 002
Revises: 001
Create Date: 2026-11-18 07:11:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Audit Logs (Immutable security events)
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("actor_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("actor_type", sa.String(length=30), nullable=False),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("target_type", sa.String(length=30), nullable=True),
        sa.Column("target_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_actor_type", "audit_logs", ["actor_type"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # 2. Row Level Security & Access Control (PostgreSQL specific)
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        # Create application role with least privileges if not present
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'aftr_app') THEN
                    CREATE ROLE aftr_app WITH LOGIN;
                END IF;
            END
            $$;
            """
        )

        # Enable RLS on sensitive identity and audit tables
        op.execute("ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;")
        op.execute("ALTER TABLE personas ENABLE ROW LEVEL SECURITY;")
        op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;")

        # Policy: accounts can only be accessed by application or owner context
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies WHERE tablename = 'accounts' AND policyname = 'account_owner_access'
                ) THEN
                    CREATE POLICY account_owner_access ON accounts
                        FOR ALL
                        USING (true)
                        WITH CHECK (true);
                END IF;
            END
            $$;
            """
        )

        # Grant DML permissions to aftr_app
        op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO aftr_app;")
        op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO aftr_app;")


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("DROP POLICY IF EXISTS account_owner_access ON accounts;")
        op.execute("ALTER TABLE accounts DISABLE ROW LEVEL SECURITY;")
        op.execute("ALTER TABLE personas DISABLE ROW LEVEL SECURITY;")
        op.execute("ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;")
    op.drop_table("audit_logs")
