"""
test_idempotency.py — Tests for job-state-based idempotency guard.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.core.idempotency import (
    check_idempotency_key,
    mark_idempotency_key_used,
    get_idempotency_key_resource,
)
from fastapi import HTTPException


class TestIdempotencyKeyValidation:
    """Verify header extraction and validation."""

    def test_check_returns_none_when_absent(self):
        """No Idempotency-Key header returns None."""
        mock_request = MagicMock()
        mock_request.headers = {}
        result = check_idempotency_key(mock_request)
        assert result is None

    def test_check_returns_key_when_present(self):
        """Returns the header value when present."""
        mock_request = MagicMock()
        mock_request.headers = {"Idempotency-Key": "abc-123"}
        result = check_idempotency_key(mock_request)
        assert result == "abc-123"

    def test_check_rejects_oversized_key(self):
        """Rejects keys longer than 256 characters."""
        mock_request = MagicMock()
        mock_request.headers = {"Idempotency-Key": "x" * 257}
        with pytest.raises(HTTPException) as exc_info:
            check_idempotency_key(mock_request)
        assert exc_info.value.status_code == 400


class TestIdempotencyRedisOperations:
    """Verify Redis SET NX and GET behavior for idempotency."""

    @patch("app.core.idempotency.get_redis_client")
    def test_mark_key_new_returns_true(self, mock_get_client):
        """First use of a key returns True (new key)."""
        mock_client = MagicMock()
        mock_client.set.return_value = True
        mock_get_client.return_value = mock_client

        result = mark_idempotency_key_used("key-1", "job-abc")
        assert result is True
        mock_client.set.assert_called_once()

    @patch("app.core.idempotency.get_redis_client")
    def test_mark_key_duplicate_returns_false(self, mock_get_client):
        """Second use of a key returns False (duplicate)."""
        mock_client = MagicMock()
        mock_client.set.return_value = None  # NX fails -> key exists
        mock_get_client.return_value = mock_client

        result = mark_idempotency_key_used("key-1", "job-abc")
        assert result is False

    @patch("app.core.idempotency.get_redis_client")
    def test_mark_fails_open_when_redis_unavailable(self, mock_get_client):
        """Returns True (allows request) when Redis is down."""
        mock_get_client.return_value = None

        result = mark_idempotency_key_used("key-1", "job-abc")
        assert result is True

    @patch("app.core.idempotency.get_redis_client")
    def test_mark_fails_open_on_redis_error(self, mock_get_client):
        """Returns True (allows request) when Redis SET raises."""
        mock_client = MagicMock()
        mock_client.set.side_effect = ConnectionError("Redis error")
        mock_get_client.return_value = mock_client

        result = mark_idempotency_key_used("key-1", "job-abc")
        assert result is True

    @patch("app.core.idempotency.get_redis_client")
    def test_get_resource_returns_stored_value(self, mock_get_client):
        """Returns the resource_id stored for a key."""
        mock_client = MagicMock()
        mock_client.get.return_value = "job-xyz"
        mock_get_client.return_value = mock_client

        result = get_idempotency_key_resource("key-1")
        assert result == "job-xyz"

    @patch("app.core.idempotency.get_redis_client")
    def test_get_resource_returns_none_when_redis_down(self, mock_get_client):
        """Returns None when Redis is unavailable."""
        mock_get_client.return_value = None

        result = get_idempotency_key_resource("key-1")
        assert result is None
