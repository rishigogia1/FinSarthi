"""
models/agent_log.py — Append-only execution trace per agent run.

ON DELETE CASCADE from agent_runs (which cascades from conversations → users).
This is the deepest node in the cascade chain.

Security rule (Phase 9 must enforce):
  detail JSONB may contain tool call parameters — Phase 9 (Agents) must ensure
  no raw user PII or secrets are written into this column.
"""
from datetime import datetime
from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    agent_run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)  # e.g. 'tool_call', 'error', 'output'
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    agent_run = relationship("AgentRun", back_populates="agent_logs")

    __table_args__ = (
        Index("ix_agent_logs_agent_run_id", "agent_run_id"),
        Index("ix_agent_logs_created_at", "created_at"),
    )
