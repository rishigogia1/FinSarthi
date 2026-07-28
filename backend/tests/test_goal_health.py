"""
test_goal_health.py — Integration tests for goal progress analytics and health status classification labels.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from datetime import date, timedelta
from app.models.user import User
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed user and return token."""
    pw_hash = security.hash_password("password123")
    user = User(name="Goal Health User", email="gh@example.com", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    
    token = security.create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_empty_goals_state_safe(client, seed_users):
    """GET /insights/goal-health returns an empty list safely when user has no goals."""
    _, token = seed_users
    response = client.get("/api/v1/insights/goal-health", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_goal_health_deadline_labels(client, seed_users, db_session):
    """GET /insights/goal-health labels goal status appropriately based on timeline metrics."""
    user, token = seed_users

    # Goal 1: Already achieved -> on_track
    g1 = Goal(user_id=user.id, goal_name="Achieved Goal", target_amount=100.00, current_amount=100.00, status="active")
    # Goal 2: Deadline in past -> off_track
    g2 = Goal(user_id=user.id, goal_name="Past Goal", target_amount=500.00, current_amount=10.00, deadline=date.today() - timedelta(days=2), status="active")
    # Goal 3: No progress no deadline -> at_risk
    g3 = Goal(user_id=user.id, goal_name="No Progress Goal", target_amount=1000.00, current_amount=0.00, status="active")

    db_session.add_all([g1, g2, g3])
    await db_session.flush()
    await db_session.commit()

    response = client.get("/api/v1/insights/goal-health", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    goals_dict = {item["goal_name"]: item for item in data}
    assert goals_dict["Achieved Goal"]["status"] == "on_track"
    assert goals_dict["Past Goal"]["status"] == "off_track"
    assert goals_dict["No Progress Goal"]["status"] == "at_risk"
