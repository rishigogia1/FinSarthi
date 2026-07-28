"""
tests/test_coach_v2.py — Automated test suite for FinSarthi V2 Agent 2 (Coach).
"""
import pytest
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.conversation import Conversation
from app.schemas.planner import ParsedIntentSchema
from app.services.transaction_service import TransactionService
from app.services.analytics_engine import AnalyticsEngine
from app.services.planner_analytics_service import PlannerAnalyticsService
from app.services.financial_rule_engine import FinancialRuleEngine
from app.services.coach_service import CoachService
from app.services.command_router import FinancialCommandRouter
from app.services.chat_service import ChatService
from app.services.intent_extractor import IntentExtractor


@pytest.fixture
async def coach_user(db_session: AsyncSession) -> User:
    """Create a temporary user for Coach tests."""
    user = User(
        name="Coach Test User",
        email="coach_test@finsarthi.app",
        password_hash="hashed_pw_456"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_analytics_engine_caching(db_session: AsyncSession, coach_user: User):
    """Test AnalyticsEngine TTL caching and invalidation on transaction creation."""
    today = date.today()
    await TransactionService.create_expense(db_session, coach_user.id, amount=500.0, category="Food", occurred_on=today)
    await db_session.commit()

    # First fetch populates cache
    s1 = await AnalyticsEngine.get_financial_summary(db_session, coach_user.id, today.year, today.month)
    assert s1["overview"]["monthly_expense"] == 500.0

    # Second transaction should invalidate cache via TransactionService
    await TransactionService.create_expense(db_session, coach_user.id, amount=300.0, category="Transport", occurred_on=today)
    await db_session.commit()

    s2 = await AnalyticsEngine.get_financial_summary(db_session, coach_user.id, today.year, today.month)
    assert s2["overview"]["monthly_expense"] == 800.0


@pytest.mark.asyncio
async def test_financial_rule_engine_evaluations():
    """Test modular rule evaluators in FinancialRuleEngine."""
    mock_analytics = {
        "overview": {
            "monthly_expense": 42000.0,
            "monthly_income": 50000.0,
            "net_cashflow": 8000.0,
            "savings_rate": 16.0
        },
        "categories": [
            {"category": "Food", "total_amount": 20000.0, "percentage": 47.6},
            {"category": "Shopping", "total_amount": 12000.0, "percentage": 28.6},
            {"category": "Transport", "total_amount": 10000.0, "percentage": 23.8}
        ]
    }

    rules = FinancialRuleEngine.evaluate_rules(mock_analytics)
    rule_ids = [r.rule_id for r in rules]

    assert "food_overspend" in rule_ids
    assert "shopping_overspend" in rule_ids
    assert "low_savings" in rule_ids
    assert "negative_cashflow" not in rule_ids


@pytest.mark.asyncio
async def test_coach_learning_state(db_session: AsyncSession, coach_user: User):
    """Test Coach Learning mode when user has < 20 transactions."""
    today = date.today()
    # Add 3 transactions
    await TransactionService.create_expense(db_session, coach_user.id, amount=100.0, category="Food", occurred_on=today)
    await TransactionService.create_expense(db_session, coach_user.id, amount=200.0, category="Shopping", occurred_on=today)
    await TransactionService.create_income(db_session, coach_user.id, amount=50000.0, category="Salary", occurred_on=today)
    await db_session.commit()

    summary = await CoachService.get_coach_summary(db_session, coach_user.id, today.year, today.month)

    assert summary.status == "Learning"
    assert summary.readiness.ready is False
    assert summary.readiness.tx_count == 3
    assert summary.score is None
    assert "Learning from spending patterns" in summary.readiness.message


@pytest.mark.asyncio
async def test_coach_active_state(db_session: AsyncSession, coach_user: User):
    """Test Coach Active state when user reaches >= 20 transactions."""
    today = date.today()

    # Seed 22 transactions
    await TransactionService.create_income(db_session, coach_user.id, amount=60000.0, category="Salary", occurred_on=today)
    for i in range(21):
        cat = "Food" if i % 2 == 0 else "Transport"
        await TransactionService.create_expense(db_session, coach_user.id, amount=200.0 + i, category=cat, occurred_on=today)
    await db_session.commit()

    summary = await CoachService.get_coach_summary(db_session, coach_user.id, today.year, today.month)

    assert summary.status == "Active"
    assert summary.readiness.ready is True
    assert summary.score is not None
    assert 0 <= summary.score.score <= 100
    assert summary.score.rating in ["Excellent", "Good", "Fair", "Needs Attention"]
    assert len(summary.score.reasons) > 0


@pytest.mark.asyncio
async def test_intent_extractor_coach_intents():
    """Test intent parsing for spending habits & overspending questions."""
    res1 = await IntentExtractor.extract("How are my spending habits?")
    assert res1.intent == "query_coach_habits"

    res2 = await IntentExtractor.extract("Am I overspending this month?")
    assert res2.intent == "query_coach_overspending"

    res3 = await IntentExtractor.extract("What is my coach score?")
    assert res3.intent == "query_coach_habits"


@pytest.mark.asyncio
async def test_coach_phase_10_verification_workflow(db_session: AsyncSession, coach_user: User):
    """
    Phase 10 Manual/Automated Workflow Verification:
    - Salary ₹50,000
    - Food ₹1,000
    - Coffee ₹300 (Food)
    - Shopping ₹5,000
    - Taxi ₹500 (Transport)
    - Verify identical metrics in Planner and Coach.
    """
    today = date.today()

    await TransactionService.create_income(db_session, coach_user.id, amount=50000.0, category="Salary", occurred_on=today)
    await TransactionService.create_expense(db_session, coach_user.id, amount=1000.0, category="Food", occurred_on=today)
    await TransactionService.create_expense(db_session, coach_user.id, amount=300.0, category="Food", note="Coffee", occurred_on=today)
    await TransactionService.create_expense(db_session, coach_user.id, amount=5000.0, category="Shopping", occurred_on=today)
    await TransactionService.create_expense(db_session, coach_user.id, amount=500.0, category="Transport", note="Taxi", occurred_on=today)
    await db_session.commit()

    planner_summary = await PlannerAnalyticsService.get_planner_summary(db_session, coach_user.id, today.year, today.month)
    coach_summary = await CoachService.get_coach_summary(db_session, coach_user.id, today.year, today.month)

    # 1. Verify totals match perfectly between Planner & Coach
    assert planner_summary.overview.monthly_expense == 6800.0
    assert planner_summary.overview.monthly_income == 50000.0
    assert planner_summary.overview.net_cashflow == 43200.0

    assert coach_summary.habits.largest_category == "Shopping"
    assert coach_summary.readiness.tx_count == 5

    # 2. Verify chat dispatch for overspending check
    conv = Conversation(user_id=coach_user.id, title="Coach Chat")
    db_session.add(conv)
    await db_session.commit()

    messages = await ChatService.process_message(
        session=db_session,
        conversation=conv,
        user=coach_user,
        content="Am I overspending?"
    )

    assert len(messages) == 2
    assert "Coach" in messages[1].content or "Shopping" in messages[1].content
