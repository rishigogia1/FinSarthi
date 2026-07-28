"""
models/transaction.py — Transactions model.
"""
from datetime import date, datetime
from sqlalchemy import ForeignKey, Index, Numeric, String, text, Date, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


BUILTIN_CATEGORIES = [
    "Food",
    "Shopping",
    "Transport",
    "Bills",
    "Utilities",
    "Entertainment",
    "Healthcare",
    "Education",
    "Travel",
    "Salary",
    "Investment",
    "Other",
]

TRANSACTION_SOURCES = ["CHAT", "MANUAL", "IMPORT", "BANK_SYNC", "API"]


class Transaction(Base):
    __tablename__ = "transactions"

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
    currency: Mapped[str] = mapped_column(String, nullable=False, default="INR", server_default="INR")
    category: Mapped[str] = mapped_column(String, nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="manual", server_default="manual")
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
    is_deleted: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    user = relationship("User", back_populates="transactions")

    __table_args__ = (
        Index("ix_transactions_user_id", "user_id"),
        Index("ix_transactions_is_deleted", "is_deleted"),
    )
