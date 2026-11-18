"""001_initial_schema

Revision ID: 001
Revises: None
Create Date: 2026-11-18 07:10:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Accounts (Identity Domain - Protected)
    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("supabase_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("email_hash", sa.String(length=64), nullable=False),
        sa.Column("is_age_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("birth_year", sa.Integer(), nullable=True),
        sa.Column("invite_quota", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_accounts_supabase_user_id", "accounts", ["supabase_user_id"], unique=True)
    op.create_index("ix_accounts_email_hash", "accounts", ["email_hash"], unique=True)

    # 2. Anonymous Personas
    op.create_table(
        "personas",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("account_id", sa.Uuid(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_name", sa.String(length=50), nullable=False),
        sa.Column("avatar_seed", sa.String(length=100), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_personas_account_id", "personas", ["account_id"])
    op.create_index("ix_personas_display_name", "personas", ["display_name"])

    # 3. Optional Self-Declared Campus Affiliations
    op.create_table(
        "campus_affiliations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("campus_name", sa.String(length=120), nullable=False),
        sa.Column("campus_code", sa.String(length=30), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_campus_affiliations_persona_id", "campus_affiliations", ["persona_id"])
    op.create_index("ix_campus_affiliations_campus_name", "campus_affiliations", ["campus_name"])

    # 4. Adult & Campus Interests
    op.create_table(
        "interests",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("is_adult", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_interests_name", "interests", ["name"], unique=True)
    op.create_index("ix_interests_slug", "interests", ["slug"], unique=True)

    op.create_table(
        "persona_interests",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interest_id", sa.Uuid(as_uuid=True), sa.ForeignKey("interests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("persona_id", "interest_id", name="uq_persona_interest"),
    )
    op.create_index("ix_persona_interests_persona_id", "persona_interests", ["persona_id"])
    op.create_index("ix_persona_interests_interest_id", "persona_interests", ["interest_id"])

    # 5. Posts (Confessions & Adult Discussions)
    op.create_table(
        "posts",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("post_type", sa.String(length=20), nullable=False, server_default=sa.text("'CONFESSION'")),
        sa.Column("tag", sa.String(length=50), nullable=False, server_default=sa.text("'general'")),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_posts_persona_id", "posts", ["persona_id"])
    op.create_index("ix_posts_post_type", "posts", ["post_type"])
    op.create_index("ix_posts_tag", "posts", ["tag"])
    op.create_index("ix_posts_created_at", "posts", ["created_at"])

    # 6. Comments (Threaded)
    op.create_table(
        "comments",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("post_id", sa.Uuid(as_uuid=True), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", sa.Uuid(as_uuid=True), sa.ForeignKey("comments.id", ondelete="CASCADE"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_comments_post_id", "comments", ["post_id"])
    op.create_index("ix_comments_persona_id", "comments", ["persona_id"])

    # 7. Reactions
    op.create_table(
        "reactions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("reaction_type", sa.String(length=20), nullable=False, server_default=sa.text("'UPVOTE'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("persona_id", "target_type", "target_id", "reaction_type", name="uq_persona_reaction_target"),
    )
    op.create_index("ix_reactions_persona_id", "reactions", ["persona_id"])
    op.create_index("ix_reactions_target_type", "reactions", ["target_type"])
    op.create_index("ix_reactions_target_id", "reactions", ["target_id"])

    # 8. Stories (24h Ephemeral)
    op.create_table(
        "stories",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_stories_persona_id", "stories", ["persona_id"])
    op.create_index("ix_stories_expires_at", "stories", ["expires_at"])

    # 9. Events & Attendees
    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("creator_persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("campus_name", sa.String(length=120), nullable=True),
        sa.Column("location_name", sa.String(length=150), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_attendees", sa.Integer(), nullable=True),
        sa.Column("is_cancelled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_events_creator_persona_id", "events", ["creator_persona_id"])
    op.create_index("ix_events_event_time", "events", ["event_time"])
    op.create_index("ix_events_campus_name", "events", ["campus_name"])

    op.create_table(
        "event_attendees",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("event_id", sa.Uuid(as_uuid=True), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("persona_id", sa.Uuid(as_uuid=True), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'GOING'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("event_id", "persona_id", name="uq_event_attendee"),
    )
    op.create_index("ix_event_attendees_event_id", "event_attendees", ["event_id"])
    op.create_index("ix_event_attendees_persona_id", "event_attendees", ["persona_id"])


def downgrade() -> None:
    op.drop_table("event_attendees")
    op.drop_table("events")
    op.drop_table("stories")
    op.drop_table("reactions")
    op.drop_table("comments")
    op.drop_table("posts")
    op.drop_table("persona_interests")
    op.drop_table("interests")
    op.drop_table("campus_affiliations")
    op.drop_table("personas")
    op.drop_table("accounts")
