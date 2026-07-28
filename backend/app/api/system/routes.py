"""
api/system/routes.py — Operational endpoints for health, readiness, version, and metrics.

These are the canonical system observability endpoints.
The legacy /health in main.py is kept for backward compatibility.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user
from app.core.metrics import metrics
from app.core.rate_limit import RateLimiter, get_redis_client
from app.models.user import User
from app.workers.reminder_worker import run_reminder_scan

logger = logging.getLogger("app.api.system")

router = APIRouter(prefix="/system", tags=["System & Operations"])

# Rate limiter: 5 manual reminder scans per 15 minutes per IP
reminder_scan_limiter = RateLimiter(
    "reminder_scan",
    settings.RATE_LIMIT_REMINDER_SCAN,
    settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
)


@router.get("/health")
async def system_health() -> dict:
    """
    Liveness probe. Returns 200 if the process is alive.
    Does NOT check external dependencies — use /ready for that.
    """
    return {"status": "ok"}


@router.get("/ready")
async def system_readiness(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    Readiness probe. Checks database and Redis connectivity.
    Returns 200 if all critical dependencies are reachable, 503 otherwise.

    LLM providers and email/push services are optional and do NOT
    affect readiness — their absence degrades features gracefully
    but does not prevent core operation.
    """
    checks: dict[str, str] = {}

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        logger.warning("Readiness: database check failed: %s", e)
        checks["database"] = "unavailable"

    # Redis check
    try:
        client = get_redis_client()
        if client and client.ping():
            checks["redis"] = "ok"
        else:
            checks["redis"] = "unavailable"
    except Exception as e:
        logger.warning("Readiness: Redis check failed: %s", e)
        checks["redis"] = "unavailable"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "ready": all_ok,
            "checks": checks,
        },
    )


@router.get("/version")
async def system_version() -> dict:
    """
    Build metadata. Values come from environment variables:
      APP_VERSION, BUILD_SHA, BUILD_DATE.
    Useful for deployment verification and incident triage.
    """
    return {
        "version": settings.APP_VERSION,
        "build_sha": settings.BUILD_SHA,
        "build_date": settings.BUILD_DATE or datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
    }


@router.get("/metrics")
async def system_metrics() -> dict:
    """
    V1 local in-process metrics snapshot.

    WARNING: These counters are local to the current process instance.
    They reset on restart and are NOT globally accurate across multiple
    instances. For production distributed metrics, integrate
    Prometheus client or OpenTelemetry exporters.
    """
    return metrics.snapshot()


@router.post(
    "/reminders/scan",
    dependencies=[Depends(reminder_scan_limiter)],
)
async def trigger_reminder_scan(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Manually trigger a reminder scan for the authenticated user.
    Runs as a lightweight post-response background task.
    Rate-limited to prevent abuse.
    """
    background_tasks.add_task(run_reminder_scan, current_user.id)
    return {"status": "scheduled", "message": "Reminder scan queued as background task."}
