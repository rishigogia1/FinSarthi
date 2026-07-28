"""
workers/delivery_worker.py — Post-response background task for notification delivery with retry.

Wraps DeliveryService.deliver_notification with exponential backoff retry logic.
Retries are in-process async sleeps — not durable across process restarts.
Acceptable for V1 because delivery is a simulated operation (no real SMTP/push).

Retry policy: up to DELIVERY_MAX_RETRIES attempts with exponential backoff
(base * 2^attempt seconds).
"""
import asyncio
import logging
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.metrics import metrics
from app.models.notification import Notification
from sqlalchemy import select

logger = logging.getLogger("app.workers.delivery")


async def run_delivery_with_retry(notification_id: str) -> None:
    """
    Attempt to deliver a notification with exponential backoff retries.

    Designed to be called via:
        background_tasks.add_task(run_delivery_with_retry, notification_id)
    """
    max_retries = settings.DELIVERY_MAX_RETRIES
    base_delay = settings.DELIVERY_RETRY_BASE_SECONDS

    metrics.gauge_inc("active_background_jobs", {"job_type": "delivery"})
    try:
        for attempt in range(1, max_retries + 1):
            try:
                async with AsyncSessionLocal() as session:
                    stmt = select(Notification).where(Notification.id == notification_id)
                    res = await session.execute(stmt)
                    notif = res.scalar_one_or_none()

                    if not notif:
                        logger.warning(
                            "Notification not found for delivery",
                            extra={"notification_id": notification_id},
                        )
                        metrics.inc("background_jobs_total", {"job_type": "delivery", "outcome": "not_found"})
                        return

                    if notif.delivered_at is not None:
                        logger.info(
                            "Notification already delivered, skipping",
                            extra={"notification_id": notification_id},
                        )
                        metrics.inc("background_jobs_total", {"job_type": "delivery", "outcome": "already_delivered"})
                        return

                    from app.services.delivery_service import DeliveryService
                    await DeliveryService.deliver_notification(session, notif)

                logger.info(
                    "Delivery succeeded",
                    extra={
                        "notification_id": notification_id,
                        "attempt": attempt,
                    },
                )
                metrics.inc("background_jobs_total", {"job_type": "delivery", "outcome": "success"})
                return

            except Exception:
                logger.warning(
                    "Delivery attempt failed",
                    extra={
                        "notification_id": notification_id,
                        "attempt": attempt,
                        "max_retries": max_retries,
                    },
                    exc_info=True,
                )
                if attempt < max_retries:
                    delay = base_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)

        # All retries exhausted
        logger.error(
            "Delivery failed after all retries",
            extra={
                "notification_id": notification_id,
                "max_retries": max_retries,
            },
        )
        metrics.inc("background_jobs_total", {"job_type": "delivery", "outcome": "failure"})

    finally:
        metrics.gauge_dec("active_background_jobs", {"job_type": "delivery"})
