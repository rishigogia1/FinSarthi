"""
services/conversation_policy.py — Conversation Policy Evaluator for FinSarthi V2.

Decides agent switching rules, priority matrix overrides, clarification needs,
and conditional Planner analytics injection before routing queries.
"""
import logging
from dataclasses import dataclass
from typing import Tuple
from app.services.conversation_state_manager import ConversationContext

logger = logging.getLogger("app.services.conversation_policy")


@dataclass
class RoutingDecision:
    target_agent: str
    reason: str
    continue_workflow: bool
    override: bool
    confidence: float = 1.0


class ConversationPolicy:
    @classmethod
    def evaluate_routing_policy(
        cls,
        context: ConversationContext,
        intent: str,
        user_message: str
    ) -> RoutingDecision:
        """
        Evaluates Agent Priority Matrix and returns structured RoutingDecision:
        - HIGH Priority: Explicit Transaction CRUD (add_expense, add_income) or Urgent Security Alerts.
        - MEDIUM Priority: Active Workflow Primary Agent (Learn, Guardian, Navigator, Coach, Planner).
        - LOW Priority: General Copilot Chat.
        """
        primary_agent = context.primary_agent.capitalize() if context.primary_agent else None
        lower = user_message.lower()

        # 1. HIGH PRIORITY: Explicit Transaction Commands
        if intent in ["add_expense", "add_income"]:
            logger.info("Policy: HIGH Priority override -> Planner (CRUD)")
            return RoutingDecision(
                target_agent="Planner",
                reason="explicit_transaction_crud",
                continue_workflow=False,
                override=True,
                confidence=0.98
            )

        # 2. HIGH PRIORITY: Urgent Guardian Security Link/QR Alert or Fraud Query
        if intent == "query_guardian" or any(kw in lower for kw in ["bit.ly", "tinyurl", "http://", "https://", "phishing", "qr code", "upi fraud", "payment link", "link safe", "is this link", "scam"]):
            logger.info("Policy: HIGH Priority override -> Guardian (Fraud Inspection)")
            return RoutingDecision(
                target_agent="Guardian",
                reason="security_alert_override",
                continue_workflow=False,
                override=True,
                confidence=0.98
            )

        # 3. HIGH PRIORITY: Explicit Agent Intent Overrides (e.g. user asks Coach/Learn question mid-workflow)
        mapped_intent_agent = cls._map_intent_to_agent(intent)
        if mapped_intent_agent and mapped_intent_agent != primary_agent and intent in ["query_coach_overspending", "query_coach_habits", "query_learn", "query_navigator"]:
            logger.info("Policy: HIGH Priority intent override -> %s (User asked specific topic)", mapped_intent_agent)
            return RoutingDecision(
                target_agent=mapped_intent_agent,
                reason="explicit_topic_switch",
                continue_workflow=False,
                override=True,
                confidence=0.92
            )

        # 4. MEDIUM PRIORITY: Active Workflow Primary Agent Continuation
        if primary_agent:
            logger.info("Policy: MEDIUM Priority -> Active Primary Agent (%s)", primary_agent)
            return RoutingDecision(
                target_agent=primary_agent,
                reason="workflow_persona_continuation",
                continue_workflow=True,
                override=False,
                confidence=0.95
            )

        # 4. LOW PRIORITY: Intent-mapped agent or Copilot fallback
        mapped = cls._map_intent_to_agent(intent)
        if mapped:
            logger.info("Policy: LOW Priority mapped agent -> %s", mapped)
            return RoutingDecision(
                target_agent=mapped,
                reason="intent_mapped_agent",
                continue_workflow=False,
                override=False,
                confidence=0.85
            )

        return RoutingDecision(
            target_agent="Copilot",
            reason="general_chat_fallback",
            continue_workflow=False,
            override=False,
            confidence=0.70
        )

    @classmethod
    def should_inject_analytics(cls, user_message: str, active_agent: str) -> bool:
        """Determines if Planner analytics should be injected into the system prompt."""
        if active_agent == "Planner":
            return True
        
        lower = user_message.lower()
        analytical_keywords = ["my expenses", "my spending", "my budget", "my income", "my cashflow", "how much did i spend", "analyse my spending"]
        return any(kw in lower for kw in analytical_keywords)

    @staticmethod
    def _map_intent_to_agent(intent: str) -> str | None:
        if intent == "query_guardian":
            return "Guardian"
        if intent == "query_learn":
            return "Learn"
        if intent == "query_navigator":
            return "Navigator"
        if intent in ["query_coach_habits", "query_coach_overspending"]:
            return "Coach"
        if intent == "query_planner":
            return "Planner"
        return None
