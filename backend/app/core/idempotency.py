"""
core/idempotency.py — Job-state-based idempotency guard for destructive writes.

Instead of caching full HTTP response bodies, this checks the persisted state
of the resource (e.g., an import job) to determine if the operation has already
been completed. On duplicate requests, the current persisted state is returned
rather than re-executing the mutation.

Redis is used only to track which idempotency keys have been seen, preventing
race conditions during the short window between request receipt and DB commit.
Fails open if Redis is unavailable (logs warning, allows request).
"""
import logging
from fastapi import Request, HTTPException
from app.core.config import settings
from app.core.rate_limit import get_redis_client

logger = logging.getLogger("app.core.idempotency")

_IDEM_PREFIX = "idem"


def check_idempotency_key(request: Request) -> str | None:
    """
    Extract and validate the Idempotency-Key header from the request.
    Returns the key string if present, None otherwise.
    """
    key = request.headers.get("Idempotency-Key")
    if key and len(key) > 256:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "invalid_idempotency_key",
                    "message": "Idempotency-Key header must be 256 characters or fewer."
                }
            }
        )
    return key


def mark_idempotency_key_used(key: str, resource_id: str) -> bool:
    """
    Attempt to reserve an idempotency key in Redis using SET NX.

    Returns True if the key was newly set (first request).
    Returns False if the key already exists (duplicate request).
    Fails open (returns True) if Redis is unavailable.
    """
    client = get_redis_client()
    if client is None:
        logger.warning("Redis unavailable — idempotency check skipped (failing open)")
        return True

    redis_key = f"{_IDEM_PREFIX}:{key}"
    try:
        was_set = client.set(
            redis_key,
            resource_id,
            nx=True,
            ex=settings.IDEMPOTENCY_TTL_SECONDS,
        )
        return bool(was_set)
    except Exception as e:
        logger.error("Idempotency key SET failed (failing open): %s", e)
        return True


def get_idempotency_key_resource(key: str) -> str | None:
    """
    Retrieve the resource_id previously stored for an idempotency key.
    Returns None if Redis is unavailable or key does not exist.
    """
    client = get_redis_client()
    if client is None:
        return None

    redis_key = f"{_IDEM_PREFIX}:{key}"
    try:
        return client.get(redis_key)
    except Exception as e:
        logger.error("Idempotency key GET failed: %s", e)
        return None
