"""009_stories_and_events

Revision ID: 009
Revises: 008
Create Date: 2026-11-18 08:20:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update stories table
    op.add_column(
        "stories",
        sa.Column("category", sa.String(length=50), nullable=False, server_default="night-thoughts"),
    )
    op.add_column(
        "stories",
        sa.Column("allow_comments", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "stories",
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="PUBLIC"),
    )
    op.add_column(
        "stories",
        sa.Column("campus_name", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "stories",
        sa.Column("moderation_status", sa.String(length=20), nullable=False, server_default="APPROVED"),
    )
    op.add_column(
        "stories",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_index("ix_stories_category", "stories", ["category"])
    op.create_index("ix_stories_expires_deleted", "stories", ["expires_at", "is_deleted"])

    # 2. Create story_comments table
    op.create_table(
        "story_comments",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "story_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("stories.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "persona_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("personas.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_story_comments_story_created", "story_comments", ["story_id", "created_at"])

    # 3. Update events table
    op.add_column(
        "events",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_events_time_cancelled", "events", ["event_time", "is_cancelled", "is_deleted"])


def downgrade() -> None:
    op.drop_index("ix_events_time_cancelled", table_name="events")
    op.drop_column("events", "is_deleted")

    op.drop_index("ix_story_comments_story_created", table_name="story_comments")
    op.drop_table("story_comments")

    op.drop_index("ix_stories_expires_deleted", table_name="stories")
    op.drop_index("ix_stories_category", table_name="stories")
    op.drop_column("stories", "is_deleted")
    op.drop_column("stories", "moderation_status")
    op.drop_column("stories", "campus_name")
    op.drop_column("stories", "visibility")
    op.drop_column("stories", "allow_comments")
    op.drop_column("stories", "category")
