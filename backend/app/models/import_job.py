"""
models/import_job.py — Import jobs metadata tracking.

ON DELETE CASCADE from users.
"""
from datetime import datetime
from sqlalchemy import ForeignKey, Index, String, text, TIMESTAMP, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class ImportJob(Base):
    __tablename__ = "import_jobs"

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
    filename: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="uploaded", server_default="uploaded")
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    accepted_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    duplicate_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    rejected_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_summary: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Stores ONLY capped preview data arrays to avoid bloating db
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    user = relationship("User", back_populates="import_jobs")

    __table_args__ = (
        Index("ix_import_jobs_user_id", "user_id"),
    )
