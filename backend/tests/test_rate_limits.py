"""
test_rate_limits.py — Tests for Phase 10 rate limiting on import upload and insights.

Mocks Redis to simulate rate limit enforcement.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


class TestImportUploadRateLimit:
    """Verify CSV upload endpoint is rate-limited."""

    @pytest.mark.asyncio
    @patch("app.core.rate_limit.get_redis_client")
    async def test_import_upload_blocked_after_limit(self, mock_redis_fn):
        """Upload endpoint returns 429 after exceeding RATE_LIMIT_IMPORT_UPLOAD."""
        mock_client = MagicMock()
        # Simulate counter already at limit + 1
        mock_client.incr.return_value = settings.RATE_LIMIT_IMPORT_UPLOAD + 1
        mock_redis_fn.return_value = mock_client

        from app.core.rate_limit import RateLimiter
        limiter = RateLimiter(
            "import_upload",
            settings.RATE_LIMIT_IMPORT_UPLOAD,
            settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
        )

        from fastapi import HTTPException
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        with pytest.raises(HTTPException) as exc_info:
            await limiter(mock_request)

        assert exc_info.value.status_code == 429


class TestRecommendationsRateLimit:
    """Verify recommendations endpoint is rate-limited."""

    @pytest.mark.asyncio
    @patch("app.core.rate_limit.get_redis_client")
    async def test_recommendations_blocked_after_limit(self, mock_redis_fn):
        """Recommendations limiter fires 429 when counter exceeds threshold."""
        mock_client = MagicMock()
        mock_client.incr.return_value = settings.RATE_LIMIT_INSIGHT_RECOMMENDATIONS + 1
        mock_redis_fn.return_value = mock_client

        from app.core.rate_limit import RateLimiter
        from fastapi import HTTPException

        limiter = RateLimiter(
            "insight_recommendations",
            settings.RATE_LIMIT_INSIGHT_RECOMMENDATIONS,
            settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
        )

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        with pytest.raises(HTTPException) as exc_info:
            await limiter(mock_request)

        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    @patch("app.core.rate_limit.get_redis_client")
    async def test_rate_limit_fails_open_on_redis_error(self, mock_redis_fn):
        """Rate limiter allows request when Redis raises an exception."""
        mock_client = MagicMock()
        mock_client.incr.side_effect = ConnectionError("Redis down")
        mock_redis_fn.return_value = mock_client

        from app.core.rate_limit import RateLimiter

        limiter = RateLimiter("test_endpoint", 5, 900)

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        # Should NOT raise — fails open
        result = await limiter(mock_request)
        assert result is None
