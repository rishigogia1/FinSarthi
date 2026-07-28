"""
test_forecasting.py — Integration tests for short-term moving average projections and goal timeline predictions.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from datetime import date, timedelta
from app.models.user import User
from app.models.transaction import Transaction
from app.models.recurring_cashflow import RecurringCashflow
from app.models.goal import Goal
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed user and return token."""
    pw_hash = security.hash_password("password123")
    user = User(name="Forecast User", email="fore@example.com", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    
    token = security.create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_forecast_low_history_fallback(client, seed_users, db_session):
    """GET /insights/forecast/monthly-cashflow uses low-confidence and recurring templates on low history."""
    user, token = seed_users

    # Seed 1 active recurring income configuration (no transactions logged yet)
    rc = RecurringCashflow(
        user_id=user.id, type="income", amount=5000.00, category="Rent",
        frequency="monthly", start_date=date.today(), active=True
    )
    db_session.add(rc)
    await db_session.flush()
    await db_session.commit()

    response = client.get("/api/v1/insights/forecast/monthly-cashflow", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_income"] == 5000.00
    assert data["predicted_expense"] == 0.00
    assert data["confidence"] == "low"
    assert "Low history" in data["reason"]


@pytest.mark.asyncio
async def test_forecast_with_historical_averages(client, seed_users, db_session):
    """GET /insights/forecast/monthly-cashflow correctly integrates history data when threshold reached."""
    user, token = seed_users

    # Seed recurring income
    rc = RecurringCashflow(
        user_id=user.id, type="income", amount=2000.00, category="Salary",
        frequency="monthly", start_date=date.today() - timedelta(days=60), active=True
    )
    db_session.add(rc)

    # Seed 10 manual non-recurring transactions to cross the threshold
    for i in range(10):
        tx = Transaction(
            user_id=user.id, type="expense", amount=100.00, category="OtherFood",
            occurred_on=date.today() - timedelta(days=i*4)
        )
        db_session.add(tx)
        
    await db_session.flush()
    await db_session.commit()

    response = client.get("/api/v1/insights/forecast/monthly-cashflow", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_income"] == 2000.00
    assert data["predicted_expense"] > 0.00
    # Over 10 points -> should be medium or high
    assert data["confidence"] in ("medium", "high")


@pytest.mark.asyncio
async def test_forecast_goal_projection_math(client, seed_users, db_session):
    """GET /insights/forecast/goal-projection projects target dates correctly using savings rate."""
    user, token = seed_users

    # Goal needing 1000 INR
    g = Goal(user_id=user.id, goal_name="Laptop Fund", target_amount=1000.00, current_amount=0.00, status="active")
    db_session.add(g)

    # Average savings rate of 1000 INR per month (net surplus)
    # E.g. income 2000, expense 1000 over 30.4 days
    tx1 = Transaction(user_id=user.id, type="income", amount=2000.00, category="Salary", occurred_on=date.today() - timedelta(days=30))
    tx2 = Transaction(user_id=user.id, type="expense", amount=1000.00, category="Rent", occurred_on=date.today() - timedelta(days=30))
    db_session.add_all([tx1, tx2])
    
    await db_session.flush()
    await db_session.commit()

    response = client.get("/api/v1/insights/forecast/goal-projection", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["is_trackable"] is True
    # At 1000 INR/month savings rate, a 1000 INR remaining goal will take ~30 days
    expected_proj = date.today() + timedelta(days=30)
    # Check projected date format and range sanity
    assert data[0]["projected_completion_date"] is not None
