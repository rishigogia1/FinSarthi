"""
services/workflows/workflow_launcher.py — Atomic Workflow Launcher for FinSarthi V2.

Handles workflow launch, conversation creation with metadata, context assembly,
and initial AgentOrchestrator execution.
"""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.workflows.workflow_registry import WorkflowRegistry, WorkflowConfig
from app.services.workflows.workflow_context_builder import WorkflowContextBuilder
from app.services.chat_service import ChatService


class WorkflowLauncher:
    @classmethod
    async def launch(
        cls,
        db_session: AsyncSession,
        user: User,
        workflow_id: str
    ) -> tuple[Conversation, list[Message], list[str]]:
        """
        Launches a guided financial AI workflow:
        1. Fetches WorkflowConfig.
        2. Assembles context and dynamic chips.
        3. Persists new Conversation record with workflow metadata.
        4. Processes initial starter prompt through ChatService/AgentOrchestrator.
        5. Returns (conversation, messages, dynamic_chips).
        """
        config = WorkflowRegistry.get(workflow_id)
        if not config:
            raise ValueError(f"Invalid workflow ID: '{workflow_id}'")

        # 1. Build context & dynamic chips
        workflow_context, dynamic_chips = await WorkflowContextBuilder.build(db_session, user, config)

        # 2. Create conversation record with persisted metadata
        conv = Conversation(
            user_id=user.id,
            title=config.title,
            workflow_id=config.id,
            workflow_status="ACTIVE",
            primary_agent=config.primary_agent,
            supporting_agents=config.supporting_agents,
            icon=config.icon
        )
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        # 3. Process starter prompt to create initial user and assistant turns
        messages = await ChatService.process_message(
            session=db_session,
            conversation=conv,
            user=user,
            content=config.starter_prompt
        )

        return conv, messages, dynamic_chips
