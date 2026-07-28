"""
core/middleware.py — Request lifecycle middleware for structured observability.

Generates a UUID request_id per request, attaches it to a ContextVar for
correlation across all log records, injects X-Request-ID into response headers,
and emits a structured access log line on completion.
"""
import logging
import time
import uuid
from contextvars import ContextVar
from starlette.types import ASGIApp, Scope, Receive, Send

logger = logging.getLogger("app.access")

# Context variable holding the current request's correlation ID.
# Accessible from any async code running within the same request context.
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

# Paths excluded from access logging to reduce noise.
_SILENT_PATHS = frozenset({"/health", "/api/v1/system/health", "/api/v1/system/ready"})


class RequestLoggingMiddleware:
    """
    Pure ASGI middleware that:
      1. Assigns a UUID request_id to every inbound HTTP request.
      2. Sets the ContextVar so downstream loggers automatically include it.
      3. Returns the request_id in the X-Request-ID response header.
      4. Emits a structured JSON access log line (unless the path is silenced).
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        rid = uuid.uuid4().hex
        request_id_ctx.set(rid)
        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", rid.encode("utf-8")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            path = scope.get("path", "")
            if path not in _SILENT_PATHS:
                logger.info(
                    "%s %s %s %.2fms",
                    scope.get("method", "GET"),
                    path,
                    status_code,
                    duration_ms,
                    extra={
                        "request_id": rid,
                        "method": scope.get("method", "GET"),
                        "path": path,
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                    },
                )
