"""
test_background_jobs.py — Unit tests for worker retry logic and metrics counter increments.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.core.metrics import metrics


class TestDeliveryWorkerRetry:
    """Verify delivery worker exponential backoff retry logic."""

    @pytest.mark.asyncio
    @patch("app.workers.delivery_worker.AsyncSessionLocal")
    async def test_delivery_retries_on_failure(self, mock_session_factory):
        """Worker retries up to DELIVERY_MAX_RETRIES times on failure."""
        from app.workers.delivery_worker import run_delivery_with_retry

        # Make session context manager raise on each attempt
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(side_effect=Exception("DB error"))
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = mock_session

        # Patch asyncio.sleep to avoid real delays
        with patch("app.workers.delivery_worker.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await run_delivery_with_retry("fake-notification-id")

            # Should sleep between retries (max_retries - 1 sleeps)
            # Default DELIVERY_MAX_RETRIES = 3, so 2 sleeps
            assert mock_sleep.call_count == 2


class TestReminderWorker:
    """Verify reminder worker metrics tracking."""

    @pytest.mark.asyncio
    @patch("app.workers.reminder_worker.AsyncSessionLocal")
    @patch("app.services.reminder_scheduler_service.ReminderSchedulerService")
    async def test_reminder_scan_increments_metrics(self, mock_scheduler, mock_session_factory):
        """Successful reminder scan increments success counter."""
        from app.workers.reminder_worker import run_reminder_scan

        # Setup mock session
        mock_session = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = mock_session_ctx

        mock_scheduler.check_and_schedule_reminders = AsyncMock(return_value=2)

        # Take snapshot before
        before = metrics.snapshot()
        success_key = "background_jobs_total{job_type=reminder_scan,outcome=success}"
        count_before = before["counters"].get(success_key, 0)

        await run_reminder_scan("user-123")

        after = metrics.snapshot()
        count_after = after["counters"].get(success_key, 0)
        assert count_after == count_before + 1


class TestMetricsStore:
    """Verify in-process metrics store behavior."""

    def test_counter_increment(self):
        """Counter increments correctly with labels."""
        metrics.inc("test_counter", {"action": "test"})
        snap = metrics.snapshot()
        key = "test_counter{action=test}"
        assert snap["counters"][key] >= 1

    def test_gauge_set_and_dec(self):
        """Gauge tracks point-in-time values."""
        metrics.gauge_set("test_gauge", 5.0, {"scope": "unit"})
        snap = metrics.snapshot()
        assert snap["gauges"]["test_gauge{scope=unit}"] == 5.0

        metrics.gauge_dec("test_gauge", {"scope": "unit"})
        snap2 = metrics.snapshot()
        assert snap2["gauges"]["test_gauge{scope=unit}"] == 4.0

    def test_gauge_dec_floors_at_zero(self):
        """Gauge does not go below zero."""
        metrics.gauge_set("floor_gauge", 0.0)
        metrics.gauge_dec("floor_gauge")
        snap = metrics.snapshot()
        assert snap["gauges"]["floor_gauge"] == 0

    def test_snapshot_includes_info_label(self):
        """Snapshot includes V1 local-only warning."""
        snap = metrics.snapshot()
        assert "V1 local" in snap["_info"]
        assert "started_at" in snap
