"""
test_auth_guards.py — Test route-level authorization guards and `/me` endpoint.

Runs completely offline (mocks DB and AuthService resolve logic).
"""
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_db
from app.models.user import User
from app.services.auth_service import AuthService, InvalidCredentialsError, TokenExpiredError


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def guard_client(mock_db):
    """Client with overridden DB dependency returning a mock."""
    app.dependency_overrides[get_db] = lambda: mock_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_me_requires_auth(guard_client):
    """GET /me without Authorization header returns 401 Unauthorized."""
    response = guard_client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "detail" in response.json()


def test_me_valid_token(guard_client, mocker):
    """GET /me with valid access token resolves and returns the current user."""
    from datetime import datetime, timezone
    mock_user = User(
        id="user-uuid-1234",
        name="Authenticated User",
        email="auth_user@example.com",
        created_at=datetime.now(timezone.utc)
    )
    
    # Mock AuthService.get_current_user to return mock_user
    mocker.patch.object(AuthService, "get_current_user", return_value=mock_user)
    
    response = guard_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer valid_access_token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "user-uuid-1234"
    assert data["name"] == "Authenticated User"
    assert data["email"] == "auth_user@example.com"


def test_me_malformed_token(guard_client, mocker):
    """GET /me with malformed JWT returns 401."""
    mocker.patch.object(
        AuthService,
        "get_current_user",
        side_effect=InvalidCredentialsError("Invalid access token")
    )
    
    response = guard_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer malformed_token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "invalid_credentials"


def test_me_expired_token(guard_client, mocker):
    """GET /me with expired JWT returns 401 Token Expired."""
    mocker.patch.object(
        AuthService,
        "get_current_user",
        side_effect=TokenExpiredError("Token has expired")
    )
    
    response = guard_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer expired_token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "token_expired"


def test_me_wrong_token_type(guard_client, mocker):
    """GET /me using a refresh token fails with 401."""
    mocker.patch.object(
        AuthService,
        "get_current_user",
        side_effect=InvalidCredentialsError("Token is not an access token")
    )
    
    response = guard_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer raw_refresh_token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "invalid_credentials"


def test_refresh_endpoint_rejects_bearer_auth(guard_client):
    """Access tokens sent to /refresh in the request body fail validation (wrong body structure)."""
    # /refresh expects RefreshTokenRequest schema (JSON body with refresh_token string)
    response = guard_client.post(
        "/api/v1/auth/refresh",
        json={"access_token": "some_access_token"}  # field is refresh_token, so this is invalid
    )
    assert response.status_code == 422  # validation error
