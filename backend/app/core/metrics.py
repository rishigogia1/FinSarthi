"""
core/metrics.py — V1 local in-process observability counters.

NOTE: This is a lightweight, single-process metrics store for local development
and interview demos. Counters reset on process restart and are NOT accurate
across multiple application instances. For production distributed metrics,
replace with Prometheus client or OpenTelemetry exporters.

Thread-safe via threading.Lock. Exposed through GET /api/v1/system/metrics.
"""
import threading
from datetime import datetime, timezone
from typing import Any


class _MetricsStore:
    """In-process counter and gauge storage."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._started_at: str = datetime.now(timezone.utc).isoformat()

    # ---- Counters (monotonically increasing) ----

    def inc(self, name: str, labels: dict[str, str] | None = None, amount: int = 1) -> None:
        """Increment a counter by *amount*."""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + amount

    # ---- Gauges (point-in-time values) ----

    def gauge_set(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def gauge_inc(self, name: str, labels: dict[str, str] | None = None) -> None:
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = self._gauges.get(key, 0) + 1

    def gauge_dec(self, name: str, labels: dict[str, str] | None = None) -> None:
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = max(self._gauges.get(key, 0) - 1, 0)

    # ---- Snapshot ----

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-safe snapshot of all metrics."""
        with self._lock:
            return {
                "_info": "V1 local in-process metrics. Not distributed. Resets on restart.",
                "started_at": self._started_at,
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }

    # ---- Internal ----

    @staticmethod
    def _make_key(name: str, labels: dict[str, str] | None) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


# Singleton instance used across the application.
metrics = _MetricsStore()
