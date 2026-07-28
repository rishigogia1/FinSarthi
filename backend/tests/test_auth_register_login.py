"""
test_auth_register_login.py — Integration tests for registration and login routes.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from sqlalchemy import select
from app.models.user import User


@pytest.mark.asyncio
async def test_register_success(client, db_session):
    """POST /register creates user in DB with hashed password and returns tokens."""
    payload = {
        "name": "Register Test User",
        "email": "REG_test@Example.Com",  # Mixed case to test normalization
        "password": "supersecretpassword123"
    }
    
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert "user" in data
    assert "tokens" in data
    
    # Assert user data returned
    user_res = data["user"]
    assert user_res["name"] == "Register Test User"
    assert user_res["email"] == "reg_test@example.com"  # normalized
    assert "id" in user_res
    
    # Assert tokens returned
    tokens_res = data["tokens"]
    assert "access_token" in tokens_res
    assert "refresh_token" in tokens_res
    assert tokens_res["token_type"] == "bearer"
    assert tokens_res["expires_in"] == 900
    
    # Verify DB persistence and password hashing
    result = await db_session.execute(
        select(User).where(User.id == user_res["id"])
    )
    db_user = result.scalar_one_or_none()
    assert db_user is not None
    assert db_user.name == "Register Test User"
    assert db_user.email == "reg_test@example.com"
    # Password must not be plaintext
    assert db_user.password_hash != "supersecretpassword123"
    # Hashing should start with standard bcrypt prefixes
    assert db_user.password_hash.startswith(("$2b$", "$2a$"))


@pytest.mark.asyncio
async def test_register_duplicate_email(client, db_session):
    """POST /register returns 409 Conflict if email is already taken."""
    payload = {
        "name": "User One",
        "email": "dup@example.com",
        "password": "password123"
    }
    
    # Register once
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201
    
    # Try registering again with same email (different case/spaces too)
    payload_dup = {
        "name": "User Two",
        "email": " DUP@example.com ",
        "password": "otherpassword"
    }
    r2 = client.post("/api/v1/auth/register", json=payload_dup)
    assert r2.status_code == 409
    
    data = r2.json()
    assert data["detail"]["error"]["code"] == "duplicate_email"


@pytest.mark.asyncio
async def test_login_success(client, db_session):
    """POST /login succeeds with correct credentials and returns token pair."""
    # Register a user first
    reg_payload = {
        "name": "Login Test User",
        "email": "login_test@example.com",
        "password": "correctpassword123"
    }
    client.post("/api/v1/auth/register", json=reg_payload)
    
    # Attempt login
    login_payload = {
        "email": "LOGIN_TEST@example.com",  # mixed case check
        "password": "correctpassword123"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "tokens" in data
    assert "user" in data
    assert data["user"]["email"] == "login_test@example.com"
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


@pytest.mark.asyncio
async def test_login_fails_wrong_password(client, db_session):
    """POST /login fails with 401 on incorrect password using generic message."""
    reg_payload = {
        "name": "Login Test User",
        "email": "login_test@example.com",
        "password": "correctpassword123"
    }
    client.post("/api/v1/auth/register", json=reg_payload)
    
    login_payload = {
        "email": "login_test@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    
    data = response.json()
    assert data["detail"]["error"]["code"] == "invalid_credentials"
    assert data["detail"]["error"]["message"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_fails_unknown_email(client, db_session):
    """POST /login fails with same generic 401 message for unknown email."""
    login_payload = {
        "email": "does_not_exist@example.com",
        "password": "some_password"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    
    data = response.json()
    # Wording must be identical to mitigate email enumeration attacks
    assert data["detail"]["error"]["code"] == "invalid_credentials"
    assert data["detail"]["error"]["message"] == "Invalid email or password"
