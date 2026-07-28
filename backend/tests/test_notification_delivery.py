"""
test_notification_delivery.py — Integration tests verifying channel fallback mechanisms.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from app.models.user import User
from app.models.notification import Notification
from app.services.delivery_service import DeliveryService
from app.services.notification_service import NotificationService
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed user and return token."""
    pw_hash = security.hash_password("password123")
    user = User(name="Delivery User", email="deliv@example.com", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    
    token = security.create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_delivery_channel_email_fallback(client, seed_users, db_session):
    """If email notification is disabled in config, delivery service falls back to in_app channel."""
    user, token = seed_users
    
    # Create notification with email channel
    notif = await NotificationService.create_notification(
        session=db_session,
        user_id=user.id,
        title="Email Alert Test",
        message="This is a test notification.",
        type="system",
        delivery_channel="email"
    )
    
    # Run delivery
    delivered = await DeliveryService.deliver_notification(db_session, notif)
    assert delivered is True
    
    # Refresh model state from DB
    await db_session.refresh(notif)
    # EMAIL_NOTIFICATIONS_ENABLED defaults to False -> channel must fallback to in_app
    assert notif.delivery_channel == "in_app"
    assert notif.delivered_at is not None
