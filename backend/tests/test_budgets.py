"""
test_budgets.py — Integration tests for category budgets, collision guards, and mutations logging.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from datetime import date, timedelta
from sqlalchemy import select
from app.models.user import User
from app.models.budget import Budget
from app.models.audit_log import AuditLog
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed users for testing."""
    pw_hash = security.hash_password("password123")
    u1 = User(name="Budget User 1", email="u1_b@example.com", password_hash=pw_hash)
    u2 = User(name="Budget User 2", email="u2_b@example.com", password_hash=pw_hash)
    db_session.add(u1)
    db_session.add(u2)
    await db_session.flush()
    await db_session.commit()
    
    t1 = security.create_access_token(u1.id)
    t2 = security.create_access_token(u2.id)
    return (u1, t1), (u2, t2)


@pytest.mark.asyncio
async def test_budget_create_success_and_audit(client, seed_users, db_session):
    """POST /finance/budgets creates a budget and logs the transaction."""
    (u1, t1), _ = seed_users

    payload = {
        "category": " Utilities ",
        "limit_amount": 5000.00,
        "period": "monthly",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=30))
    }

    response = client.post(
        "/api/v1/finance/budgets",
        json=payload,
        headers={"Authorization": f"Bearer {t1}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "Utilities"  # trimmed
    assert data["limit_amount"] == 5000.00
    assert data["active"] is True

    # Verify DB
    stmt = select(Budget).where(Budget.id == data["id"])
    res = await db_session.execute(stmt)
    db_b = res.scalar_one_or_none()
    assert db_b is not None
    assert db_b.user_id == u1.id

    # Verify audit log
    stmt_audit = select(AuditLog).where(AuditLog.user_id == u1.id)
    res_audit = await db_session.execute(stmt_audit)
    audit = res_audit.scalar_one()
    assert audit.action == "budget.created"


@pytest.mark.asyncio
async def test_budget_negative_amount_fails(client, seed_users):
    """POST /finance/budgets rejects zero or negative budget limits."""
    _, (_, t2) = seed_users

    payload = {
        "category": "Utilities",
        "limit_amount": -50.00,
        "period": "monthly",
        "start_date": str(date.today())
    }

    response = client.post(
        "/api/v1/finance/budgets",
        json=payload,
        headers={"Authorization": f"Bearer {t2}"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_budget_overlap_rule(client, seed_users, db_session):
    """Creating overlapping active budgets in same category/period yields a 400 error."""
    (u1, t1), _ = seed_users

    # Create active budget 1
    b1 = Budget(
        user_id=u1.id, category="Food", limit_amount=1000.00, period="monthly",
        start_date=date.today(), end_date=date.today() + timedelta(days=30), active=True
    )
    db_session.add(b1)
    await db_session.flush()
    await db_session.commit()

    # Attempt to create overlapping active budget in same category
    payload = {
        "category": "Food",
        "limit_amount": 1500.00,
        "period": "monthly",
        "start_date": str(date.today() + timedelta(days=15)),
        "end_date": str(date.today() + timedelta(days=45))
    }

    response = client.post(
        "/api/v1/finance/budgets",
        json=payload,
        headers={"Authorization": f"Bearer {t1}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "budget_overlap"


@pytest.mark.asyncio
async def test_budget_overlap_ignores_inactive(client, seed_users, db_session):
    """Budget overlap collision checker ignores inactive budgets."""
    (u1, t1), _ = seed_users

    # Create inactive budget 1
    b1 = Budget(
        user_id=u1.id, category="Rent", limit_amount=1000.00, period="monthly",
        start_date=date.today(), end_date=date.today() + timedelta(days=30), active=False
    )
    db_session.add(b1)
    await db_session.flush()
    await db_session.commit()

    # Create active budget in same category and timeframe
    payload = {
        "category": "Rent",
        "limit_amount": 1200.00,
        "period": "monthly",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=30))
    }

    response = client.post(
        "/api/v1/finance/budgets",
        json=payload,
        headers={"Authorization": f"Bearer {t1}"}
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_budget_ownership_guards(client, seed_users, db_session):
    """Editing/deleting a foreign budget returns 404."""
    (u1, t1), (u2, t2) = seed_users

    b = Budget(
        user_id=u1.id, category="Fun", limit_amount=300.00, period="monthly",
        start_date=date.today(), active=True
    )
    db_session.add(b)
    await db_session.flush()
    await db_session.commit()

    # User 2 update -> 404
    r_patch = client.patch(
        f"/api/v1/finance/budgets/{b.id}",
        json={"limit_amount": 400.00},
        headers={"Authorization": f"Bearer {t2}"}
    )
    assert r_patch.status_code == 404

    # User 2 delete -> 404
    r_del = client.delete(f"/api/v1/finance/budgets/{b.id}", headers={"Authorization": f"Bearer {t2}"})
    assert r_del.status_code == 404
