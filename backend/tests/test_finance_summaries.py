"""
test_finance_summaries.py — Integration tests for finance summary overview and aggregations.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from datetime import date
from app.models.user import User
from app.models.transaction import Transaction
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed users for testing."""
    pw_hash = security.hash_password("password123")
    u1 = User(name="Summary User 1", email="u1_s@example.com", password_hash=pw_hash)
    u2 = User(name="Summary User 2", email="u2_s@example.com", password_hash=pw_hash)
    db_session.add(u1)
    db_session.add(u2)
    await db_session.flush()
    await db_session.commit()
    
    t1 = security.create_access_token(u1.id)
    t2 = security.create_access_token(u2.id)
    return (u1, t1), (u2, t2)


@pytest.mark.asyncio
async def test_summary_overview_computation(client, seed_users, db_session):
    """GET /finance/summary/overview computes correct total income, total expenses, and net cashflow."""
    (u1, t1), (u2, t2) = seed_users

    # User 1 transactions
    tx1 = Transaction(user_id=u1.id, type="income", amount=5000.00, category="Salary", occurred_on=date(2026, 7, 1))
    tx2 = Transaction(user_id=u1.id, type="expense", amount=1200.00, category="Rent", occurred_on=date(2026, 7, 5))
    tx3 = Transaction(user_id=u1.id, type="expense", amount=300.00, category="Food", occurred_on=date(2026, 7, 10))
    
    # User 2 transactions (should be isolated from User 1 summary)
    tx4 = Transaction(user_id=u2.id, type="income", amount=1000.00, category="Freelance", occurred_on=date(2026, 7, 2))

    db_session.add_all([tx1, tx2, tx3, tx4])
    await db_session.flush()
    await db_session.commit()

    # Query User 1 overview
    response = client.get("/api/v1/finance/summary/overview", headers={"Authorization": f"Bearer {t1}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_income"] == 5000.00
    assert data["total_expenses"] == 1500.00
    assert data["net_cashflow"] == 3500.00

    # Query User 2 overview
    r2 = client.get("/api/v1/finance/summary/overview", headers={"Authorization": f"Bearer {t2}"})
    assert r2.status_code == 200
    assert r2.json()["total_income"] == 1000.00
    assert r2.json()["total_expenses"] == 0.00


@pytest.mark.asyncio
async def test_summary_categories_breakdown(client, seed_users, db_session):
    """GET /finance/summary/categories totals and percentages are correct."""
    (u1, t1), _ = seed_users

    tx1 = Transaction(user_id=u1.id, type="expense", amount=600.00, category="Food", occurred_on=date(2026, 7, 1))
    tx2 = Transaction(user_id=u1.id, type="expense", amount=400.00, category="Food", occurred_on=date(2026, 7, 2))
    tx3 = Transaction(user_id=u1.id, type="expense", amount=1000.00, category="Rent", occurred_on=date(2026, 7, 3))

    db_session.add_all([tx1, tx2, tx3])
    await db_session.flush()
    await db_session.commit()

    response = client.get("/api/v1/finance/summary/categories", headers={"Authorization": f"Bearer {t1}"})
    assert response.status_code == 200
    data = response.json()
    
    # 2 categories: Food (1000 total, 50%), Rent (1000 total, 50%)
    assert len(data) == 2
    for item in data:
        assert item["total_amount"] == 1000.00
        assert item["percentage"] == 50.00


@pytest.mark.asyncio
async def test_summary_monthly_cashflow_rollup(client, seed_users, db_session):
    """GET /finance/summary/monthly-cashflow rolls up totals chronologically."""
    (u1, t1), _ = seed_users

    tx1 = Transaction(user_id=u1.id, type="income", amount=5000.00, category="Salary", occurred_on=date(2026, 6, 1))
    tx2 = Transaction(user_id=u1.id, type="expense", amount=1500.00, category="Rent", occurred_on=date(2026, 6, 15))
    tx3 = Transaction(user_id=u1.id, type="income", amount=6000.00, category="Salary", occurred_on=date(2026, 7, 1))

    db_session.add_all([tx1, tx2, tx3])
    await db_session.flush()
    await db_session.commit()

    response = client.get("/api/v1/finance/summary/monthly-cashflow", headers={"Authorization": f"Bearer {t1}"})
    assert response.status_code == 200
    data = response.json()
    
    # Chronological: June then July
    assert len(data) == 2
    
    assert data[0]["month"] == "2026-06"
    assert data[0]["income"] == 5000.00
    assert data[0]["expense"] == 1500.00
    assert data[0]["net"] == 3500.00

    assert data[1]["month"] == "2026-07"
    assert data[1]["income"] == 6000.00
    assert data[1]["expense"] == 0.00
    assert data[1]["net"] == 6000.00
