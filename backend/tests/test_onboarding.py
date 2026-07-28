"""
test_onboarding.py — Integration tests verifying onboarding status and complete endpoints.
"""
import pytest
from app.models.user import User
from app.models.audit_log import AuditLog
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed user and return token."""
    pw_hash = security.hash_password("password123")
    user = User(name="Onboard User", email="onb@example.com", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()

    token = security.create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_get_onboarding_status_default(client, seed_users):
    """GET /onboarding/status returns all steps incomplete initially."""
    _, token = seed_users

    response = client.get(
        "/api/v1/onboarding/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["onboarding_completed"] is False
    assert len(data["steps"]) == 4
    assert data["steps"][0]["completed"] is False  # add_transaction
    assert data["steps"][1]["completed"] is False  # upload_csv
    assert data["steps"][2]["completed"] is False  # configure_budget


@pytest.mark.asyncio
async def test_complete_onboarding_mutation(client, seed_users, db_session):
    """POST /onboarding/complete flags onboarding as completed and logs audit log entry."""
    user, token = seed_users

    payload = {"completed": True}
    response = client.post(
        "/api/v1/onboarding/complete",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["onboarding_completed"] is True
    assert data["steps"][3]["completed"] is True  # check_insights

    # Verify audit log entry was written
    from sqlalchemy import select
    stmt = select(AuditLog).where(AuditLog.user_id == user.id, AuditLog.action == "user.onboarding_completed")
    res = await db_session.execute(stmt)
    logs = res.scalars().all()
    assert len(logs) == 1
    assert logs[0].after["onboarding_completed"] is True
