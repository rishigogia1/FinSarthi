"""
workers/reminder_worker.py — Post-response background task for reminder scanning.

Wraps ReminderSchedulerService inside its own database session so the
HTTP response is not blocked by budget/goal evaluation logic.

Not a durable worker: if the process restarts mid-scan, the work is lost.
Acceptable for V1 because reminder scans are cheap and re-runnable.
"""
import logging
from app.core.database import AsyncSessionLocal
from app.core.metrics import metrics

logger = logging.getLogger("app.workers.reminder")


async def run_reminder_scan(user_id: str) -> None:
    """
    Evaluate budget thresholds and goal deadlines for a single user,
    creating notification records for any triggered alerts.

    Designed to be called via:
        background_tasks.add_task(run_reminder_scan, user_id)
    """
    metrics.gauge_inc("active_background_jobs", {"job_type": "reminder_scan"})
    try:
        async with AsyncSessionLocal() as session:
            from app.services.reminder_scheduler_service import ReminderSchedulerService
            count = await ReminderSchedulerService.check_and_schedule_reminders(session, user_id)
            logger.info(
                "Reminder scan completed",
                extra={"user_id": user_id, "notifications_created": count},
            )
            metrics.inc("background_jobs_total", {"job_type": "reminder_scan", "outcome": "success"})
    except Exception:
        logger.exception("Reminder scan failed", extra={"user_id": user_id})
        metrics.inc("background_jobs_total", {"job_type": "reminder_scan", "outcome": "failure"})
    finally:
        metrics.gauge_dec("active_background_jobs", {"job_type": "reminder_scan"})
