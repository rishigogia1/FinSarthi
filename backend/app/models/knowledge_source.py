"""
models/knowledge_source.py — Global RAG knowledge sources.

No user FK — this is a global/admin-managed table (not per-user).
Phase 8 (RAG Tool) owns this table's content.
"""
from datetime import datetime
from sqlalchemy import Boolean, String, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
