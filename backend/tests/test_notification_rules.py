"""
test_notification_rules.py — Integration tests verifying reminder scheduler triggers.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from datetime import date, timedelta
from app.models.user import User
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.models.goal import Goal
from app.models.notification import Notification
from app.services.reminder_scheduler_service import ReminderSchedulerService
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed user and return token."""
    pw_hash = security.hash_password("password123")
    user = User(name="Notif User", email="notif@example.com", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    
    token = security.create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_scheduler_budget_limit_warning(client, seed_users, db_session):
    """Reminder scheduler generates a warning alert when budget exceeds 90%."""
    user, token = seed_users
    
    # 1. Create a budget
    b = Budget(
        user_id=user.id, category="Food", limit_amount=1000.00, period="monthly",
        start_date=date.today() - timedelta(days=2), end_date=date.today() + timedelta(days=28), active=True
    )
    # 2. Add an expense transaction that consumes 950 INR (95% usage)
    tx = Transaction(user_id=user.id, type="expense", amount=950.00, category="Food", occurred_on=date.today())
    db_session.add_all([b, tx])
    await db_session.flush()
    await db_session.commit()
    
    # 3. Trigger reminder check
    new_notifs_count = await ReminderSchedulerService.check_and_schedule_reminders(db_session, user_id=user.id)
    assert new_notifs_count == 1
    
    # 4. Fetch list of notifications via router
    response = client.get("/api/v1/notifications/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    feed = response.json()["notifications"]
    assert len(feed) == 1
    assert feed[0]["type"] == "budget_limit"
    assert "Food" in feed[0]["title"]
    assert feed[0]["read"] is False
    
    # Verify read/archive idempotency
    notif_id = feed[0]["id"]
    
    # Mark read
    r_read = client.patch(f"/api/v1/notifications/{notif_id}/read", headers={"Authorization": f"Bearer {token}"})
    assert r_read.status_code == 200
    assert r_read.json()["read"] is True
    
    # Mark archived
    r_arch = client.patch(f"/api/v1/notifications/{notif_id}/archive", headers={"Authorization": f"Bearer {token}"})
    assert r_arch.status_code == 200
    assert r_arch.json()["archived"] is True
    
    # List active feed without archived
    r_active = client.get("/api/v1/notifications/", headers={"Authorization": f"Bearer {token}"})
    assert len(r_active.json()["notifications"]) == 0
