"""
services/planner_analytics_service.py — Planner analytics service consuming the shared AnalyticsEngine.
"""
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics_engine import AnalyticsEngine
from app.schemas.planner import (
    PlannerSummaryResponseSchema,
    PlannerOverviewSchema,
    PlannerCategoryAggregateSchema,
    PlannerActivitySchema,
    PlannerAnalyticsMetricsSchema,
)

logger = logging.getLogger("app.services.planner_analytics")


class PlannerAnalyticsService:
    @classmethod
    async def get_planner_summary(
        cls,
        session: AsyncSession,
        user_id: str,
        year: int | None = None,
        month: int | None = None
    ) -> PlannerSummaryResponseSchema:
        """
        Assembles the standardized Planner summary object consuming the shared AnalyticsEngine.
        """
        data = await AnalyticsEngine.get_financial_summary(session, user_id, year, month)

        overview = PlannerOverviewSchema(
            monthly_expense=data["overview"]["monthly_expense"],
            monthly_income=data["overview"]["monthly_income"],
            net_cashflow=data["overview"]["net_cashflow"],
            savings_rate=data["overview"]["savings_rate"]
        )

        categories = [
            PlannerCategoryAggregateSchema(
                category=cat["category"],
                total_amount=cat["total_amount"],
                percentage=cat["percentage"]
            )
            for cat in data["categories"]
        ]

        activity = PlannerActivitySchema(
            today_count=data["activity"]["today_count"],
            latest_category=data["activity"]["latest_category"],
            last_transaction_amount=data["activity"]["last_transaction_amount"],
            last_transaction_type=data["activity"]["last_transaction_type"]
        )

        analytics = PlannerAnalyticsMetricsSchema(
            avg_daily_spend=data["analytics"]["avg_daily_spend"],
            weekly_spend=data["analytics"]["weekly_spend"],
            largest_category=data["analytics"]["largest_category"],
            largest_category_amount=data["analytics"]["largest_category_amount"],
            total_transactions=data["analytics"]["total_transactions"]
        )

        logger.info(
            "Planner Summary Generated (via AnalyticsEngine): user_id=%s, month=%02d/%d, expense=%s, income=%s, txs=%d",
            user_id, data["month"], data["year"], overview.monthly_expense, overview.monthly_income, analytics.total_transactions
        )

        return PlannerSummaryResponseSchema(
            overview=overview,
            categories=categories,
            activity=activity,
            analytics=analytics,
            generated_at=datetime.now(timezone.utc),
            currency="INR"
        )

    @classmethod
    async def average_daily_spend(cls, session: AsyncSession, user_id: str, year: int | None = None, month: int | None = None) -> float:
        data = await AnalyticsEngine.get_financial_summary(session, user_id, year, month)
        return data["analytics"]["avg_daily_spend"]

    @classmethod
    async def weekly_spend(cls, session: AsyncSession, user_id: str, year: int | None = None, month: int | None = None) -> float:
        data = await AnalyticsEngine.get_financial_summary(session, user_id, year, month)
        return data["analytics"]["weekly_spend"]
