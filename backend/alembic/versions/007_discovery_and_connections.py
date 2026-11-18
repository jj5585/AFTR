"""007_discovery_and_connections

Revision ID: 007
Revises: 006
Create Date: 2026-11-18 07:56:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add discovery fields to personas
    op.add_column(
        "personas",
        sa.Column("is_discoverable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "personas",
        sa.Column("relationship_intention", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "personas",
        sa.Column("min_age_preference", sa.Integer(), nullable=False, server_default=sa.text("18")),
    )
    op.add_column(
        "personas",
        sa.Column("max_age_preference", sa.Integer(), nullable=False, server_default=sa.text("99")),
    )
    op.add_column(
        "personas",
        sa.Column("dating_preferences_json", sa.Text(), nullable=True),
    )

    op.create_index("ix_personas_is_discoverable", "personas", ["is_discoverable"])
    op.create_index("ix_personas_relationship_intention", "personas", ["relationship_intention"])

    # 2. Add optional introductory note to connection_requests
    op.add_column(
        "connection_requests",
        sa.Column("note", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("connection_requests", "note")

    op.drop_index("ix_personas_relationship_intention", table_name="personas")
    op.drop_index("ix_personas_is_discoverable", table_name="personas")

    op.drop_column("personas", "dating_preferences_json")
    op.drop_column("personas", "max_age_preference")
    op.drop_column("personas", "min_age_preference")
    op.drop_column("personas", "relationship_intention")
    op.drop_column("personas", "is_discoverable")
