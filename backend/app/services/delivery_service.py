"""
services/delivery_service.py — Delivery attempt logging and multi-channel fallbacks.

Handles emails and pushes channel redirects to in-app targets on configuration settings limits.
"""
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.notification import Notification

logger = logging.getLogger(__name__)


class DeliveryService:
    @staticmethod
    async def deliver_notification(
        session: AsyncSession,
        notification: Notification
    ) -> bool:
        """Process send attempts across active channels, adjusting to in_app fallbacks."""
        channel = notification.delivery_channel
        
        # Check channel capabilities
        if channel == "email" and not settings.EMAIL_NOTIFICATIONS_ENABLED:
            logger.info("Email alerts disabled. Redirecting notification %s to in-app channel.", notification.id)
            notification.delivery_channel = "in_app"
            notification.delivered_at = datetime.utcnow()
            await session.commit()
            return True
            
        if channel == "push" and not settings.PUSH_NOTIFICATIONS_ENABLED:
            logger.info("Push alerts disabled. Redirecting notification %s to in-app channel.", notification.id)
            notification.delivery_channel = "in_app"
            notification.delivered_at = datetime.utcnow()
            await session.commit()
            return True
            
        # Simulates successful delivery
        notification.delivered_at = datetime.utcnow()
        await session.commit()
        
        logger.info("Delivered notification %s successfully via channel %s.", notification.id, notification.delivery_channel)
        return True
