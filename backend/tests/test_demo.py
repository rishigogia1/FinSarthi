"""
test_demo.py — Integration tests verifying demo resets, environment settings guards, and reseed limits.
"""
import pytest
from unittest.mock import patch
from app.models.user import User
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.audit_log import AuditLog
from app.core import security


@pytest.fixture
async def seed_demo_accounts(db_session):
    """Seed demo and unauthorized accounts."""
    pw_hash = security.hash_password("password123")
    
    demo_user = User(name="Demo User", email="demo@finsarthi.com", password_hash=pw_hash, role="user")
    regular_user = User(name="Reg User", email="reg@example.com", password_hash=pw_hash, role="user")
    admin_user = User(name="Admin User", email="admin@example.com", password_hash=pw_hash, role="admin")
    
    db_session.add_all([demo_user, regular_user, admin_user])
    await db_session.flush()
    await db_session.commit()

    demo_token = security.create_access_token(demo_user.id)
    reg_token = security.create_access_token(regular_user.id)
    admin_token = security.create_access_token(admin_user.id)
    return demo_user, demo_token, regular_user, reg_token, admin_user, admin_token


@pytest.mark.asyncio
async def test_demo_reset_regular_user_blocked(client, seed_demo_accounts):
    """A regular user is blocked from triggering the demo reset endpoint."""
    _, _, _, reg_token, _, _ = seed_demo_accounts

    response = client.post(
        "/api/v1/demo/reset",
        headers={"Authorization": f"Bearer {reg_token}"}
    )
    assert response.status_code == 403
    data = response.json()
    assert data["detail"]["error"]["code"] == "ACCESS_DENIED"


@pytest.mark.asyncio
async def test_demo_reset_settings_disabled(client, seed_demo_accounts):
    """If DEMO_MODE_ENABLED setting is False, the reset is blocked."""
    _, demo_token, _, _, _, _ = seed_demo_accounts

    with patch("app.services.demo_service.settings.DEMO_MODE_ENABLED", False):
        response = client.post(
            "/api/v1/demo/reset",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"]["code"] == "DEMO_MODE_DISABLED"


@pytest.mark.asyncio
async def test_demo_reset_production_blocked(client, seed_demo_accounts):
    """Resets are blocked in prod environments."""
    _, demo_token, _, _, _, _ = seed_demo_accounts

    with patch("app.services.demo_service.settings.ENVIRONMENT", "prod"):
        response = client.post(
            "/api/v1/demo/reset",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"]["code"] == "DEMO_MODE_DISABLED"


@pytest.mark.asyncio
async def test_demo_reset_allowed_and_reseeded(client, seed_demo_accounts, db_session):
    """Demo user is allowed to reset, cascading deletes existing records and seeds clean sets."""
    demo_user, demo_token, _, _, _, _ = seed_demo_accounts

    # 1. Seed some preliminary dirty records for this user
    tx = Transaction(user_id=demo_user.id, type="expense", amount=9999.00, category="Shopping", occurred_on=date.today())
    db_session.add(tx)
    await db_session.flush()
    await db_session.commit()

    # 2. Trigger demo reset
    response = client.post(
        "/api/v1/demo/reset",
        headers={"Authorization": f"Bearer {demo_token}"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    # 3. Assert dirty transactions are wiped and seeded template exists
    from sqlalchemy import select
    res_txs = await db_session.execute(select(Transaction).where(Transaction.user_id == demo_user.id))
    txs = res_txs.scalars().all()
    assert len(txs) == 12
    # Ensure dirty transaction with 9999.00 amount is wiped
    assert all(t.amount != 9999.00 for t in txs)

    # 4. Assert budgets and goals are seeded
    res_budgets = await db_session.execute(select(Budget).where(Budget.user_id == demo_user.id))
    assert len(res_budgets.scalars().all()) == 2

    res_goals = await db_session.execute(select(Goal).where(Goal.user_id == demo_user.id))
    assert len(res_goals.scalars().all()) == 1

    # 5. Assert audit log event demo.reset exists
    res_audit = await db_session.execute(select(AuditLog).where(AuditLog.user_id == demo_user.id, AuditLog.action == "demo.reset"))
    assert len(res_audit.scalars().all()) == 1
