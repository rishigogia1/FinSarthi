"""
test_insights.py — Integration tests for structured insights engine, rankings, and feedback collections.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from datetime import date
from sqlalchemy import select
from app.models.user import User
from app.models.audit_log import AuditLog
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed user and return token."""
    pw_hash = security.hash_password("password123")
    user = User(name="Insights User", email="ins@example.com", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    
    token = security.create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_recommendations_and_feedback_flow(client, seed_users, db_session):
    """GET /insights/recommendations list and POST /insights/feedback logs audit trial successfully."""
    user, token = seed_users

    # Verify recommendations list works
    r_rec = client.get("/api/v1/insights/recommendations", headers={"Authorization": f"Bearer {token}"})
    assert r_rec.status_code == 200
    recs = r_rec.json()["recommendations"]
    assert len(recs) > 0
    assert recs[0]["priority"] in ("high", "medium", "low")

    # Send feedback
    feedback_payload = {
        "insight_title": "Build Your Financial History",
        "feedback_score": 5,
        "comments": "Very helpful context information!"
    }
    r_fb = client.post(
        "/api/v1/insights/feedback",
        json=feedback_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_fb.status_code == 200
    assert r_fb.json() == {"success": True}

    # Verify feedback was logged inside AuditLog table
    stmt = select(AuditLog).where(
        AuditLog.user_id == user.id,
        AuditLog.action == "insight.feedback_logged"
    )
    res = await db_session.execute(stmt)
    audit = res.scalar_one_or_none()
    assert audit is not None
    assert audit.after["score"] == 5
    assert audit.after["insight_title"] == "Build Your Financial History"
