"""
models/user.py — User account table.

Phase 5 contract: email must be lowercased before INSERT and before any
lookup query, so the functional lower(email) index is actually used.
"""
from datetime import datetime
from sqlalchemy import Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="user", server_default="user")
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    # Relationships (used for cascade awareness — not for lazy-loading in async)
    refresh_tokens = relationship("RefreshToken", back_populates="user", passive_deletes=True)
    digital_twin = relationship("DigitalTwin", back_populates="user", passive_deletes=True, uselist=False)
    user_preference = relationship("UserPreference", back_populates="user", passive_deletes=True, uselist=False)
    conversations = relationship("Conversation", back_populates="user", passive_deletes=True)
    goals = relationship("Goal", back_populates="user", passive_deletes=True)
    audit_logs = relationship("AuditLog", back_populates="user", passive_deletes=True)
    transactions = relationship("Transaction", back_populates="user", passive_deletes=True)
    recurring_cashflows = relationship("RecurringCashflow", back_populates="user", passive_deletes=True)
    budgets = relationship("Budget", back_populates="user", passive_deletes=True)
    import_jobs = relationship("ImportJob", back_populates="user", passive_deletes=True)
    notifications = relationship("Notification", back_populates="user", passive_deletes=True)

    # Functional index on lower(email) for case-insensitive lookups
    # Phase 5 must lowercase emails before insert/lookup for this index to be used.
    __table_args__ = (
        Index("ix_users_email_lower", text("lower(email)")),
    )
