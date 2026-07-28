"""
models/goal.py — User financial goals.

ON DELETE CASCADE from users.
Indexed on user_id for fast per-user goal list queries.
"""
from datetime import date, datetime
from sqlalchemy import Date, ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class Goal(Base):
    __tablename__ = "goals"

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
    goal_name: Mapped[str] = mapped_column(String, nullable=False)
    target_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    current_amount: Mapped[float] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=0,
        server_default="0",
    )
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="active",
        server_default="active",
    )

    user = relationship("User", back_populates="goals")

    __table_args__ = (
        Index("ix_goals_user_id", "user_id"),
    )
