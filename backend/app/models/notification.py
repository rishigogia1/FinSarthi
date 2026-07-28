"""
models/notification.py — User-scoped in-app notifications model.

ON DELETE CASCADE from users.
"""
from datetime import datetime
from sqlalchemy import ForeignKey, Index, String, text, TIMESTAMP, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class Notification(Base):
    __tablename__ = "notifications"

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
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # "budget_limit", "goal_due", "system", etc.
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    delivery_channel: Mapped[str] = mapped_column(String, nullable=False, default="in_app", server_default="in_app")
    delivered_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
    )
