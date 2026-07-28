"""
tests/test_workflow_launcher.py — Integration tests for FinSarthi V2 Guided AI Workflows.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.services.workflows.workflow_launcher import WorkflowLauncher
from app.services.workflows.workflow_registry import WorkflowRegistry


@pytest.fixture
async def workflow_user(db_session: AsyncSession) -> User:
    """Create temporary user for Workflow Launcher tests."""
    user = User(
        name="Workflow Test User",
        email="workflow_user_v2@finsarthi.app",
        password_hash="hashed_pw_123"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_workflow_registry_config():
    """Verifies that all 6 workflow configurations are correctly registered."""
    workflows = WorkflowRegistry.list_all()
    assert len(workflows) == 6
    ids = {w.id for w in workflows}
    assert ids == {"save_money", "government_schemes", "fraud_protection", "financial_goals", "investment_advice", "learn_finance"}


@pytest.mark.asyncio
async def test_workflow_launcher_save_money(db_session: AsyncSession, workflow_user: User):
    """Test launching Save Money guided workflow."""
    conv, messages, chips = await WorkflowLauncher.launch(db_session, workflow_user, "save_money")
    assert conv.title == "Saving More Every Month"
    assert conv.workflow_id == "save_money"
    assert conv.primary_agent == "coach"
    assert conv.icon == "💰"
    assert len(messages) >= 2
    assert "[🎯 Coach]" in messages[-1].content
    assert len(chips) > 0


@pytest.mark.asyncio
async def test_workflow_launcher_government_schemes(db_session: AsyncSession, workflow_user: User):
    """Test launching Government Schemes guided workflow."""
    conv, messages, chips = await WorkflowLauncher.launch(db_session, workflow_user, "government_schemes")
    assert conv.title == "Government Schemes & Benefits"
    assert conv.primary_agent == "navigator"
    assert "[🧭 Navigator]" in messages[-1].content


@pytest.mark.asyncio
async def test_workflow_launcher_fraud_protection(db_session: AsyncSession, workflow_user: User):
    """Test launching Fraud Protection guided workflow."""
    conv, messages, chips = await WorkflowLauncher.launch(db_session, workflow_user, "fraud_protection")
    assert conv.title == "Fraud & Security Check"
    assert conv.primary_agent == "guardian"
    assert "[🛡️ Guardian]" in messages[-1].content


@pytest.mark.asyncio
async def test_workflow_launcher_invalid_id(db_session: AsyncSession, workflow_user: User):
    """Test launching an invalid workflow ID raises ValueError."""
    with pytest.raises(ValueError, match="Invalid workflow ID"):
        await WorkflowLauncher.launch(db_session, workflow_user, "non_existent_workflow")
