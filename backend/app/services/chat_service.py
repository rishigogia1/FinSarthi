"""
services/chat_service.py — AI Chat Service for FinSarthi.

Handles conversation memory, context management, intent routing, and LLM orchestration.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.llm_service import LLMService, LLMError
from app.services.intent_extractor import IntentExtractor
from app.services.command_router import FinancialCommandRouter

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Manages system instructions and conversation history formatting."""
    
    @staticmethod
    def build_system_prompt(user_name: str) -> str:
        return (
            f"You are FinSarthi, an AI Personal Finance Assistant for {user_name}.\n"
            "Follow these rules strictly:\n"
            "1. NEVER hallucinate financial guarantees or promise specific returns.\n"
            "2. Distinguish clearly between facts and your own suggestions.\n"
            "3. Ask follow-up questions when insufficient information exists (e.g., age, income, risk appetite).\n"
            "4. Avoid repeating greetings. You are already in the middle of a conversation.\n"
            "5. Answer naturally, concisely, and conversationally. Do not use generic templates.\n"
            "6. Provide expertise on: Investments, Mutual Funds, SIPs, Budgeting, Taxes, Loans, Insurance, Government Schemes, and Fraud Detection."
        )

    @staticmethod
    def format_history(history: list[Message], max_history_turns: int = 10) -> list[dict[str, str]]:
        formatted = []
        recent_history = history[-(max_history_turns * 2):] if len(history) > (max_history_turns * 2) else history
        
        for msg in recent_history:
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })
            
        return formatted


from app.schemas.dashboard_context import AgentContext
from app.services.agents.agent_orchestrator import AgentOrchestrator
from app.services.conversation_state_manager import ConversationStateManager
from app.services.conversation_policy import ConversationPolicy


class ChatService:
    """Orchestrates the chat pipeline via ConversationStateManager, ConversationPolicy, and AgentOrchestrator."""

    @staticmethod
    def _generate_deterministic_title(content: str, intent: str) -> str:
        """Generates clear, topic-focused titles based on query intent."""
        lower = content.lower()
        if intent == "query_planner" or "spent" in lower or "budget" in lower:
            return "Monthly Budget & Spending Review"
        if intent in ["query_coach_habits", "query_coach_overspending"]:
            return "Financial Behavior & Overspending Check"
        if intent == "query_guardian":
            return "Fraud & Security Verification"
        if intent == "query_learn":
            if "sip" in lower:
                return "SIP & Investment Education"
            return "Financial Literacy & Education"
        if intent == "query_navigator" or "afford" in lower or "buy" in lower:
            return "Purchase Affordability & Goal Planning"
        if intent in ["add_expense", "add_income"]:
            return "Expense & Income Tracking"

        return (content[:30] + "...") if len(content) > 30 else content

    @staticmethod
    async def process_message(
        session: AsyncSession,
        conversation: Conversation,
        user: User,
        content: str
    ) -> list[Message]:
        """
        Processes user messages via stateful multi-agent pipeline:
        1. Saves user message to database.
        2. Hydrates ConversationContext via ConversationStateManager.
        3. Extracts Intent via IntentExtractor.
        4. Evaluates routing policy via ConversationPolicy.
        5. Executes turn via AgentOrchestrator.
        6. Persists updated conversation state/memory.
        7. Saves assistant message to database.
        """
        # 1. Save user's message
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=content
        )
        session.add(user_msg)
        await session.flush()

        # 2. Hydrate Conversation Context via ConversationStateManager
        conv_context = await ConversationStateManager.load_context(
            session=session,
            conversation=conversation,
            user=user
        )

        # 3. Extract Intent
        intent_payload = await IntentExtractor.extract(content)

        # 4. Evaluate Routing Policy
        routing_decision = ConversationPolicy.evaluate_routing_policy(
            context=conv_context,
            intent=intent_payload.intent,
            user_message=content
        )

        logger.info(
            "[PIPELINE] conv_id=%s, wf_id=%s, primary_agent=%s, intent=%s, target_agent=%s, reason=%s",
            conversation.id,
            conv_context.workflow_id,
            conv_context.primary_agent,
            intent_payload.intent,
            routing_decision.target_agent,
            routing_decision.reason
        )

        # 5. Deterministic Title Generation
        if conversation.title == "New Conversation" or not conversation.title:
            conversation.title = ChatService._generate_deterministic_title(content, intent_payload.intent)

        # 6. Build AgentContext for Orchestrator
        agent_context = AgentContext(
            user=user,
            session=session,
            conversation_history=conv_context.recent_messages,
            workflow_id=conv_context.workflow_id,
            workflow_status=conv_context.workflow_status,
            primary_agent=routing_decision.target_agent,
            supporting_agents=conversation.supporting_agents or [],
            workflow_state=conv_context.workflow_state,
            workflow_memory=conv_context.workflow_memory
        )

        # 7. Route & Execute via AgentOrchestrator
        orch_res = await AgentOrchestrator.route_and_execute(
            context=agent_context,
            intent_payload=intent_payload,
            user_message=content
        )

        # 8. Persist updated context memory back to PostgreSQL
        if "updated_workflow_state" in orch_res:
            conv_context.workflow_state = orch_res["updated_workflow_state"]
        if "updated_workflow_memory" in orch_res:
            conv_context.workflow_memory = orch_res["updated_workflow_memory"]

        await ConversationStateManager.save_context(session, conversation, conv_context)

        badge_prefix = f"[{orch_res['agent_badge']}] " if orch_res.get("agent_badge") else ""
        final_content = badge_prefix + orch_res["content"]

        # 8. Save Assistant Response
        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=final_content
        )
        session.add(assistant_msg)
        await session.commit()

        # 9. Return updated conversation thread
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
