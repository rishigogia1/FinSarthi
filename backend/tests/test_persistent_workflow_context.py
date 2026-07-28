"""
tests/test_persistent_workflow_context.py — Integration tests for FinSarthi V2 Persistent Workflow Context & Agent Isolation.

Verifies:
1. Multi-turn persona isolation for Learn, Guardian, Navigator, Coach workflows.
2. Suppression of unsolicited generic spending snapshot cards in specialized workflows.
3. Cross-agent priority override (logging expense via Planner) and seamless return to primary workflow agent.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.services.workflows.workflow_launcher import WorkflowLauncher
from app.services.chat_service import ChatService


@pytest.fixture
async def workflow_user(db_session: AsyncSession) -> User:
    """Create temporary user for Workflow Context tests."""
    user = User(
        name="Workflow Test User",
        email="context_test_user@finsarthi.app",
        password_hash="hashed_pw_123"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_learn_finance_multi_turn_persona_isolation(db_session, workflow_user):
    """Verify learn_finance maintains 💡 Learn persona across multiple turns."""
    conv, messages, chips = await WorkflowLauncher.launch(
        db_session=db_session,
        user=workflow_user,
        workflow_id="learn_finance"
    )

    assert conv.primary_agent.lower() == "learn"
    assert "💡 Learn" in messages[-1].content

    # Turn 2: Ask follow-up question about mutual funds
    turn2_messages = await ChatService.process_message(
        session=db_session,
        conversation=conv,
        user=workflow_user,
        content="What is a Mutual Fund and how does it differ from a fixed deposit?"
    )

    assistant_turn2 = turn2_messages[-1].content
    assert "[💡 Learn]" in assistant_turn2
    # Ensure no generic monthly spend dump
    assert "Monthly Spend:" not in assistant_turn2


@pytest.mark.asyncio
async def test_fraud_protection_multi_turn_persona_isolation(db_session, workflow_user):
    """Verify fraud_protection maintains 🛡️ Guardian persona across turns."""
    conv, messages, chips = await WorkflowLauncher.launch(
        db_session=db_session,
        user=workflow_user,
        workflow_id="fraud_protection"
    )

    assert conv.primary_agent.lower() == "guardian"
    assert "🛡️ Guardian" in messages[-1].content

    # Turn 2: Provide suspicious link
    turn2_messages = await ChatService.process_message(
        session=db_session,
        conversation=conv,
        user=workflow_user,
        content="Is http://bit.ly/free-reward-claim safe to click?"
    )

    assistant_turn2 = turn2_messages[-1].content
    assert "[🛡️ Guardian]" in assistant_turn2
    assert "Phishing Risk" in assistant_turn2 or "Guardian" in assistant_turn2
    assert "Monthly Spend:" not in assistant_turn2


@pytest.mark.asyncio
async def test_government_schemes_multi_turn_persona_isolation(db_session, workflow_user):
    """Verify government_schemes maintains 🧭 Navigator persona across turns."""
    conv, messages, chips = await WorkflowLauncher.launch(
        db_session=db_session,
        user=workflow_user,
        workflow_id="government_schemes"
    )

    assert conv.primary_agent.lower() == "navigator"
    assert "🧭 Navigator" in messages[-1].content

    # Turn 2: Query schemes for senior citizens
    turn2_messages = await ChatService.process_message(
        session=db_session,
        conversation=conv,
        user=workflow_user,
        content="Which government schemes are available for senior citizens in India?"
    )

    assistant_turn2 = turn2_messages[-1].content
    assert "[🧭 Navigator]" in assistant_turn2


@pytest.mark.asyncio
async def test_cross_agent_priority_override_and_return(db_session, workflow_user):
    """
    Test Priority Matrix transition:
    1. Learn workflow launched -> 💡 Learn
    2. User logs transaction ("I spent ₹650 on books") -> HIGH priority override to 📊 Planner
    3. User asks educational question ("What is inflation?") -> Returns control to 💡 Learn
    """
    conv, messages, chips = await WorkflowLauncher.launch(
        db_session=db_session,
        user=workflow_user,
        workflow_id="learn_finance"
    )

    assert "[💡 Learn]" in messages[-1].content

    # Turn 2: HIGH priority transaction command
    turn2_messages = await ChatService.process_message(
        session=db_session,
        conversation=conv,
        user=workflow_user,
        content="I spent ₹650 on books"
    )

    assistant_turn2 = turn2_messages[-1].content
    assert "[📊 Planner]" in assistant_turn2
    assert "₹650" in assistant_turn2 or "recorded" in assistant_turn2.lower()

    # Turn 3: Educational question -> Returns to primary agent (Learn)
    turn3_messages = await ChatService.process_message(
        session=db_session,
        conversation=conv,
        user=workflow_user,
        content="What is inflation and how does it affect purchasing power?"
    )

    assistant_turn3 = turn3_messages[-1].content
    assert "[💡 Learn]" in assistant_turn3


@pytest.mark.asyncio
async def test_guardian_official_google_url_is_safe(db_session, workflow_user):
    """Verify Guardian correctly identifies official Google URLs as 🟢 SAFE instead of flagging High Phishing Risk."""
    conv, messages, chips = await WorkflowLauncher.launch(
        db_session=db_session,
        user=workflow_user,
        workflow_id="fraud_protection"
    )

    turn2_messages = await ChatService.process_message(
        session=db_session,
        conversation=conv,
        user=workflow_user,
        content="Is https://www.google.com/search?q=finsarthi safe to open?"
    )

    assistant_reply = turn2_messages[-1].content
    assert "[🛡️ Guardian]" in assistant_reply
    assert "🟢 SAFE" in assistant_reply or "Official Verified Domain" in assistant_reply
    assert "High risk detected if from an unverified SMS" not in assistant_reply


@pytest.mark.asyncio
async def test_analyse_my_expenses_does_not_trigger_add_expense(db_session, workflow_user):
    """Verify 'Analyse my expenses' maps to query_planner instead of add_expense."""
    from app.services.intent_extractor import IntentExtractor
    
    intent_res = await IntentExtractor.extract("Analyse my expenses")
    assert intent_res.intent == "query_planner"
    assert intent_res.intent != "add_expense"


@pytest.mark.asyncio
async def test_coach_save_money_goal_turn(db_session, workflow_user):
    """Verify Coach workflow responds dynamically to 'I wish I can save ₹10,000 every month' without returning static Coach Score list."""
    conv, messages, chips = await WorkflowLauncher.launch(
        db_session=db_session,
        user=workflow_user,
        workflow_id="save_money"
    )

    turn2_messages = await ChatService.process_message(
        session=db_session,
        conversation=conv,
        user=workflow_user,
        content="I wish I can save ₹10,000 every month."
    )

    reply = turn2_messages[-1].content
    assert "[🎯 Coach]" in reply
    # Must not contain static card header
    assert "Coach Score 100" not in reply
    assert "✨ FinSarthi Copilot Guidance" not in reply


@pytest.mark.asyncio
async def test_acceptance_criterion_no_generic_copilot_leakage(db_session, workflow_user):
    """
    Acceptance Criterion Test:
    A specialized workflow conversation must NEVER return another agent's greeting or generic Copilot dashboard card.
    """
    for wf_id, expected_badge in [("learn_finance", "[💡 Learn]"), ("fraud_protection", "[🛡️ Guardian]"), ("government_schemes", "[🧭 Navigator]"), ("save_money", "[🎯 Coach]")]:
        conv, messages, chips = await WorkflowLauncher.launch(
            db_session=db_session,
            user=workflow_user,
            workflow_id=wf_id
        )

        turn2_messages = await ChatService.process_message(
            session=db_session,
            conversation=conv,
            user=workflow_user,
            content="Can you explain more details about this?"
        )

        reply = turn2_messages[-1].content
        assert expected_badge in reply, f"Expected {expected_badge} in reply for workflow {wf_id}, got: {reply[:100]}"
        assert "✨ FinSarthi Copilot Guidance" not in reply
        assert "Monthly Spending:" not in reply


