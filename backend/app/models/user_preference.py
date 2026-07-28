"""
models/user_preference.py — UI/behavioral preferences (distinct from digital_twin).

One-to-one with users (UNIQUE on user_id).
Stores only UI state: theme and notification switches.
Financial profile data lives in digital_twins.
"""
from datetime import datetime
from sqlalchemy import Boolean, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # One preference row per user
    )
    theme: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="light",
        server_default="light",
    )
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    user = relationship("User", back_populates="user_preference")
