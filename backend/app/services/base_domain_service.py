"""
services/base_domain_service.py — Abstract base class for domain services.

Provides infrastructure utilities (structured logging, performance timing,
and cache management primitives) for Planner, Coach, Guardian, Navigator, and Learn.
"""
import time
import logging
from typing import Any


class BaseDomainService:
    def __init__(self, service_name: str | None = None):
        name = service_name or self.__class__.__name__
        self.logger = logging.getLogger(f"app.services.{name.lower()}")

    def log_operation(self, operation: str, user_id: str, extra: dict[str, Any] | None = None) -> None:
        """Log a structured domain operation."""
        payload = {"user_id": user_id, "operation": operation}
        if extra:
            payload.update(extra)
        self.logger.info(f"[{self.__class__.__name__}] {operation} for user={user_id}", extra=payload)

    def log_error(self, operation: str, user_id: str, error: Exception) -> None:
        """Log a structured domain error."""
        self.logger.error(
            f"[{self.__class__.__name__}] Error during {operation} for user={user_id}: {error}",
            exc_info=True
        )

    def time_operation(self, operation: str, start_time: float) -> float:
        """Calculate and log duration of an operation."""
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        self.logger.debug(f"[{self.__class__.__name__}] {operation} took {elapsed_ms:.2f}ms")
        return elapsed_ms
