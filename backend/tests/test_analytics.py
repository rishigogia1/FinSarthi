"""
test_analytics.py — Integration tests for historical financial overview and budget health calculations.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from datetime import date, timedelta
from app.models.user import User
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed test user and return token."""
    pw_hash = security.hash_password("password123")
    user = User(name="Analytics User", email="anal@example.com", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    
    token = security.create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_overview_computation_zero_income_edge_case(client, seed_users, db_session):
    """GET /insights/overview behaves safely and avoids division by zero on zero income."""
    user, token = seed_users

    # Only expenses
    tx1 = Transaction(user_id=user.id, type="expense", amount=500.00, category="Food", occurred_on=date.today())
    db_session.add(tx1)
    await db_session.flush()
    await db_session.commit()

    response = client.get("/api/v1/insights/overview", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_income"] == 0.00
    assert data["total_expenses"] == 500.00
    assert data["net_savings"] == -500.00
    assert data["savings_rate"] == 0.00  # fallback handles division by zero safely


@pytest.mark.asyncio
async def test_overview_and_spending_trends_success(client, seed_users, db_session):
    """GET /insights/overview and spending-trends return accurate scoped totals."""
    user, token = seed_users

    tx1 = Transaction(user_id=user.id, type="income", amount=5000.00, category="Salary", occurred_on=date.today())
    tx2 = Transaction(user_id=user.id, type="expense", amount=1000.00, category="Rent", occurred_on=date.today())
    tx3 = Transaction(user_id=user.id, type="expense", amount=1000.00, category="Food", occurred_on=date.today())
    db_session.add_all([tx1, tx2, tx3])
    await db_session.flush()
    await db_session.commit()

    r_overview = client.get("/api/v1/insights/overview", headers={"Authorization": f"Bearer {token}"})
    assert r_overview.status_code == 200
    assert r_overview.json()["savings_rate"] == 60.00

    r_trends = client.get("/api/v1/insights/spending-trends", headers={"Authorization": f"Bearer {token}"})
    assert r_trends.status_code == 200
    trends = r_trends.json()["trends"]
    assert len(trends) == 2
    # Rent and Food should both have 50.00% share
    assert trends[0]["percentage"] == 50.00
    assert trends[1]["percentage"] == 50.00


@pytest.mark.asyncio
async def test_budget_health_calculations(client, seed_users, db_session):
    """GET /insights/budget-health reflects correct active budget utilization."""
    user, token = seed_users

    b = Budget(
        user_id=user.id, category="Food", limit_amount=1000.00, period="monthly",
        start_date=date.today() - timedelta(days=5), end_date=date.today() + timedelta(days=25), active=True
    )
    # Outside dates budget (should be ignored for actual spent matching)
    tx_inside = Transaction(user_id=user.id, type="expense", amount=950.00, category="Food", occurred_on=date.today())
    tx_outside = Transaction(user_id=user.id, type="expense", amount=100.00, category="Food", occurred_on=date.today() - timedelta(days=10))
    
    db_session.add_all([b, tx_inside, tx_outside])
    await db_session.flush()
    await db_session.commit()

    response = client.get("/api/v1/insights/budget-health", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "Food"
    assert data[0]["actual_spent"] == 950.00
    assert data[0]["usage_percentage"] == 95.00
    assert data[0]["status"] == "warning"  # used >= 90%
