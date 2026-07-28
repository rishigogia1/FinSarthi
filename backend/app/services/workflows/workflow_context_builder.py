"""
services/workflows/workflow_context_builder.py — Assembles workflow domain context & dynamic chips.

Gathers specific financial analytics, profile completeness, and spending trends
before passing to AgentOrchestrator to generate personalized AI guided responses.
"""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.workflows.workflow_registry import WorkflowConfig
from app.services.planner_analytics_service import PlannerAnalyticsService
from app.services.coach_service import CoachService


class WorkflowContextBuilder:
    @classmethod
    async def build(
        cls,
        db_session: AsyncSession,
        user: User,
        config: WorkflowConfig
    ) -> tuple[dict[str, Any], list[str]]:
        """
        Builds domain context payload and dynamic personalized chips.
        Returns: (workflow_context_dict, dynamic_chips_list)
        """
        context_payload: dict[str, Any] = {
            "workflow_id": config.id,
            "title": config.title,
            "primary_agent": config.primary_agent,
            "supporting_agents": config.supporting_agents,
        }
        dynamic_chips: list[str] = list(config.default_chips)

        try:
            if config.id == "save_money":
                summary = await PlannerAnalyticsService.get_summary(db_session, user.id)
                top_cats = sorted(summary.categories, key=lambda c: c.total_amount, reverse=True)
                if top_cats:
                    top_name = top_cats[0].category
                    dynamic_chips = [
                        f"Reduce {top_name} Spend",
                        f"{top_name} Spending Trends",
                        "Set Monthly Savings Target",
                        "Create Category Budget"
                    ]
                context_payload["top_categories"] = [
                    {"category": c.category, "amount": c.total_amount} for c in top_cats[:3]
                ]
                context_payload["monthly_expense"] = summary.overview.monthly_expense
                context_payload["savings_rate"] = summary.overview.savings_rate

            elif config.id == "government_schemes":
                # Check user profile fields if available
                missing_info = []
                profile = getattr(user, "profile", None)
                if profile:
                    if not getattr(profile, "age", None): missing_info.append("Age")
                    if not getattr(profile, "annual_income", None): missing_info.append("Income")
                    if not getattr(profile, "state", None): missing_info.append("State")
                context_payload["missing_profile_fields"] = missing_info

            elif config.id == "investment_advice":
                summary = await PlannerAnalyticsService.get_summary(db_session, user.id)
                surplus = summary.overview.net_cashflow
                context_payload["monthly_surplus"] = max(0.0, surplus)
                if surplus > 5000:
                    dynamic_chips = [
                        f"Invest ₹{int(surplus * 0.5):,} Surplus",
                        "SIP Strategy",
                        "Low Risk Debt Funds",
                        "Equity Growth Portfolio"
                    ]

        except Exception:
            # Fallback gracefully to default chips if analytics fetching encounters empty state
            pass

        return context_payload, dynamic_chips
