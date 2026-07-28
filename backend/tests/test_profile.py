"""
test_profile.py — Integration tests for user profile (User + DigitalTwin) endpoints.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from sqlalchemy import select
from app.models.user import User
from app.models.digital_twin import DigitalTwin
from app.models.audit_log import AuditLog
from app.core import security


@pytest.fixture
async def auth_user(db_session):
    """Seed a test user and return the user object + access token."""
    pw_hash = security.hash_password("password123")
    user = User(
        name="Profile Test User",
        email="profile_test@example.com",
        password_hash=pw_hash
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    
    token = security.create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_get_profile_requires_auth(client):
    """GET /users/me without Authorization header returns 401."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_success_lazy_twin(client, auth_user, db_session):
    """GET /users/me lazy-creates a DigitalTwin profile and returns correct data."""
    user, token = auth_user
    
    # Assert twin doesn't exist initially
    stmt_check = select(DigitalTwin).where(DigitalTwin.user_id == user.id)
    res_check = await db_session.execute(stmt_check)
    assert res_check.scalar_one_or_none() is None
    
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == user.id
    assert data["name"] == "Profile Test User"
    assert data["email"] == "profile_test@example.com"
    assert data["income_pattern"] is None
    assert data["risk_appetite"] is None
    assert data["onboarding_complete"] is False
    
    # Assert twin was lazy-created in database
    res_after = await db_session.execute(stmt_check)
    db_twin = res_after.scalar_one_or_none()
    assert db_twin is not None
    assert db_twin.user_id == user.id


@pytest.mark.asyncio
async def test_update_profile_success_and_audit(client, auth_user, db_session):
    """PATCH /users/me updates display name and twin fields and creates audit log."""
    user, token = auth_user
    
    payload = {
        "name": " Updated Name ",
        "income_pattern": "Salary: 50k",
        "risk_appetite": "moderate",
        "literacy_level": "intermediate",
        "language_preference": "Hindi"
    }
    
    response = client.patch(
        "/api/v1/users/me",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Verify fields updated (and name trimmed)
    assert data["name"] == "Updated Name"
    assert data["income_pattern"] == "Salary: 50k"
    assert data["risk_appetite"] == "moderate"
    assert data["literacy_level"] == "intermediate"
    assert data["language_preference"] == "Hindi"
    
    # Verify DB state directly
    stmt_user = select(User).where(User.id == user.id)
    res_user = await db_session.execute(stmt_user)
    assert res_user.scalar_one().name == "Updated Name"
    
    # Verify audit log entry was created
    stmt_audit = select(AuditLog).where(AuditLog.user_id == user.id)
    res_audit = await db_session.execute(stmt_audit)
    audit_entries = res_audit.scalars().all()
    assert len(audit_entries) == 1
    
    audit = audit_entries[0]
    assert audit.action == "profile_updated"
    assert audit.before["name"] == "Profile Test User"
    assert audit.after["name"] == "Updated Name"
    assert audit.after["income_pattern"] == "Salary: 50k"
