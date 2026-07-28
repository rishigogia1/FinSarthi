"""
models/digital_twin.py — User's financial profile twin.

One-to-one with users (UNIQUE on user_id).
accessibility_needs: JSONB with server_default='{}'. Shape is enforced at the
  Pydantic layer only — no DB-level CHECK constraint per Phase 3 decision.
  This keeps the column flexible for future field additions without a migration.
"""
from datetime import datetime
from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base


class DigitalTwin(Base):
    __tablename__ = "digital_twins"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # One digital twin per user
    )
    financial_goals: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    income_pattern: Mapped[str | None] = mapped_column(String, nullable=True)
    risk_appetite: Mapped[str | None] = mapped_column(String, nullable=True)
    literacy_level: Mapped[str | None] = mapped_column(String, nullable=True)
    language_preference: Mapped[str | None] = mapped_column(String, nullable=True)
    # Shape enforced at Pydantic layer only (see DigitalTwinSchema in later phases)
    accessibility_needs: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    behavioral_notes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    user = relationship("User", back_populates="digital_twin")
