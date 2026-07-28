"""
test_preferences.py — Integration tests for user preferences settings.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from sqlalchemy import select
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.audit_log import AuditLog
from app.core import security


@pytest.fixture
async def auth_user(db_session):
    pw_hash = security.hash_password("password123")
    user = User(
        name="Prefs Test User",
        email="prefs_test@example.com",
        password_hash=pw_hash
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    
    token = security.create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_get_preferences_lazy_default(client, auth_user, db_session):
    """GET /users/me/preferences returns light theme and notifications active by default."""
    user, token = auth_user
    
    # Assert no preferences row initially
    stmt_check = select(UserPreference).where(UserPreference.user_id == user.id)
    res_check = await db_session.execute(stmt_check)
    assert res_check.scalar_one_or_none() is None
    
    response = client.get(
        "/api/v1/users/me/preferences",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "light"
    assert data["notifications_enabled"] is True
    
    # Assert row was lazy-created
    res_after = await db_session.execute(stmt_check)
    db_pref = res_after.scalar_one_or_none()
    assert db_pref is not None
    assert db_pref.theme == "light"


@pytest.mark.asyncio
async def test_update_preferences_and_audit(client, auth_user, db_session):
    """PATCH /users/me/preferences updates settings and writes to audit log."""
    user, token = auth_user
    
    payload = {
        "theme": "dark",
        "notifications_enabled": False
    }
    
    response = client.patch(
        "/api/v1/users/me/preferences",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "dark"
    assert data["notifications_enabled"] is False
    
    # Verify DB state directly
    stmt_check = select(UserPreference).where(UserPreference.user_id == user.id)
    res_check = await db_session.execute(stmt_check)
    db_pref = res_check.scalar_one()
    assert db_pref.theme == "dark"
    assert db_pref.notifications_enabled is False
    
    # Verify audit log exists
    stmt_audit = select(AuditLog).where(AuditLog.user_id == user.id)
    res_audit = await db_session.execute(stmt_audit)
    audit = res_audit.scalar_one()
    assert audit.action == "preferences_updated"
    assert audit.before["theme"] == "light"
    assert audit.after["theme"] == "dark"


@pytest.mark.asyncio
async def test_update_preferences_invalid_theme(client, auth_user):
    """PATCH /users/me/preferences rejects invalid theme names with 422."""
    user, token = auth_user
    response = client.patch(
        "/api/v1/users/me/preferences",
        json={"theme": "blue"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
