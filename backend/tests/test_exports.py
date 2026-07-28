"""
test_exports.py — Integration tests verifying CSV export generation and download.
"""
import pytest
from app.models.user import User
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.audit_log import AuditLog
from app.core import security
from datetime import date


@pytest.fixture
async def seed_users(db_session):
    """Seed user and return token."""
    pw_hash = security.hash_password("password123")
    user = User(name="Export User", email="exp@example.com", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()

    token = security.create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_export_transactions_csv(client, seed_users, db_session):
    """GET /exports/transactions returns CSV FileResponse download and writes audit log."""
    user, token = seed_users

    # Seed a transaction
    tx = Transaction(user_id=user.id, type="expense", amount=120.00, category="Food", occurred_on=date.today())
    db_session.add(tx)
    await db_session.flush()
    await db_session.commit()

    response = client.get(
        "/api/v1/exports/transactions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    
    content = response.text
    assert "Date,Type,Amount,Category,Note,Source" in content
    assert "Food" in content
    assert "120.0" in content

    # Verify audit log
    from sqlalchemy import select
    stmt = select(AuditLog).where(AuditLog.user_id == user.id, AuditLog.action == "export.transactions")
    res = await db_session.execute(stmt)
    logs = res.scalars().all()
    assert len(logs) == 1
    assert "export_" in logs[0].after["filename"]


@pytest.mark.asyncio
async def test_export_budgets_csv(client, seed_users, db_session):
    """GET /exports/budgets returns CSV budgets FileResponse."""
    user, token = seed_users

    b = Budget(user_id=user.id, category="Utilities", limit_amount=3000.00, period="monthly", start_date=date.today(), end_date=date.today(), active=True)
    db_session.add(b)
    await db_session.flush()
    await db_session.commit()

    response = client.get(
        "/api/v1/exports/budgets",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    content = response.text
    assert "Category,Limit Amount,Period,Start Date,End Date,Active" in content
    assert "Utilities" in content


@pytest.mark.asyncio
async def test_export_goals_csv(client, seed_users, db_session):
    """GET /exports/goals returns CSV goals FileResponse."""
    user, token = seed_users

    g = Goal(user_id=user.id, goal_name="Home Fund", target_amount=50000.00, current_amount=100.00)
    db_session.add(g)
    await db_session.flush()
    await db_session.commit()

    response = client.get(
        "/api/v1/exports/goals",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    content = response.text
    assert "Goal Name,Target Amount,Current Amount,Deadline,Status" in content
    assert "Home Fund" in content
