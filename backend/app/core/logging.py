"""
core/logging.py — Structured JSON logging with request_id correlation.

All log records are emitted as single-line JSON objects to stdout.
The RequestIdFilter automatically injects the current request's correlation ID
(from the ContextVar set by RequestLoggingMiddleware) into every record.

SECURITY RULE: raw secrets, passwords, JWT tokens, and connection strings
are redacted before output. All future phases must maintain this guarantee.
"""
import json
import logging
import sys
import re
from datetime import datetime, timezone
from typing import Any
from app.core.config import settings


class RequestIdFilter(logging.Filter):
    """
    Logging filter that injects `request_id` from the middleware ContextVar
    into every log record. Safe to call even when no request context exists
    (returns empty string).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id") or not record.request_id:
            # Lazy import to avoid circular dependency (middleware → logging → middleware)
            from app.core.middleware import request_id_ctx
            record.request_id = request_id_ctx.get("")  # type: ignore[attr-defined]
        return True


class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs log records as single-line JSON objects.
    Supports extra fields passthrough for structured service-level context
    (e.g. job_id, user_id, action).
    """

    # Fields that are standard LogRecord attributes and should NOT be treated as extras.
    _STANDARD_ATTRS = frozenset({
        "name", "msg", "args", "created", "relativeCreated", "exc_info",
        "exc_text", "stack_info", "lineno", "funcName", "pathname",
        "filename", "module", "thread", "threadName", "process",
        "processName", "levelname", "levelno", "message", "msecs",
        "taskName",
    })

    def format(self, record: logging.LogRecord) -> str:
        # Construct log payload
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Inject request_id if present
        request_id = getattr(record, "request_id", "")
        if request_id:
            log_data["request_id"] = request_id

        # Inject exception details if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Passthrough structured extra fields (e.g. job_id, user_id, duration_ms)
        for key, value in record.__dict__.items():
            if key not in self._STANDARD_ATTRS and key not in log_data and not key.startswith("_"):
                try:
                    json.dumps(value)  # ensure serializable
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)

        # Serialize to JSON string
        log_str = json.dumps(log_data)

        # Redact any sensitive information
        return self.redact_secrets(log_str)

    def redact_secrets(self, text: str) -> str:
        """
        HARD SECURITY RULE: Under no circumstances should raw secrets, passwords,
        JWT tokens, or raw connection strings be logged. All future development
        phases must adhere to this rule.
        """
        # Redact the explicit JWT Secret Key and LLM API Key values
        secrets_to_redact = []
        if settings.JWT_SECRET_KEY:
            secrets_to_redact.append(settings.JWT_SECRET_KEY)
        if settings.GEMINI_API_KEY:
            secrets_to_redact.append(settings.GEMINI_API_KEY)
        if settings.OPENAI_API_KEY:
            secrets_to_redact.append(settings.OPENAI_API_KEY)
        if settings.CLAUDE_API_KEY:
            secrets_to_redact.append(settings.CLAUDE_API_KEY)

        for secret in secrets_to_redact:
            if secret and len(secret) > 4 and secret != "changeme":
                text = text.replace(secret, "[REDACTED]")

        # Redact database credentials from DATABASE_URL
        # Pattern matches: protocol://user:password@host
        text = re.sub(
            r"(postgresql(?:\+asyncpg)?://[^:]+:)([^@]+)(@)",
            r"\1[REDACTED_PASSWORD]\3",
            text
        )
        
        # Redact redis credentials from REDIS_URL
        text = re.sub(
            r"(redis://[^:]+:)([^@]+)(@)",
            r"\1[REDACTED_PASSWORD]\3",
            text
        )

        # Generic fallback to redact full sensitive URL strings if they appear raw
        if settings.DATABASE_URL in text:
            text = text.replace(settings.DATABASE_URL, "[REDACTED_DATABASE_URL]")
        if settings.REDIS_URL in text:
            text = text.replace(settings.REDIS_URL, "[REDACTED_REDIS_URL]")

        return text

def setup_logging() -> None:
    """
    Configures structured logging for the application.
    Log levels are driven by settings.ENVIRONMENT (DEBUG in dev, INFO in prod/test).
    Attaches RequestIdFilter so all records carry request_id correlation.
    """
    log_level = logging.DEBUG if settings.ENVIRONMENT == "dev" else logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear pre-existing default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Establish stream handler writing JSON structured lines to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    handler.addFilter(RequestIdFilter())
    root_logger.addHandler(handler)

    # Restrain noise from uvicorn loggers in production
    if settings.ENVIRONMENT != "dev":
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
