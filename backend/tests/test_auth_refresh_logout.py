"""
test_auth_refresh_logout.py — Integration tests for token refresh and logout.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update

from app.models.refresh_token import RefreshToken
from app.core import security
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_refresh_token_rotation(client, db_session):
    """POST /refresh rotates refresh token and invalidates the old one."""
    # Register & get initial token pair
    reg_payload = {
        "name": "Refresh User",
        "email": "refresh@example.com",
        "password": "password123"
    }
    r = client.post("/api/v1/auth/register", json=reg_payload)
    assert r.status_code == 201
    
    tokens = r.json()["tokens"]
    old_access = tokens["access_token"]
    old_refresh = tokens["refresh_token"]
    
    # 1. First refresh call should succeed and return new tokens
    refresh_payload = {"refresh_token": old_refresh}
    response = client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert response.status_code == 200
    
    new_tokens = response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["access_token"] != old_access
    assert new_tokens["refresh_token"] != old_refresh
    
    # 2. Re-using the old refresh token must be rejected
    dup_response = client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert dup_response.status_code == 401
    assert dup_response.json()["detail"]["error"]["code"] == "token_revoked"


@pytest.mark.asyncio
async def test_logout_revokes_token(client, db_session):
    """POST /logout revokes active refresh token; subsequent refresh fails."""
    # Register user
    reg_payload = {
        "name": "Logout User",
        "email": "logout@example.com",
        "password": "password123"
    }
    r = client.post("/api/v1/auth/register", json=reg_payload)
    tokens = r.json()["tokens"]
    refresh_token = tokens["refresh_token"]
    
    # Logout
    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token}
    )
    assert logout_response.status_code == 200
    assert logout_response.json()["success"] is True
    
    # Attempting to refresh with the logged out token must fail
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"]["error"]["code"] == "token_revoked"


@pytest.mark.asyncio
async def test_expired_token_rejected(client, db_session):
    """An expired refresh token is rejected during refresh."""
    # Register user
    reg_payload = {
        "name": "Expired User",
        "email": "expired@example.com",
        "password": "password123"
    }
    r = client.post("/api/v1/auth/register", json=reg_payload)
    tokens = r.json()["tokens"]
    refresh_token = tokens["refresh_token"]
    
    # Manually modify the expiration date in DB to be in the past
    hashed_token = security.hash_token(refresh_token)
    stmt = (
        update(RefreshToken)
        .where(RefreshToken.token_hash == hashed_token)
        .values(expires_at=datetime.now(timezone.utc) - timedelta(hours=1))
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    # Attempt refresh
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "token_expired"
