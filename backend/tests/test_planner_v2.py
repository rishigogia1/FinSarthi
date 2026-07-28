"""
tests/test_planner_v2.py — Automated test suite for FinSarthi V2 Agent 1 (Planner).
"""
import pytest
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.conversation import Conversation
from app.schemas.planner import TransactionCreateSchema, ParsedIntentSchema
from app.services.transaction_service import TransactionService, TransactionServiceError
from app.services.planner_analytics_service import PlannerAnalyticsService
from app.services.command_router import FinancialCommandRouter
from app.services.chat_service import ChatService
from app.services.intent_extractor import IntentExtractor


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a temporary user for Planner tests."""
    user = User(
        name="Planner Test User",
        email="planner_test@finsarthi.app",
        password_hash="hashed_pw_123"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_transaction_service_validation(db_session: AsyncSession, test_user: User):
    """Test domain validation in TransactionService."""
    from pydantic import ValidationError
    # Amount <= 0 must fail either schema validation or service validation
    with pytest.raises((TransactionServiceError, ValidationError)):
        await TransactionService.create_transaction(
            db_session,
            test_user.id,
            TransactionCreateSchema(type="expense", amount=-10.0, category="Food")
        )


@pytest.mark.asyncio
async def test_transaction_idempotency_check(db_session: AsyncSession, test_user: User):
    """Test that rapid duplicate transactions are suppressed by the idempotency guard."""
    schema = TransactionCreateSchema(
        type="expense",
        amount=500.0,
        category="Food",
        note="Lunch with team",
        occurred_on=date.today(),
        source="CHAT"
    )

    tx1, dup1 = await TransactionService.create_transaction(db_session, test_user.id, schema)
    await db_session.commit()
    assert dup1 is False

    # Second immediate submission of identical parameters
    tx2, dup2 = await TransactionService.create_transaction(db_session, test_user.id, schema)
    assert dup2 is True
    assert tx2.id == tx1.id


@pytest.mark.asyncio
async def test_planner_analytics_service(db_session: AsyncSession, test_user: User):
    """Test deterministic calculation of monthly totals, net cashflow, and top categories."""
    today = date.today()

    # Add 2 expenses & 1 income
    await TransactionService.create_expense(db_session, test_user.id, amount=2000.0, category="Food", occurred_on=today)
    await TransactionService.create_expense(db_session, test_user.id, amount=1500.0, category="Transport", occurred_on=today)
    await TransactionService.create_income(db_session, test_user.id, amount=50000.0, category="Salary", occurred_on=today)
    await db_session.commit()

    summary = await PlannerAnalyticsService.get_planner_summary(db_session, test_user.id, year=today.year, month=today.month)

    assert summary.overview.monthly_expense == 3500.0
    assert summary.overview.monthly_income == 50000.0
    assert summary.overview.net_cashflow == 46500.0
    assert summary.analytics.largest_category == "Food"
    assert summary.analytics.largest_category_amount == 2000.0
    assert summary.analytics.total_transactions == 3


@pytest.mark.asyncio
async def test_financial_command_router(db_session: AsyncSession, test_user: User):
    """Test FinancialCommandRouter dispatching and rich confirmation text formatting."""
    today = date.today()

    intent = ParsedIntentSchema(
        intent="add_expense",
        confidence=0.95,
        requires_confirmation=False,
        amount=1200.0,
        category="Bills",
        date=today,
        description="Electricity bill"
    )

    result = await FinancialCommandRouter.dispatch(db_session, test_user.id, intent)

    assert result["handled"] is True
    assert result["action"] == "add_expense"
    assert "recorded your expense" in result["message"]
    assert "₹1,200" in result["message"]
    assert result["summary"].overview.monthly_expense == 1200.0


@pytest.mark.asyncio
async def test_intent_extractor_regex_matching():
    """Test intent parsing rules."""
    res1 = await IntentExtractor.extract("I spent ₹2000 on food today")
    assert res1.intent == "add_expense"
    assert res1.amount == 2000.0
    assert res1.category == "Food"

    res2 = await IntentExtractor.extract("Salary credited 50000")
    assert res2.intent == "add_income"
    assert res2.amount == 50000.0

    res3 = await IntentExtractor.extract("How much have I spent this month?")
    assert res3.intent == "query_planner"


@pytest.mark.asyncio
async def test_semantic_category_mapping():
    """Test semantic normalization of user input keywords to categories."""
    coffee_res = await IntentExtractor.extract("I spent ₹500 on coffee")
    assert coffee_res.category == "Food"

    uber_res = await IntentExtractor.extract("Paid ₹350 for uber cab")
    assert uber_res.category == "Transport"

    amazon_res = await IntentExtractor.extract("Bought shirt on amazon for ₹1200")
    assert amazon_res.category == "Shopping"


@pytest.mark.asyncio
async def test_chat_pipeline_end_to_end(db_session: AsyncSession, test_user: User):
    """Test full end-to-end chat flow from user message to DB insertion and rich confirmation."""
    conv = Conversation(user_id=test_user.id, title="Financial Chat")
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    messages = await ChatService.process_message(
        session=db_session,
        conversation=conv,
        user=test_user,
        content="I spent ₹300 on petrol"
    )

    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
    assert "recorded your expense" in messages[1].content
    assert "Transport" in messages[1].content or "petrol" in messages[1].content.lower()
