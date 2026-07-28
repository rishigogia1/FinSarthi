"""
models/agent_run.py — Live agent execution status per conversation.

ON DELETE CASCADE from conversations (which cascades from users).
Indexed on conversation_id — queried frequently to show run status per chat.
"""
from datetime import datetime
from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    # Valid status values: queued | running | completed | failed
    # Enforced at service layer, not DB layer
    status: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    conversation = relationship("Conversation", back_populates="agent_runs")
    agent_logs = relationship("AgentLog", back_populates="agent_run", passive_deletes=True)

    __table_args__ = (
        Index("ix_agent_runs_conversation_id", "conversation_id"),
    )
