"""
test_recurring_cashflows.py — Integration tests for recurring cashflow endpoints and validation guards.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from datetime import date, timedelta
from sqlalchemy import select
from app.models.user import User
from app.models.recurring_cashflow import RecurringCashflow
from app.models.audit_log import AuditLog
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed users for testing."""
    pw_hash = security.hash_password("password123")
    u1 = User(name="Rec User 1", email="u1_rec@example.com", password_hash=pw_hash)
    u2 = User(name="Rec User 2", email="u2_rec@example.com", password_hash=pw_hash)
    db_session.add(u1)
    db_session.add(u2)
    await db_session.flush()
    await db_session.commit()
    
    t1 = security.create_access_token(u1.id)
    t2 = security.create_access_token(u2.id)
    return (u1, t1), (u2, t2)


@pytest.mark.asyncio
async def test_recurring_create_success_and_audit(client, seed_users, db_session):
    """POST /finance/recurring creates a cashflow configuration and logs it."""
    (u1, t1), _ = seed_users

    payload = {
        "type": "income",
        "amount": 25000.00,
        "category": "Salary",
        "frequency": "monthly",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=180)),
        "note": "Company monthly paycheck"
    }

    response = client.post(
        "/api/v1/finance/recurring",
        json=payload,
        headers={"Authorization": f"Bearer {t1}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 25000.00
    assert data["active"] is True
    assert data["frequency"] == "monthly"

    # Verify DB
    stmt = select(RecurringCashflow).where(RecurringCashflow.id == data["id"])
    res = await db_session.execute(stmt)
    db_rc = res.scalar_one_or_none()
    assert db_rc is not None
    assert db_rc.user_id == u1.id

    # Verify Audit log
    stmt_audit = select(AuditLog).where(AuditLog.user_id == u1.id)
    res_audit = await db_session.execute(stmt_audit)
    audit = res_audit.scalar_one()
    assert audit.action == "recurring_cashflow.created"


@pytest.mark.asyncio
async def test_recurring_date_validation_gate(client, seed_users):
    """POST /finance/recurring rejects end_date preceding start_date."""
    _, (_, t2) = seed_users

    payload = {
        "type": "expense",
        "amount": 1000.00,
        "category": "Gym",
        "frequency": "monthly",
        "start_date": str(date.today()),
        "end_date": str(date.today() - timedelta(days=1))
    }

    response = client.post(
        "/api/v1/finance/recurring",
        json=payload,
        headers={"Authorization": f"Bearer {t2}"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_recurring_ownership_guards(client, seed_users, db_session):
    """Foreign-owned recurring configs cannot be edited or deleted (returns 404)."""
    (u1, t1), (u2, t2) = seed_users

    rc = RecurringCashflow(
        user_id=u1.id, type="expense", amount=100.00, category="Netflix",
        frequency="monthly", start_date=date.today(), active=True
    )
    db_session.add(rc)
    await db_session.flush()
    await db_session.commit()

    # User 2 patch -> 404
    r_patch = client.patch(
        f"/api/v1/finance/recurring/{rc.id}",
        json={"active": False},
        headers={"Authorization": f"Bearer {t2}"}
    )
    assert r_patch.status_code == 404

    # User 2 delete -> 404
    r_del = client.delete(f"/api/v1/finance/recurring/{rc.id}", headers={"Authorization": f"Bearer {t2}"})
    assert r_del.status_code == 404


@pytest.mark.asyncio
async def test_recurring_list_includes_inactive(client, seed_users, db_session):
    """GET /finance/recurring includes both active and inactive entries in user results."""
    (u1, t1), _ = seed_users

    rc1 = RecurringCashflow(
        user_id=u1.id, type="expense", amount=10.00, category="Active",
        frequency="weekly", start_date=date.today(), active=True
    )
    rc2 = RecurringCashflow(
        user_id=u1.id, type="expense", amount=20.00, category="Inactive",
        frequency="monthly", start_date=date.today(), active=False
    )
    db_session.add(rc1)
    db_session.add(rc2)
    await db_session.flush()
    await db_session.commit()

    response = client.get("/api/v1/finance/recurring", headers={"Authorization": f"Bearer {t1}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    categories = [item["category"] for item in data]
    assert "Active" in categories
    assert "Inactive" in categories
