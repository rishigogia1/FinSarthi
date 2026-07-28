"""
test_goals.py — Integration tests for financial goals CRUD operations and ownership checking.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from datetime import date, timedelta
from sqlalchemy import select
from app.models.user import User
from app.models.goal import Goal
from app.models.audit_log import AuditLog
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed two users for ownership testing."""
    pw_hash = security.hash_password("password123")
    u1 = User(name="Goal User 1", email="u1_goals@example.com", password_hash=pw_hash)
    u2 = User(name="Goal User 2", email="u2_goals@example.com", password_hash=pw_hash)
    db_session.add(u1)
    db_session.add(u2)
    await db_session.flush()
    await db_session.commit()
    
    t1 = security.create_access_token(u1.id)
    t2 = security.create_access_token(u2.id)
    return (u1, t1), (u2, t2)


@pytest.mark.asyncio
async def test_goal_create_success_and_audit(client, seed_users, db_session):
    """POST /users/me/goals creates a goal and writes a synchronous audit trail."""
    (u1, t1), _ = seed_users
    
    deadline_date = date.today() + timedelta(days=30)
    payload = {
        "goal_name": " Buy a House ",
        "target_amount": 120000.00,
        "current_amount": 5000.00,
        "deadline": str(deadline_date)
    }
    
    response = client.post(
        "/api/v1/users/me/goals",
        json=payload,
        headers={"Authorization": f"Bearer {t1}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["goal_name"] == "Buy a House"  # name trimmed
    assert data["target_amount"] == 120000.00
    assert data["current_amount"] == 5000.00
    assert data["status"] == "active"
    assert "id" in data
    
    # Assert persisted in DB
    stmt_check = select(Goal).where(Goal.id == data["id"])
    res_check = await db_session.execute(stmt_check)
    db_goal = res_check.scalar_one_or_none()
    assert db_goal is not None
    assert db_goal.user_id == u1.id
    
    # Assert audit log entry created
    stmt_audit = select(AuditLog).where(AuditLog.user_id == u1.id)
    res_audit = await db_session.execute(stmt_audit)
    audit = res_audit.scalar_one()
    assert audit.action == "goal_created"
    assert audit.before is None
    assert audit.after["goal_name"] == "Buy a House"


@pytest.mark.asyncio
async def test_goal_validation_rules(client, seed_users):
    """POST /users/me/goals enforces target > 0, current >= 0, and non-empty name."""
    _, (_, t2) = seed_users
    
    # Rejects empty name
    r1 = client.post(
        "/api/v1/users/me/goals",
        json={"goal_name": "  ", "target_amount": 100.0},
        headers={"Authorization": f"Bearer {t2}"}
    )
    assert r1.status_code == 422
    
    # Rejects negative target
    r2 = client.post(
        "/api/v1/users/me/goals",
        json={"goal_name": "Laptop", "target_amount": -50.0},
        headers={"Authorization": f"Bearer {t2}"}
    )
    assert r2.status_code == 422
    
    # Rejects past deadline
    past_date = date.today() - timedelta(days=5)
    r3 = client.post(
        "/api/v1/users/me/goals",
        json={"goal_name": "Laptop", "target_amount": 1000.0, "deadline": str(past_date)},
        headers={"Authorization": f"Bearer {t2}"}
    )
    assert r3.status_code == 422


@pytest.mark.asyncio
async def test_goal_list_ownership(client, seed_users, db_session):
    """GET /users/me/goals returns only owned goals."""
    (u1, t1), (u2, t2) = seed_users
    
    # Create goal for User 1
    g1 = Goal(user_id=u1.id, goal_name="Goal 1", target_amount=100.0, current_amount=0.0)
    db_session.add(g1)
    await db_session.flush()
    await db_session.commit()
    
    # List as User 2 (should be empty list)
    r2 = client.get(
        "/api/v1/users/me/goals",
        headers={"Authorization": f"Bearer {t2}"}
    )
    assert r2.status_code == 200
    assert len(r2.json()) == 0
    
    # List as User 1 (should return 1 goal)
    r1 = client.get(
        "/api/v1/users/me/goals",
        headers={"Authorization": f"Bearer {t1}"}
    )
    assert r1.status_code == 200
    assert len(r1.json()) == 1
    assert r1.json()[0]["id"] == g1.id


@pytest.mark.asyncio
async def test_goal_update_delete_ownership(client, seed_users, db_session):
    """Updating/deleting another user's goal is forbidden (returns 403 or 404)."""
    (u1, t1), (u2, t2) = seed_users
    
    # Create goal for User 1
    g1 = Goal(user_id=u1.id, goal_name="Goal 1", target_amount=100.0, current_amount=0.0)
    db_session.add(g1)
    await db_session.flush()
    await db_session.commit()
    
    # User 2 attempts to patch User 1's goal
    patch_res = client.patch(
        f"/api/v1/users/me/goals/{g1.id}",
        json={"goal_name": "Hacked name"},
        headers={"Authorization": f"Bearer {t2}"}
    )
    # Must fail with 403 (forbidden)
    assert patch_res.status_code == 403
    
    # User 2 attempts to delete User 1's goal
    del_res = client.delete(
        f"/api/v1/users/me/goals/{g1.id}",
        headers={"Authorization": f"Bearer {t2}"}
    )
    assert del_res.status_code == 403
    
    # Verify goal is NOT deleted from DB
    stmt_check = select(Goal).where(Goal.id == g1.id)
    res_check = await db_session.execute(stmt_check)
    assert res_check.scalar_one_or_none() is not None
    
    # User 1 deletes their own goal
    self_del_res = client.delete(
        f"/api/v1/users/me/goals/{g1.id}",
        headers={"Authorization": f"Bearer {t1}"}
    )
    assert self_del_res.status_code == 204
    
    # Verify goal IS gone from DB
    res_gone = await db_session.execute(stmt_check)
    assert res_gone.scalar_one_or_none() is None
