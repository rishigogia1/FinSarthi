"""initial schema — all 11 tables

Revision ID: 0001
Revises: 
Create Date: 2026-07-15

Creates all 11 tables per Phase 3's schema design:
  users, refresh_tokens, digital_twins, user_preferences,
  conversations, messages, agent_runs, agent_logs,
  goals, knowledge_sources, audit_logs

Requires: pgcrypto extension (for gen_random_uuid()).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Enable pgcrypto for gen_random_uuid() server-side UUID generation.
    # Must come before any table creation that uses gen_random_uuid().
    # ------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ------------------------------------------------------------------
    # users — root table; all user-scoped tables cascade from here.
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    # Functional index for case-insensitive email lookups
    # Phase 5 contract: must lowercase emails before INSERT and before SELECT
    op.create_index("ix_users_email_lower", "users", [sa.text("lower(email)")], unique=False)

    # ------------------------------------------------------------------
    # refresh_tokens
    # ------------------------------------------------------------------
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default="false", nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    # ------------------------------------------------------------------
    # digital_twins — one-to-one with users
    # ------------------------------------------------------------------
    op.create_table(
        "digital_twins",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("financial_goals", postgresql.JSONB(), nullable=True),
        sa.Column("income_pattern", sa.String(), nullable=True),
        sa.Column("risk_appetite", sa.String(), nullable=True),
        sa.Column("literacy_level", sa.String(), nullable=True),
        sa.Column("language_preference", sa.String(), nullable=True),
        # No DB-level CHECK constraint — shape enforced at Pydantic layer only (Phase 3 decision)
        sa.Column(
            "accessibility_needs",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("behavioral_notes", postgresql.JSONB(), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_digital_twins_user_id"),
    )

    # ------------------------------------------------------------------
    # user_preferences — one-to-one with users (UI state only)
    # ------------------------------------------------------------------
    op.create_table(
        "user_preferences",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("theme", sa.String(), server_default="light", nullable=False),
        sa.Column("notifications_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_preferences_user_id"),
    )

    # ------------------------------------------------------------------
    # conversations
    # ------------------------------------------------------------------
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_index("ix_conversations_created_at", "conversations", ["created_at"])

    # ------------------------------------------------------------------
    # messages
    # ------------------------------------------------------------------
    op.create_table(
        "messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])

    # ------------------------------------------------------------------
    # agent_runs
    # ------------------------------------------------------------------
    op.create_table(
        "agent_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_runs_conversation_id", "agent_runs", ["conversation_id"])

    # ------------------------------------------------------------------
    # agent_logs — deepest node in cascade chain
    # ------------------------------------------------------------------
    op.create_table(
        "agent_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("agent_run_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("detail", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_logs_agent_run_id", "agent_logs", ["agent_run_id"])
    op.create_index("ix_agent_logs_created_at", "agent_logs", ["created_at"])

    # ------------------------------------------------------------------
    # goals
    # ------------------------------------------------------------------
    op.create_table(
        "goals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("goal_name", sa.String(), nullable=False),
        sa.Column("target_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("current_amount", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("status", sa.String(), server_default="active", nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goals_user_id", "goals", ["user_id"])

    # ------------------------------------------------------------------
    # knowledge_sources — global table, no user FK
    # ------------------------------------------------------------------
    op.create_table(
        "knowledge_sources",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("source_name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("ingested_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # audit_logs — append-only; no application-layer DELETE path.
    # Only removed via cascade from users row deletion (right-to-deletion).
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("before", postgresql.JSONB(), nullable=True),
        sa.Column("after", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    # Drop in reverse dependency order — deepest tables first.
    op.drop_table("audit_logs")
    op.drop_table("knowledge_sources")
    op.drop_table("goals")
    op.drop_table("agent_logs")
    op.drop_table("agent_runs")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("user_preferences")
    op.drop_table("digital_twins")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    # Drop extension last — only after all tables using it are gone.
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
