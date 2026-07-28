"""
services/notification_service.py — Manage notification states, listing, and updates.

Handles in-app read/archive triggers.
"""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotificationService:
    @staticmethod
    async def create_notification(
        session: AsyncSession,
        user_id: str,
        title: str,
        message: str,
        type: str,
        delivery_channel: str = "in_app"
    ) -> Notification:
        """Create a new notification entry for the user."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            delivery_channel=delivery_channel,
            delivered_at=datetime.utcnow() if delivery_channel == "in_app" else None
        )
        session.add(notification)
        await session.flush()
        return notification

    @staticmethod
    async def list_notifications(
        session: AsyncSession,
        user_id: str,
        include_archived: bool = False
    ) -> list[Notification]:
        """List active notification items for the user."""
        stmt = select(Notification).where(Notification.user_id == user_id)
        if not include_archived:
            stmt = stmt.where(Notification.archived == False)
            
        stmt = stmt.order_by(Notification.created_at.desc())
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def mark_as_read(
        session: AsyncSession,
        user_id: str,
        notification_id: str
    ) -> Notification:
        """Mark notification as read (idempotent validation)."""
        stmt = select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        res = await session.execute(stmt)
        notification = res.scalar_one_or_none()
        if not notification:
            raise NotificationServiceError("NOTIFICATION_NOT_FOUND", "Notification not found or foreign-owned.", status_code=404)
            
        if not notification.read:
            notification.read = True
            await session.commit()
        return notification

    @staticmethod
    async def archive_notification(
        session: AsyncSession,
        user_id: str,
        notification_id: str
    ) -> Notification:
        """Mark notification as archived."""
        stmt = select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        res = await session.execute(stmt)
        notification = res.scalar_one_or_none()
        if not notification:
            raise NotificationServiceError("NOTIFICATION_NOT_FOUND", "Notification not found or foreign-owned.", status_code=404)
            
        if not notification.archived:
            notification.archived = True
            await session.commit()
        return notification
