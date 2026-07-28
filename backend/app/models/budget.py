"""
models/budget.py — Budget limit model.
"""
from datetime import date, datetime
from sqlalchemy import ForeignKey, Index, Numeric, String, text, Date, Boolean, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class Budget(Base):
    __tablename__ = "budgets"

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
    category: Mapped[str] = mapped_column(String, nullable=False)
    limit_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False, default="monthly", server_default="monthly")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
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

    user = relationship("User", back_populates="budgets")

    __table_args__ = (
        Index("ix_budgets_user_id", "user_id"),
    )
