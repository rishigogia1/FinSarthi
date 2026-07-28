"""
core/rate_limit.py — Redis-backed rate limiting for auth endpoints.

Uses a fixed-window pattern: INCR + EXPIRE.
Fails open (logs a warning and allows the request) if Redis is unavailable
or if a Redis command fails, ensuring reliability.
"""
import logging
from redis import Redis
from fastapi import Request, HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client = None

def get_redis_client() -> Redis | None:
    """Lazy initialize and test the Redis client connection."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    
    try:
        # socket_connect_timeout prevents blocking startup/requests if Redis is down
        client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, decode_responses=True)
        client.ping()
        _redis_client = client
        return _redis_client
    except Exception as e:
        logger.warning("Redis not available at %s. Rate limiting will fail open. Error: %s", settings.REDIS_URL, e)
        return None

class RateLimiter:
    """FastAPI dependency for endpoint rate limiting."""
    def __init__(self, key_prefix: str, max_calls: int, window_seconds: int):
        self.key_prefix = key_prefix
        self.max_calls = max_calls
        self.window_seconds = window_seconds

    async def __call__(self, request: Request) -> None:
        client = get_redis_client()
        if client is None:
            return  # Fail open if Redis is down
        
        # Identify requester by IP address
        ip = request.client.host if request.client else "unknown"
        key = f"rl:{self.key_prefix}:{ip}"
        
        try:
            current_count = client.incr(key)
            if current_count == 1:
                client.expire(key, self.window_seconds)
            
            if current_count > self.max_calls:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": {
                            "code": "too_many_requests",
                            "message": "Too many requests. Please try again later."
                        }
                    }
                )
        except HTTPException:
            raise
        except Exception as e:
            # Fail open if any Redis command raises an exception
            logger.error("Rate limit check failed (failing open): %s", e)
            return
