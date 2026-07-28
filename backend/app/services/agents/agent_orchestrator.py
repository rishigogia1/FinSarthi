"""
services/agents/agent_orchestrator.py — Multi-Agent Coordinator for FinSarthi V2.

Coordinates Planner, Coach, Guardian, Learn, and Navigator agents.
Uses Priority Matrix (HIGH / MEDIUM / LOW) and PromptFactory for agent persona isolation.
"""
import re
import logging
from typing import Any
from app.schemas.dashboard_context import AgentContext
from app.schemas.planner import ParsedIntentSchema
from app.services.planner_analytics_service import PlannerAnalyticsService
from app.services.coach_service import CoachService
from app.services.command_router import FinancialCommandRouter
from app.services.prompts.prompt_factory import PromptFactory
from app.services.guardian_service import GuardianService
from app.services.conversation_policy import ConversationPolicy
from app.services.llm_service import LLMService

logger = logging.getLogger("app.services.agents.agent_orchestrator")


class AgentOrchestrator:
    @classmethod
    async def route_and_execute(
        cls,
        context: AgentContext,
        intent_payload: ParsedIntentSchema,
        user_message: str
    ) -> dict[str, Any]:
        """
        Orchestrates agent execution based on Priority Matrix:
        1. HIGH Priority: Explicit Transaction CRUD (add_expense, add_income) or Urgent Guardian Security Alerts.
        2. MEDIUM Priority: Active Workflow Primary Agent (Learn, Guardian, Navigator, Coach, Planner).
        3. LOW Priority: General Copilot Chat.
        """
        intent = intent_payload.intent
        session = context.session
        user_id = context.user.id
        primary_agent = context.primary_agent

        logger.info(
            "Routing turn: workflow_id=%s, primary_agent=%s, intent=%s",
            context.workflow_id, primary_agent, intent,
            extra={
                "workflow_id": context.workflow_id,
                "primary_agent": primary_agent,
                "intent": intent,
                "is_override": intent in ["add_expense", "add_income"]
            }
        )

        # ----------------------------------------------------
        # 1. HIGH PRIORITY: Explicit Transaction Commands
        # ----------------------------------------------------
        if intent in ["add_expense", "add_income"]:
            cmd_result = await FinancialCommandRouter.dispatch(
                session=session,
                user_id=user_id,
                intent_payload=intent_payload
            )
            cat = intent_payload.category or "Spending"
            chips = [
                f"View {cat} Spending",
                "Am I overspending?",
                "How much did I spend this month?"
            ]
            return {
                "handled": True,
                "content": cmd_result.get("message", "Transaction recorded successfully."),
                "agent_badge": "📊 Planner",
                "suggested_chips": chips,
                "action": intent
            }

        # ----------------------------------------------------
        # 2. MEDIUM PRIORITY: Active Workflow Agent / Persona Execution
        # ----------------------------------------------------
        active_agent_raw = primary_agent or cls._map_intent_to_agent(intent)
        active_agent = active_agent_raw.capitalize() if active_agent_raw else None

        if active_agent == "Guardian" or intent == "query_guardian":
            content = await cls._execute_agent_llm(context, user_message, agent_name="Guardian")
            chips = ["Check payment link", "Is UPI request safe?", "Online banking safety rules"]
            return {
                "handled": True,
                "content": content,
                "agent_badge": "🛡️ Guardian",
                "suggested_chips": chips,
                "action": "query_guardian"
            }

        if active_agent == "Learn" or intent == "query_learn":
            content = await cls._execute_agent_llm(context, user_message, agent_name="Learn")
            chips = ["Explain Mutual Funds", "What is an Emergency Fund?", "Tax saving options"]
            return {
                "handled": True,
                "content": content,
                "agent_badge": "💡 Learn",
                "suggested_chips": chips,
                "action": "query_learn"
            }

        if active_agent == "Navigator" or intent == "query_navigator":
            content = await cls._execute_agent_llm(context, user_message, agent_name="Navigator")
            chips = ["How much to save monthly?", "Am I overspending?", "Investment options"]
            return {
                "handled": True,
                "content": content,
                "agent_badge": "🧭 Navigator",
                "suggested_chips": chips,
                "action": "query_navigator"
            }

        if active_agent == "Coach" or intent in ["query_coach_habits", "query_coach_overspending"]:
            content = await cls._execute_agent_llm(context, user_message, agent_name="Coach")
            chips = ["How to improve my score?", "Monthly spending breakdown", "Set savings target"]
            return {
                "handled": True,
                "content": content,
                "agent_badge": "🎯 Coach",
                "suggested_chips": chips,
                "action": intent
            }

        if active_agent == "Planner" or intent == "query_planner":
            content = await cls._execute_agent_llm(context, user_message, agent_name="Planner")
            chips = ["Am I overspending?", "Top spending categories", "Set monthly budget"]
            return {
                "handled": True,
                "content": content,
                "agent_badge": "📊 Planner",
                "suggested_chips": chips,
                "action": intent
            }

        # ----------------------------------------------------
        # 3. LOW PRIORITY: General Copilot Chat
        # ----------------------------------------------------
        content = await cls._execute_agent_llm(context, user_message, agent_name="Copilot")
        chips = ["How much did I spend this month?", "Am I overspending?", "Explain SIP"]
        return {
            "handled": True,
            "content": content,
            "agent_badge": "✨ Copilot",
            "suggested_chips": chips,
            "action": "general_chat"
        }

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

    @classmethod
    async def _evaluate_guardian_security(cls, context: AgentContext, text: str) -> str:
        lower = text.lower()
        if any(kw in lower for kw in ["http", "https", ".com", ".xyz", ".top", "bit.ly"]):
            return (
                "🛡️ **Guardian Security Alert**\n\n"
                "I've analyzed the link you shared:\n"
                "• **Phishing Risk**: High risk detected if from an unverified SMS/WhatsApp sender.\n"
                "• **Safety Rule**: Banks and genuine payment gateways NEVER send shortened link URLs asking for PINs, passwords, or OTPs.\n\n"
                "⚠️ **Action**: Do not click or enter any financial credentials."
            )
        
        # Try dynamic LLM reasoning via PromptFactory
        try:
            return await cls._execute_agent_llm(context, text, agent_name="Guardian")
        except Exception:
            return (
                "🛡️ **Guardian Fraud Safety Guidance**\n\n"
                "• **UPI Safety**: Entering your UPI PIN is ONLY required to DEBIT money from your account, never to receive money.\n"
                "• **QR Code Scam**: Scanning a QR code sent by someone else authorizes a PAYMENT out of your bank.\n"
                "• **Golden Rule**: If a deal or refund sounds too good to be true, verify directly with official app customer service."
            )

    @classmethod
    async def _evaluate_learn_education(cls, context: AgentContext, query: str) -> str:
        lower = query.lower()
        if "sip" in lower and len(query.split()) < 6:
            return (
                "💡 **Learn: Systematic Investment Plan (SIP)**\n\n"
                "A **SIP** allows you to invest a fixed amount regularly (e.g. ₹1,000/month) into mutual funds.\n\n"
                "• **Rupee Cost Averaging**: You buy more units when prices are low and fewer when prices are high.\n"
                "• **Power of Compounding**: Interest earned earns further returns over long periods.\n"
                "• **Disciplined Savings**: Automated monthly debits remove emotional market timing."
            )
        if "emergency fund" in lower and len(query.split()) < 6:
            return (
                "💡 **Learn: Emergency Fund 101**\n\n"
                "An **Emergency Fund** is liquid money set aside for unexpected crises like medical expenses or job disruption.\n\n"
                "• **Target Size**: 3 to 6 months of essential living expenses (rent, food, utilities, EMIs).\n"
                "• **Where to keep**: High-yield savings accounts or liquid mutual funds for instant access."
            )
        
        # LLM educational response with Learn Persona
        return await cls._execute_agent_llm(context, query, agent_name="Learn")

    @classmethod
    async def _evaluate_navigator_affordability(cls, context: AgentContext, query: str) -> str:
        session = context.session
        user_id = context.user.id
        summary = await PlannerAnalyticsService.get_planner_summary(session, user_id)

        net_cashflow = summary.overview.net_cashflow
        monthly_exp = summary.overview.monthly_expense

        amount_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d{1,2})?)', query, re.IGNORECASE)
        if amount_match:
            target_amt = float(amount_match.group(1).replace(",", ""))
            target_fmt = f"₹{target_amt:,.2f}".replace(".00", "")
            cashflow_fmt = f"₹{net_cashflow:,.2f}".replace(".00", "")

            if net_cashflow <= 0:
                return (
                    f"🧭 **Navigator Affordability Assessment**\n\n"
                    f"You're considering a purchase of **{target_fmt}**.\n\n"
                    f"• **Current Net Cashflow**: {cashflow_fmt} (Monthly expenses equal or exceed income)\n"
                    f"• **Recommendation**: Before taking on new major purchases or EMIs, focus on reducing monthly expenses to establish a positive savings rate of at least 15-20%."
                )
            
            months_needed = int(target_amt / net_cashflow) if net_cashflow > 0 else 24
            return (
                f"🧭 **Navigator Affordability & Goal Plan**\n\n"
                f"Target Purchase: **{target_fmt}**\n\n"
                f"• **Current Monthly Surplus**: {cashflow_fmt}\n"
                f"• **Estimated Timeframe**: ~**{months_needed} month(s)** saving 100% of your current monthly surplus.\n"
                f"• **Balanced Strategy**: Allocating 50% of your monthly surplus ({f'₹{net_cashflow*0.5:,.2f}'.replace('.00','')}/mo) achieves your target in ~**{months_needed*2} months** while maintaining emergency liquidity."
            )
        
        # Fallback to LLM reasoning via PromptFactory
        return await cls._execute_agent_llm(context, query, agent_name="Navigator")

    @classmethod
    async def _execute_agent_llm(cls, context: AgentContext, query: str, agent_name: str | None = None) -> str:
        from app.services.response_validator import ResponseValidator

        history = context.conversation_history
        target_agent = (agent_name or context.primary_agent or "Copilot").capitalize()
        
        system_prompt = PromptFactory.get_system_prompt(target_agent, context, query)

        messages = [{"role": "system", "content": system_prompt}]
        recent_history = history[-10:] if len(history) > 10 else history
        messages.extend(recent_history)

        # Deduplicate user query if it's already the last element in recent_history
        if not (recent_history and recent_history[-1].get("role") == "user" and recent_history[-1].get("content") == query):
            messages.append({"role": "user", "content": query})

        try:
            res = await LLMService.generate(messages=messages, temperature=0.7, max_tokens=1000)
            raw_content = res.get("content", "")
            
            # Response Validation
            is_valid, validated_content = ResponseValidator.validate(raw_content, target_agent)
            if not is_valid:
                logger.warning("ResponseValidator flagged output for agent '%s', using validated content.", target_agent)
            
            return validated_content
        except Exception as e:
            logger.warning("Agent LLM call failed for '%s', using persona fallback: %s", target_agent, e)
            return await cls._generate_agent_fallback(context, query, target_agent)

    @classmethod
    async def _generate_agent_fallback(cls, context: AgentContext, query: str, agent_name: str) -> str:
        user_name = context.user.name
        agent_clean = agent_name.capitalize()
        notice_header = "⚠️ *AI reasoning is temporarily unavailable (Quota/Connection limit). Displaying local analysis:*\n\n"

        if agent_clean == "Guardian":
            from app.services.guardian_service import GuardianService
            return GuardianService.analyze_security_request(query)

        elif agent_clean == "Planner":
            try:
                summary = await PlannerAnalyticsService.get_planner_summary(context.session, context.user.id)
                exp = f"₹{summary.overview.monthly_expense:,.2f}".replace(".00", "")
                inc = f"₹{summary.overview.monthly_income:,.2f}".replace(".00", "")
                net = f"₹{summary.overview.net_cashflow:,.2f}".replace(".00", "")
                top_cat = summary.analytics.largest_category or "General"
                return (
                    f"{notice_header}📊 **FinSarthi Planner Snapshot**\n\n"
                    f"• **Monthly Spend:** {exp}\n"
                    f"• **Monthly Income:** {inc}\n"
                    f"• **Net Cashflow:** {net}\n"
                    f"• **Top Expense Category:** {top_cat}"
                )
            except Exception:
                return f"{notice_header}📊 **FinSarthi Planner**: Unable to fetch local transaction summary right now."

        elif agent_clean == "Coach":
            try:
                summary = await PlannerAnalyticsService.get_planner_summary(context.session, context.user.id)
                exp = summary.overview.monthly_expense
                inc = summary.overview.monthly_income
                surplus = inc - exp
                exp_str = f"₹{exp:,.2f}".replace(".00", "")
                inc_str = f"₹{inc:,.2f}".replace(".00", "")
                surplus_str = f"₹{surplus:,.2f}".replace(".00", "")

                return (
                    f"{notice_header}🎯 **FinSarthi Coach Local Analysis**\n\n"
                    f"Based on your latest financial records:\n"
                    f"• **Monthly Income**: {inc_str}\n"
                    f"• **Monthly Expenses**: {exp_str}\n"
                    f"• **Calculated Surplus**: {surplus_str}\n\n"
                    f"Once AI reasoning is restored, I will analyze specific habit optimizations for your target."
                )
            except Exception:
                return f"{notice_header}🎯 **FinSarthi Coach**: Hello {user_name}! Ready to review spending habits once AI connectivity is restored."

        elif agent_clean == "Navigator":
            return (
                f"{notice_header}🧭 **FinSarthi Navigator**\n\n"
                f"Hello {user_name}! I can assist you with evaluating major purchase goals, planning EMI budgets, or discovering Indian Government Schemes (PPF, NPS, Sukanya Samriddhi)."
            )

        elif agent_clean == "Learn":
            return (
                f"{notice_header}💡 **FinSarthi Learn Guidance**\n\n"
                f"Popular Financial Literacy Topics:\n"
                f"• **SIP & Compounding**: Investing fixed monthly amounts over long horizons.\n"
                f"• **Emergency Reserves**: Saving 3-6 months of essential living expenses.\n"
                f"• **Tax Regimes**: Comparing Old Regime 80C deductions vs lower New Regime tax slabs."
            )

        # Generic Copilot Fallback
        try:
            summary = await PlannerAnalyticsService.get_planner_summary(context.session, context.user.id)
            exp = f"₹{summary.overview.monthly_expense:,.2f}".replace(".00", "")
            inc = f"₹{summary.overview.monthly_income:,.2f}".replace(".00", "")
            net = f"₹{summary.overview.net_cashflow:,.2f}".replace(".00", "")
            top_cat = summary.analytics.largest_category or "General"

            return (
                f"{notice_header}✨ **FinSarthi Copilot Guidance**\n\n"
                f"Here is your current financial snapshot:\n\n"
                f"• **Monthly Spend:** {exp}\n"
                f"• **Monthly Income:** {inc}\n"
                f"• **Net Cashflow:** {net}\n"
                f"• **Top Category:** {top_cat}"
            )
        except Exception:
            return f"{notice_header}✨ **FinSarthi Copilot**: Hello {user_name}! Offline mode active."

