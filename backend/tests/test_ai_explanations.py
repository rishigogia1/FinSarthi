"""
test_ai_explanations.py — Integration tests for AI-enriched descriptions and template fallbacks validation.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.insights import InsightResponse
from app.services.ai_explanation_service import AIExplanationService
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed user and return token."""
    pw_hash = security.hash_password("password123")
    user = User(name="AI Expl User", email="ai@example.com", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    
    token = security.create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_explanation_fallback_templates_direct(client):
    """Verify fallback templates are correctly formatted from structured evidence metrics."""
    insight_budget = InsightResponse(
        title="Budget Exceeded",
        message="You exceeded your budget limit.",
        type="budget_alert",
        severity="critical",
        confidence="high",
        evidence={"category": "Entertainment", "limit": 100.0, "actual": 120.0}
    )
    
    explanation = AIExplanationService.get_fallback_explanation(insight_budget)
    assert "Entertainment" in explanation
    assert "120" in explanation
    assert "100" in explanation
    
    insight_savings = InsightResponse(
        title="Healthy Savings",
        message="Good saving pattern.",
        type="savings_insight",
        severity="info",
        confidence="high",
        evidence={"savings_rate": 35.5}
    )
    exp_savings = AIExplanationService.get_fallback_explanation(insight_savings)
    assert "35.5%" in exp_savings


@pytest.mark.asyncio
async def test_highlights_endpoint_falls_back_gracefully(client, seed_users, db_session):
    """GET /insights/highlights executes and degrades gracefully to template descriptions when LLM fails."""
    user, token = seed_users

    # Add low transactions to trigger low history alert
    tx = Transaction(user_id=user.id, type="expense", amount=50.00, category="Groceries", occurred_on=date.today())
    db_session.add(tx)
    await db_session.flush()
    await db_session.commit()

    response = client.get("/api/v1/insights/highlights", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "insights" in data
    insights = data["insights"]
    assert len(insights) > 0
    # The message should match our fallback description since the live LLM client fails or is offline
    assert "personalized AI insights" in insights[0]["message"] or "personalized" in insights[0]["message"]
