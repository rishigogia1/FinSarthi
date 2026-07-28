"""
test_auth_rate_limit.py — Verify Redis-backed rate limiting on auth endpoints.

Runs completely offline by mocking the Redis client.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core import rate_limit


class MockRedis:
    """In-memory Redis mock for rate limit testing."""
    def __init__(self):
        self.store = {}

    def ping(self):
        return True

    def incr(self, key):
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    def expire(self, key, seconds):
        pass


@pytest.fixture
def mock_redis(mocker):
    """Fixture that replaces the real Redis client with MockRedis."""
    redis_instance = MockRedis()
    mocker.patch("app.core.rate_limit.get_redis_client", return_value=redis_instance)
    return redis_instance


@pytest.fixture
def rate_limit_client():
    # Clear overrides to use real endpoints (with rate limit dependencies active)
    app.dependency_overrides.clear()
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def test_rate_limit_login(rate_limit_client, mock_redis):
    """Repeated login attempts trigger a 429 Too Many Requests response."""
    # We mock AuthService.login to raise an error, but that comes AFTER rate limiting.
    # The rate limiter is hit first.
    # Limit for login is settings.AUTH_RATE_LIMIT_LOGIN = 5.
    
    # First 5 calls pass the rate limiter (though they might fail credentials inside route,
    # but let's see: we want to test rate limit triggers 429 on the 6th call).
    payload = {"email": "rate_limit_login@example.com", "password": "password123"}
    
    # We mock AuthService.login to prevent real database lookup
    with patch("app.services.auth_service.AuthService.login", side_effect=Exception("Dummy exception")):
        for i in range(5):
            response = rate_limit_client.post("/api/v1/auth/login", json=payload)
            # Response should be 500 (our mocked Exception) or anything other than 429
            assert response.status_code != 429
            
        # 6th call must be blocked by rate limiter with 429
        response = rate_limit_client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 429
        assert response.json()["detail"]["error"]["code"] == "too_many_requests"


def test_rate_limit_register(rate_limit_client, mock_redis):
    """Repeated registration attempts trigger a 429 Too Many Requests response."""
    # Limit for register is settings.AUTH_RATE_LIMIT_REGISTER = 10.
    payload = {"name": "Test User", "email": "rate_limit_reg@example.com", "password": "password123"}
    
    with patch("app.services.auth_service.AuthService.register", side_effect=Exception("Dummy exception")):
        for i in range(10):
            response = rate_limit_client.post("/api/v1/auth/register", json=payload)
            assert response.status_code != 429
            
        # 11th call must be blocked with 429
        response = rate_limit_client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 429
        assert response.json()["detail"]["error"]["code"] == "too_many_requests"


def test_rate_limit_refresh(rate_limit_client, mock_redis):
    """Repeated refresh attempts trigger a 429 rate limit."""
    # Limit for refresh is settings.AUTH_RATE_LIMIT_REFRESH = 20.
    payload = {"refresh_token": "some_refresh_token"}
    
    with patch("app.services.auth_service.AuthService.refresh", side_effect=Exception("Dummy exception")):
        for i in range(20):
            response = rate_limit_client.post("/api/v1/auth/refresh", json=payload)
            assert response.status_code != 429
            
        # 21st call must be blocked with 429
        response = rate_limit_client.post("/api/v1/auth/refresh", json=payload)
        assert response.status_code == 429
        assert response.json()["detail"]["error"]["code"] == "too_many_requests"
