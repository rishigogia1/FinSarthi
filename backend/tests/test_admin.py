"""
test_admin.py — Integration tests verifying gated admin privilege routes.
"""
import pytest
from app.models.user import User
from app.core import security


@pytest.fixture
async def seed_accounts(db_session):
    """Seed user, admin, and return tokens."""
    pw_hash = security.hash_password("password123")
    
    regular_user = User(name="Regular User", email="reg@example.com", password_hash=pw_hash, role="user")
    admin_user = User(name="Admin User", email="admin@example.com", password_hash=pw_hash, role="admin")
    
    db_session.add_all([regular_user, admin_user])
    await db_session.flush()
    await db_session.commit()

    reg_token = security.create_access_token(regular_user.id)
    admin_token = security.create_access_token(admin_user.id)
    return regular_user, reg_token, admin_user, admin_token


@pytest.mark.asyncio
async def test_non_admin_blocked(client, seed_accounts):
    """Endpoints under /admin return HTTP 403 Forbidden for non-admin accounts."""
    _, reg_token, _, _ = seed_accounts

    endpoints = [
        "/api/v1/admin/users",
        "/api/v1/admin/audit-logs",
        "/api/v1/admin/system-summary"
    ]
    for url in endpoints:
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {reg_token}"}
        )
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"]["code"] == "ACCESS_DENIED"


@pytest.mark.asyncio
async def test_admin_allowed(client, seed_accounts):
    """Admin token accesses admin summaries, audit logs list, and system metrics successfully."""
    _, _, _, admin_token = seed_accounts

    # 1. GET /admin/users
    r_users = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r_users.status_code == 200
    data_users = r_users.json()
    assert len(data_users["users"]) >= 2
    # First user email is reg or admin
    emails = {u["email"] for u in data_users["users"]}
    assert "reg@example.com" in emails
    assert "admin@example.com" in emails

    # 2. GET /admin/audit-logs
    r_logs = client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r_logs.status_code == 200
    data_logs = r_logs.json()
    assert isinstance(data_logs["logs"], list)

    # 3. GET /admin/system-summary
    r_system = client.get(
        "/api/v1/admin/system-summary",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r_system.status_code == 200
    data_system = r_system.json()
    assert data_system["total_users"] >= 2
    assert "database_connected" in data_system
    assert "redis_connected" in data_system
