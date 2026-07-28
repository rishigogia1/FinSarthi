"""
scratch/trace_pipeline.py — Pipeline Trace Tool for FinSarthi V2.

Executes a exact multi-turn conversation sequence and prints the exact execution trace at every stage:
Incoming Message -> Conversation Context -> Intent -> Policy Decision -> Selected Agent -> LLM Execution -> Final Response.
"""
import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
import logging

# Configure root logger to output detailed pipeline logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import User
from app.models.conversation import Conversation
from app.services.chat_service import ChatService
from app.services.workflows.workflow_launcher import WorkflowLauncher
from app.services.conversation_state_manager import ConversationStateManager
from app.services.conversation_policy import ConversationPolicy
from app.services.intent_extractor import IntentExtractor
from app.services.agents.agent_orchestrator import AgentOrchestrator


async def trace_conversation():
    print("=" * 80)
    print("FINSARTHI MULTI-TURN PIPELINE TRACE RUN")
    print("=" * 80)

    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create test user
        import uuid
        user = User(
            email=f"trace_user_{uuid.uuid4().hex[:6]}@finsarthi.app",
            name="Rishi",
            password_hash="hashed_pwd"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        print(f"\n[STEP 0] Launching Workflow: financial_goals")
        conv, messages, chips = await WorkflowLauncher.launch(
            db_session=session,
            user=user,
            workflow_id="financial_goals"
        )
        print(f"Created Conversation ID: {conv.id}")
        print(f"Initial Primary Agent: {conv.primary_agent}")
        print(f"Initial Workflow State: {conv.workflow_state}")

        queries = [
            "Let's plan a financial goal.",
            "I have some financial goals to complete this month.",
            "Am I overspending?",
            "Is this payment link safe?"
        ]

        for idx, query in enumerate(queries, start=1):
            print("\n" + "-" * 80)
            print(f"[TURN {idx}] Incoming Message: '{query}'")
            print("-" * 80)

            # 1. Hydrate Conversation Context
            conv_context = await ConversationStateManager.load_context(
                session=session,
                conversation=conv,
                user=user
            )
            print(f"  |-- [1. Context] workflow_id={conv_context.workflow_id}, primary_agent={conv_context.primary_agent}, recent_msg_count={len(conv_context.recent_messages)}")

            # 2. Extract Intent
            intent_payload = await IntentExtractor.extract(query)
            print(f"  |-- [2. Intent Extractor] intent={intent_payload.intent}, confidence={intent_payload.confidence}")

            # 3. Policy Decision
            routing_decision = ConversationPolicy.evaluate_routing_policy(
                context=conv_context,
                intent=intent_payload.intent,
                user_message=query
            )
            print(f"  |-- [3. Policy Decision] target_agent={routing_decision.target_agent}, reason={routing_decision.reason}, override={routing_decision.override}")

            # 4. Process message via ChatService
            updated_messages = await ChatService.process_message(
                session=session,
                conversation=conv,
                user=user,
                content=query
            )

            final_reply = updated_messages[-1].content.encode('ascii', 'ignore').decode('ascii')
            print(f"  |-- [4. Final Response Returned]\n")
            print(f"     {final_reply}")

        print("\n" + "=" * 80)
        print("TRACE RUN COMPLETE")
        print("=" * 80)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(trace_conversation())
