"""
services/command_router.py — Central dispatcher mapping actionable chat intents to domain services.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.planner import ParsedIntentSchema, PlannerSummaryResponseSchema
from app.services.transaction_service import TransactionService, TransactionServiceError
from app.services.planner_analytics_service import PlannerAnalyticsService

logger = logging.getLogger("app.services.command_router")


class FinancialCommandRouter:
    @classmethod
    async def dispatch(
        cls,
        session: AsyncSession,
        user_id: str,
        intent_payload: ParsedIntentSchema
    ) -> dict:
        """
        Dispatches parsed intents to domain services (TransactionService, PlannerAnalyticsService).
        Returns a dict containing execution status, conversational confirmation text, and updated summary.
        """
        intent = intent_payload.intent

        # 1. Ambiguity / Low Confidence Check
        if intent_payload.requires_confirmation or intent_payload.confidence < 0.6:
            prompt = intent_payload.clarification_prompt or "I noticed you mentioned a transaction. Could you specify the exact amount in ₹?"
            return {
                "handled": True,
                "action": "clarification_requested",
                "message": prompt,
                "summary": None
            }

        # 2. Add Expense Intent
        if intent == "add_expense":
            amount = intent_payload.amount
            if not amount or amount <= 0:
                return {
                    "handled": True,
                    "action": "validation_failed",
                    "message": "I couldn't identify a valid expense amount. Please specify an amount greater than zero.",
                    "summary": None
                }

            category = intent_payload.category or "Other"
            note = intent_payload.description or "Logged via chat"
            occurred_on = intent_payload.date

            try:
                tx, is_dup = await TransactionService.create_expense(
                    session=session,
                    user_id=user_id,
                    amount=amount,
                    category=category,
                    occurred_on=occurred_on,
                    note=note,
                    source="CHAT"
                )

                summary = await PlannerAnalyticsService.get_planner_summary(session, user_id)
                formatted_amount = f"₹{amount:,.2f}".replace(".00", "")
                monthly_exp = f"₹{summary.overview.monthly_expense:,.2f}".replace(".00", "")
                tx_count = summary.analytics.total_transactions

                if is_dup:
                    msg = (
                        f"ℹ️ I noticed an identical expense of {formatted_amount} for **{category}** was recently recorded.\n\n"
                        f"• Monthly Spending: **{monthly_exp}**\n"
                        f"• Total Transactions: **{tx_count}**"
                    )
                else:
                    msg = (
                        f"✅ I've recorded your expense.\n\n"
                        f"• Amount: **{formatted_amount}**\n"
                        f"• Category: **{category}**\n"
                        f"• Monthly Spending: **{monthly_exp}**\n\n"
                        f"You've recorded **{tx_count}** transaction(s) this month."
                    )

                return {
                    "handled": True,
                    "action": "add_expense",
                    "is_duplicate": is_dup,
                    "message": msg,
                    "transaction_id": tx.id,
                    "summary": summary
                }

            except TransactionServiceError as e:
                return {
                    "handled": True,
                    "action": "error",
                    "message": f"Could not record expense: {e.message}",
                    "summary": None
                }

        # 3. Add Income Intent
        elif intent == "add_income":
            amount = intent_payload.amount
            if not amount or amount <= 0:
                return {
                    "handled": True,
                    "action": "validation_failed",
                    "message": "I couldn't identify a valid income amount. Please specify an amount greater than zero.",
                    "summary": None
                }

            category = intent_payload.category or "Salary"
            note = intent_payload.description or "Logged via chat"
            occurred_on = intent_payload.date

            try:
                tx, is_dup = await TransactionService.create_income(
                    session=session,
                    user_id=user_id,
                    amount=amount,
                    category=category,
                    occurred_on=occurred_on,
                    note=note,
                    source="CHAT"
                )

                summary = await PlannerAnalyticsService.get_planner_summary(session, user_id)
                formatted_amount = f"₹{amount:,.2f}".replace(".00", "")
                monthly_inc = f"₹{summary.overview.monthly_income:,.2f}".replace(".00", "")
                net_cash = f"₹{summary.overview.net_cashflow:,.2f}".replace(".00", "")

                msg = (
                    f"🎉 I've recorded your income!\n\n"
                    f"• Amount: **{formatted_amount}**\n"
                    f"• Category: **{category}**\n"
                    f"• Monthly Income: **{monthly_inc}**\n"
                    f"• Net Cashflow: **{net_cash}**"
                )

                return {
                    "handled": True,
                    "action": "add_income",
                    "is_duplicate": is_dup,
                    "message": msg,
                    "transaction_id": tx.id,
                    "summary": summary
                }

            except TransactionServiceError as e:
                return {
                    "handled": True,
                    "action": "error",
                    "message": f"Could not record income: {e.message}",
                    "summary": None
                }

        # 4. Query Planner Intent
        elif intent == "query_planner":
            summary = await PlannerAnalyticsService.get_planner_summary(session, user_id)
            exp_fmt = f"₹{summary.overview.monthly_expense:,.2f}".replace(".00", "")
            inc_fmt = f"₹{summary.overview.monthly_income:,.2f}".replace(".00", "")
            net_fmt = f"₹{summary.overview.net_cashflow:,.2f}".replace(".00", "")
            top_cat = summary.analytics.largest_category or "None"
            top_amt = f"₹{summary.analytics.largest_category_amount:,.2f}".replace(".00", "")

            msg = (
                f"📊 Here is your financial summary from Planner:\n\n"
                f"• Monthly Spending: **{exp_fmt}**\n"
                f"• Monthly Income: **{inc_fmt}**\n"
                f"• Net Cashflow: **{net_fmt}**\n"
                f"• Top Category: **{top_cat}** ({top_amt})\n"
                f"• Total Transactions: **{summary.analytics.total_transactions}**"
            )

            return {
                "handled": True,
                "action": "query_planner",
                "message": msg,
                "summary": summary
            }

        # 5. Query Coach Intents
        elif intent in ["query_coach_habits", "query_coach_overspending", "query_coach"]:
            from app.services.coach_service import CoachService
            msg = await CoachService.format_chat_response(session, user_id, intent)
            return {
                "handled": True,
                "action": intent,
                "message": msg,
                "summary": None
            }

        # 6. General Chat
        return {
            "handled": False,
            "action": "general_chat",
            "message": "",
            "summary": None
        }

