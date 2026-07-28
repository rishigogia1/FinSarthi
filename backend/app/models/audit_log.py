"""
models/audit_log.py — Append-only user action audit trail.

ON DELETE CASCADE from users: user deletion (right-to-deletion) removes
their entire audit history. This is deliberate and noted in Phase 3.

SECURITY: No application code path should expose a DELETE on this table.
  - No repository will implement a delete method for audit_logs.
  - The only row removal is via the cascade from a users row deletion.
"""
from datetime import datetime
from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

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
    action: Mapped[str] = mapped_column(String, nullable=False)  # e.g. 'profile_updated', 'goal_created'
    before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )
