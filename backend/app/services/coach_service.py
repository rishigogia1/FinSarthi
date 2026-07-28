"""
services/coach_service.py — Domain service orchestrating Coach readiness, scoring, rules, and coaching text.

Inherits from BaseDomainService. Consumes AnalyticsEngine and FinancialRuleEngine.
"""
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base_domain_service import BaseDomainService
from app.services.analytics_engine import AnalyticsEngine
from app.services.financial_rule_engine import FinancialRuleEngine
from app.services.recommendation_formatter import RecommendationFormatter
from app.core.coach_config import coach_settings
from app.schemas.coach import (
    CoachSummaryResponseSchema,
    CoachReadinessSchema,
    CoachScoreSchema,
    CoachHabitsSchema,
)


class CoachService(BaseDomainService):
    def __init__(self):
        super().__init__("coach")

    @classmethod
    async def get_coach_summary(
        cls,
        session: AsyncSession,
        user_id: str,
        year: int | None = None,
        month: int | None = None
    ) -> CoachSummaryResponseSchema:
        """
        Generates full Coach Summary response:
        - Evaluates readiness threshold (20 tx or 30 days history)
        - Computes Coach Score (0-100) if Active, or enters Learning state
        - Evaluates financial rules via FinancialRuleEngine
        - Generates natural coaching text via RecommendationFormatter
        """
        start_time = datetime.now()
        # 1. Fetch unified analytics snapshot
        data = await AnalyticsEngine.get_financial_summary(session, user_id, year, month)

        # 2. Check Readiness Thresholds
        tx_count = data["history"]["total_tx_count"]
        days_history = data["history"]["days_history"]
        min_tx = coach_settings.MIN_TRANSACTIONS
        min_days = coach_settings.MIN_HISTORY_DAYS

        is_ready = (tx_count >= min_tx) or (days_history >= min_days)
        status = "Active" if is_ready else "Learning"
        progress_pct = min(100.0, round((tx_count / min_tx) * 100.0, 1))

        if is_ready:
            readiness_msg = "Sufficient financial history collected. Coach is Active."
        else:
            readiness_msg = f"Learning from spending patterns. {tx_count}/{min_tx} transactions collected."

        readiness = CoachReadinessSchema(
            status=status,
            ready=is_ready,
            progress_percentage=progress_pct,
            tx_count=tx_count,
            required_tx=min_tx,
            days_history=days_history,
            required_days=min_days,
            message=readiness_msg
        )

        # 3. Assemble Habits
        habits = CoachHabitsSchema(
            most_frequent_category=data["analytics"]["most_frequent_category"],
            largest_category=data["analytics"]["largest_category"],
            avg_daily_spend=data["analytics"]["avg_daily_spend"],
            avg_weekly_spend=data["analytics"]["weekly_spend"],
            category_breakdown=data["categories"]
        )

        # 4. If Learning State: return without score or rules
        if not is_ready:
            ai_coaching = await RecommendationFormatter.format_coaching(
                status="Learning",
                score=None,
                savings_rate=data["overview"]["savings_rate"],
                largest_category=data["analytics"]["largest_category"],
                recommendations=[],
                tx_count=tx_count,
                required_tx=min_tx
            )

            return CoachSummaryResponseSchema(
                status="Learning",
                readiness=readiness,
                score=None,
                habits=habits,
                recommendations=[],
                ai_coaching=ai_coaching,
                last_updated=datetime.now(timezone.utc)
            )

        # 5. Active State: Evaluate Rules & Calculate Score
        recommendations = FinancialRuleEngine.evaluate_rules(data)
        score_obj = cls._calculate_coach_score(data, recommendations)

        # 6. Format Coaching Text
        ai_coaching = await RecommendationFormatter.format_coaching(
            status="Active",
            score=score_obj.score,
            savings_rate=data["overview"]["savings_rate"],
            largest_category=data["analytics"]["largest_category"],
            recommendations=recommendations,
            tx_count=tx_count,
            required_tx=min_tx
        )

        return CoachSummaryResponseSchema(
            status="Active",
            readiness=readiness,
            score=score_obj,
            habits=habits,
            recommendations=recommendations,
            ai_coaching=ai_coaching,
            last_updated=datetime.now(timezone.utc)
        )

    @classmethod
    def _calculate_coach_score(cls, data: dict[str, Any], recommendations: list) -> CoachScoreSchema:
        """
        Calculates a deterministic 0-100 Coach Score based on:
        - Savings Ratio (30 pts max)
        - Cashflow Surplus (20 pts max)
        - Category Concentration (25 pts max)
        - Daily Spend Stability (25 pts max)
        """
        overview = data["overview"]
        analytics = data["analytics"]

        savings_rate = overview["savings_rate"]
        inc = overview["monthly_income"]
        exp = overview["monthly_expense"]

        reasons = []

        # 1. Savings Ratio (30 pts max)
        if inc > 0:
            savings_pts = min(30.0, (savings_rate / 20.0) * 30.0)
            if savings_rate >= 20.0:
                reasons.append(f"Good savings rate ({savings_rate:.1f}%)")
            else:
                reasons.append(f"Savings rate ({savings_rate:.1f}%) below 20% target")
        else:
            savings_pts = 15.0
            reasons.append("Income not recorded for full savings assessment")

        # 2. Cashflow Surplus (20 pts max)
        if inc >= exp:
            cashflow_pts = 20.0
            reasons.append("Positive cashflow")
        else:
            cashflow_pts = 5.0
            reasons.append("Cashflow deficit (Expenses exceed income)")

        # 3. Category Concentration (25 pts max)
        categories = data.get("categories", [])
        max_pct = categories[0]["percentage"] if categories else 0.0
        if max_pct <= 35.0:
            category_pts = 25.0
            reasons.append("Balanced spending across categories")
        elif max_pct <= 50.0:
            category_pts = 15.0
            reasons.append(f"Concentrated spend in top category ({categories[0]['category']}: {max_pct:.1f}%)")
        else:
            category_pts = 5.0
            reasons.append(f"High discretionary concentration in {categories[0]['category']} ({max_pct:.1f}%)")

        # 4. Transaction Regularity & Stability (25 pts max)
        avg_daily = analytics["avg_daily_spend"]
        if avg_daily > 0 and exp > 0:
            stability_pts = 25.0
            reasons.append("Consistent daily spending pattern")
        else:
            stability_pts = 15.0

        total_score = int(round(savings_pts + cashflow_pts + category_pts + stability_pts))
        total_score = max(0, min(100, total_score))

        if total_score >= 80:
            rating = "Excellent"
        elif total_score >= 65:
            rating = "Good"
        elif total_score >= 50:
            rating = "Fair"
        else:
            rating = "Needs Attention"

        return CoachScoreSchema(
            score=total_score,
            rating=rating,
            reasons=reasons
        )

    @classmethod
    async def format_chat_response(
        cls,
        session: AsyncSession,
        user_id: str,
        intent: str
    ) -> str:
        """
        Formats a clean, direct chat reply for Coach intent queries ("How are my spending habits?", "Am I overspending?").
        Chat pipeline calls this method directly to avoid duplicating conditional state logic.
        """
        summary = await cls.get_coach_summary(session, user_id)

        if summary.status == "Learning":
            return (
                f"🧠 **Coach is currently in Learning Mode**\n\n"
                f"I've collected **{summary.readiness.tx_count} / {summary.readiness.required_tx}** transactions so far. "
                f"Keep logging your daily transactions, and once we reach {summary.readiness.required_tx} transactions, "
                f"I'll unlock your full Coach Score and habit insights!"
            )

        top_cat = summary.habits.largest_category or "None"
        avg_daily = f"₹{summary.habits.avg_daily_spend:,.2f}".replace(".00", "")
        weekly_sp = f"₹{summary.habits.avg_weekly_spend:,.2f}".replace(".00", "")
        score_val = summary.score.score if summary.score else "N/A"
        savings_val = f"{summary.habits.category_breakdown[0]['percentage']:.1f}%" if summary.habits.category_breakdown else "0%"

        if intent == "query_coach_overspending":
            recs_text = ""
            if summary.recommendations:
                recs_text = "\n\n**Actionable Advice:**\n" + "\n".join([f"• **{r.title}**: {r.recommendation}" for r in summary.recommendations])

            return (
                f"🧭 **Coach Spend Analysis:**\n\n"
                f"{summary.ai_coaching}\n\n"
                f"• **Weekly Spend:** {weekly_sp}\n"
                f"• **Average Daily Spend:** {avg_daily}\n"
                f"• **Top Spending Category:** {top_cat}"
                f"{recs_text}"
            )

        # Default query_coach_habits
        return (
            f"🎯 **Coach Habit Breakdown (Score: {score_val}/100):**\n\n"
            f"{summary.ai_coaching}\n\n"
            f"• **Most Frequent Category:** {summary.habits.most_frequent_category or 'None'}\n"
            f"• **Largest Category:** {top_cat}\n"
            f"• **Average Daily Spend:** {avg_daily}\n"
            f"• **Weekly Spend:** {weekly_sp}"
        )
