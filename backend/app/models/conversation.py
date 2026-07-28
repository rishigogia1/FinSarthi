"""
models/conversation.py — Chat conversation sessions.

ON DELETE CASCADE from users.
Indexed on user_id (FK lookup) and created_at (sort order for list endpoints).
"""
from datetime import datetime
from sqlalchemy import ForeignKey, Index, String, JSON, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    workflow_id: Mapped[str | None] = mapped_column(String, nullable=True)
    workflow_status: Mapped[str | None] = mapped_column(String, nullable=True, default="ACTIVE")
    primary_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    supporting_agents: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    workflow_state: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    workflow_memory: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", passive_deletes=True)
    agent_runs = relationship("AgentRun", back_populates="conversation", passive_deletes=True)

    __table_args__ = (
        Index("ix_conversations_user_id", "user_id"),
        Index("ix_conversations_created_at", "created_at"),
    )
