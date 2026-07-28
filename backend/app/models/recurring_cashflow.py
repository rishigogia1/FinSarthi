"""
models/recurring_cashflow.py — Recurring cashflow model.
"""
from datetime import date, datetime
from sqlalchemy import ForeignKey, Index, Numeric, String, text, Date, Boolean, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class RecurringCashflow(Base):
    __tablename__ = "recurring_cashflows"

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
    type: Mapped[str] = mapped_column(String, nullable=False)  # income or expense
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    frequency: Mapped[str] = mapped_column(String, nullable=False, default="monthly", server_default="monthly")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    note: Mapped[str | None] = mapped_column(String, nullable=True)
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

    user = relationship("User", back_populates="recurring_cashflows")

    __table_args__ = (
        Index("ix_recurring_cashflows_user_id", "user_id"),
    )
