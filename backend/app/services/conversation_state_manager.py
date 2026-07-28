"""
services/conversation_state_manager.py — Stateful Conversation Manager for FinSarthi V2.

Encapsulates conversation loading, history formatting, compact memory management,
and PostgreSQL state persistence across multi-turn agent conversations.
"""
import logging
from dataclasses import dataclass, field
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.planner_analytics_service import PlannerAnalyticsService

logger = logging.getLogger("app.services.conversation_state_manager")


@dataclass
class ConversationContext:
    conversation: Conversation
    user: User
    session: AsyncSession
    workflow_id: str | None = None
    primary_agent: str | None = None
    workflow_status: str = "ACTIVE"
    workflow_state: dict[str, Any] = field(default_factory=dict)
    workflow_memory: dict[str, Any] = field(default_factory=dict)
    recent_messages: list[dict[str, str]] = field(default_factory=list)
    conversation_summary: str | None = None
    planner_summary: Any | None = None

    def update_memory(self, key: str, value: Any) -> None:
        """Stores a key-value parameter in typed workflow memory."""
        self.workflow_memory[key] = value

    def get_memory(self, key: str, default: Any = None) -> Any:
        """Retrieves a key-value parameter from typed workflow memory."""
        return self.workflow_memory.get(key, default)


class ConversationStateManager:
    @classmethod
    async def load_context(
        cls,
        session: AsyncSession,
        conversation: Conversation,
        user: User,
        max_history_turns: int = 10
    ) -> ConversationContext:
        """
        Hydrates full ConversationContext:
        1. Loads recent message history (last 10 turns).
        2. Hydrates user planner analytics summary.
        3. Parses persistent workflow_state and workflow_memory JSON.
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
        )
        res = await session.execute(stmt)
        history_msgs = list(res.scalars().all())

        # Extract recent turns
        recent_history = history_msgs[-(max_history_turns * 2):] if len(history_msgs) > (max_history_turns * 2) else history_msgs
        formatted_history = [
            {"role": m.role, "content": m.content}
            for m in recent_history
        ]

        # Hydrate planner summary safely
        planner_summary = None
        try:
            planner_summary = await PlannerAnalyticsService.get_planner_summary(session, user.id)
        except Exception as e:
            logger.warning("Could not hydrate planner summary for context: %s", e)

        # Parse memory dicts
        wf_state = conversation.workflow_state if isinstance(conversation.workflow_state, dict) else {}
        wf_mem = conversation.workflow_memory if isinstance(conversation.workflow_memory, dict) else {}

        return ConversationContext(
            conversation=conversation,
            user=user,
            session=session,
            workflow_id=conversation.workflow_id,
            primary_agent=conversation.primary_agent,
            workflow_status=conversation.workflow_status or "ACTIVE",
            workflow_state=wf_state,
            workflow_memory=wf_mem,
            recent_messages=formatted_history,
            planner_summary=planner_summary
        )

    @classmethod
    async def save_context(
        cls,
        session: AsyncSession,
        conversation: Conversation,
        context: ConversationContext
    ) -> None:
        """Persists updated workflow_state and workflow_memory back to PostgreSQL."""
        conversation.workflow_state = context.workflow_state
        conversation.workflow_memory = context.workflow_memory
        session.add(conversation)
        await session.flush()
