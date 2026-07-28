"""
tests/test_copilot_v2.py — Integration tests for FinSarthi V2 AI Copilot multi-agent routing.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.conversation import Conversation
from app.services.chat_service import ChatService


@pytest.fixture
async def copilot_user(db_session: AsyncSession) -> User:
    """Create a temporary user for Copilot tests."""
    user = User(
        name="Copilot Test User",
        email="copilot_v2_test@finsarthi.app",
        password_hash="hashed_pw_123"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_copilot_v2_multi_agent_routing(db_session: AsyncSession, copilot_user: User):
    """Verifies agent routing for Planner, Coach, Guardian, Learn, Navigator, and command execution."""
    # 1. Create conversation
    conv = Conversation(user_id=copilot_user.id, title="New Conversation")
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    # 2. Expense Command Execution
    msgs1 = await ChatService.process_message(db_session, conv, copilot_user, "I spent ₹650 on fuel")
    assert len(msgs1) == 2
    assert "[📊 Planner]" in msgs1[1].content
    assert "₹650" in msgs1[1].content

    # 3. Planner Analytical Query
    msgs2 = await ChatService.process_message(db_session, conv, copilot_user, "How much have I spent this month?")
    assert "[📊 Planner]" in msgs2[-1].content
    assert "Planner" in msgs2[-1].content

    # 4. Coach Overspending Query
    msgs3 = await ChatService.process_message(db_session, conv, copilot_user, "Am I overspending?")
    assert "[🎯 Coach]" in msgs3[-1].content

    # 5. Guardian Fraud Safety Query
    msgs4 = await ChatService.process_message(db_session, conv, copilot_user, "Is this link safe: http://suspicious-upi-pay.com?")
    assert "[🛡️ Guardian]" in msgs4[-1].content
    assert "Guardian" in msgs4[-1].content

    # 6. Learn Financial Literacy Query
    msgs5 = await ChatService.process_message(db_session, conv, copilot_user, "Explain SIP and Mutual Funds")
    assert "[💡 Learn]" in msgs5[-1].content
    assert "SIP" in msgs5[-1].content

    # 7. Navigator Purchase Affordability Query
    msgs6 = await ChatService.process_message(db_session, conv, copilot_user, "Can I afford a ₹1.8 lakh bike?")
    assert "[🧭 Navigator]" in msgs6[-1].content
    assert "Navigator" in msgs6[-1].content

    # 8. Verify Deterministic Title Generation
    await db_session.refresh(conv)
    assert conv.title == "Monthly Budget & Spending Review"
