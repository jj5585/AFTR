"""006_social_feed

Revision ID: 006
Revises: 005
Create Date: 2026-11-18 07:42:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add social feed columns to posts
    op.add_column(
        "posts",
        sa.Column("allow_comments", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "posts",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "posts",
        sa.Column("moderation_status", sa.String(length=20), nullable=False, server_default=sa.text("'PUBLISHED'")),
    )
    op.add_column(
        "posts",
        sa.Column("campus_name", sa.String(length=120), nullable=True),
    )

    # 2. Add soft deletion to comments
    op.add_column(
        "comments",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    # 3. Create high-performance indexes for feeds and filtering
    op.create_index("ix_posts_campus_name", "posts", ["campus_name"])
    op.create_index("ix_posts_moderation_status", "posts", ["moderation_status"])
    op.create_index("ix_posts_feed", "posts", ["is_deleted", "moderation_status", "created_at"])
    op.create_index("ix_comments_post_feed", "comments", ["post_id", "is_deleted", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_comments_post_feed", table_name="comments")
    op.drop_index("ix_posts_feed", table_name="posts")
    op.drop_index("ix_posts_moderation_status", table_name="posts")
    op.drop_index("ix_posts_campus_name", table_name="posts")

    op.drop_column("comments", "is_deleted")

    op.drop_column("posts", "campus_name")
    op.drop_column("posts", "moderation_status")
    op.drop_column("posts", "is_deleted")
    op.drop_column("posts", "allow_comments")
