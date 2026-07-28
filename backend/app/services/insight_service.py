"""
services/insight_service.py — Service identifying structured financial warnings and savings milestones.

Prioritizes alerts, filters noise, and encapsulates raw evidence details.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
# Let's import Settings to get default config properties
from app.services.analytics_service import AnalyticsService
from app.services.goal_health_service import GoalHealthService
from app.services.forecasting_service import ForecastingService
from app.schemas.insights import InsightResponse

logger = logging.getLogger(__name__)


class InsightService:
    @staticmethod
    async def get_structured_insights(session: AsyncSession, user_id: str) -> list[InsightResponse]:
        """Convert calculated indicators into ranked structured alerts."""
        overview = await AnalyticsService.get_overview(session, user_id)
        budget_health = await AnalyticsService.get_budget_health(session, user_id)
        goal_health = await GoalHealthService.get_goals_health(session, user_id)
        
        # Get count of transactions to check data threshold
        stats = await ForecastingService.get_history_stats(session, user_id)
        _, _, _, _, tx_count, _, _ = stats
        
        insights = []
        
        # 1. Low history warning
        if tx_count < 10:
            insights.append(
                InsightResponse(
                    title="Build Your Financial History",
                    message="You have fewer than 10 transactions recorded. Keep logging to unlock personalized AI insights.",
                    type="low_history",
                    severity="info",
                    confidence="low",
                    evidence={"transactions_count": tx_count},
                    action_hint="Log a transaction today."
                )
            )
            
        # 2. Overspending / Budget alerts
        for b in budget_health:
            if b.status == "exceeded":
                insights.append(
                    InsightResponse(
                        title=f"Budget Exceeded: {b.category}",
                        message=f"You spent INR {round(b.actual_spent, 2)} in {b.category}, exceeding limit of INR {round(b.limit_amount, 2)}.",
                        type="budget_alert",
                        severity="critical",
                        confidence="high",
                        evidence={"category": b.category, "limit": b.limit_amount, "actual": b.actual_spent},
                        action_hint="Review recent purchases in this category."
                    )
                )
            elif b.status == "warning":
                insights.append(
                    InsightResponse(
                        title=f"Nearing Budget: {b.category}",
                        message=f"You spent {round(b.usage_percentage, 2)}% of your limit for {b.category}.",
                        type="budget_alert",
                        severity="warning",
                        confidence="high",
                        evidence={"category": b.category, "limit": b.limit_amount, "actual": b.actual_spent},
                        action_hint="Consider slowing down discretionary purchases here."
                    )
                )
                
        # 3. Goal health alerts
        for g in goal_health:
            if g.status == "off_track":
                insights.append(
                    InsightResponse(
                        title=f"Goal Off Track: {g.goal_name}",
                        message=f"Your goal is off track. {g.reason}",
                        type="goal_warning",
                        severity="critical",
                        confidence="medium",
                        evidence={"goal_id": g.goal_id, "status": g.status, "completion": g.completion_percentage},
                        action_hint="Adjust the goal target date or monthly saving rate."
                    )
                )
            elif g.status == "at_risk":
                insights.append(
                    InsightResponse(
                        title=f"Goal At Risk: {g.goal_name}",
                        message=f"Your goal is at risk. {g.reason}",
                        type="goal_warning",
                        severity="warning",
                        confidence="medium",
                        evidence={"goal_id": g.goal_id, "status": g.status, "completion": g.completion_percentage},
                        action_hint="Allocate slightly more to your savings this month."
                    )
                )
                
        # 4. Healthy savings rate milestone
        if overview.savings_rate >= 30.0:
            insights.append(
                InsightResponse(
                    title="Healthy Savings Rate",
                    message=f"Congratulations! You saved {round(overview.savings_rate, 2)}% of your total income.",
                    type="savings_insight",
                    severity="info",
                    confidence="high",
                    evidence={"savings_rate": overview.savings_rate},
                    action_hint="Keep up the excellent savings discipline."
                )
            )
            
        # Rank by severity: critical -> warning -> info
        severity_rank = {"critical": 0, "warning": 1, "info": 2}
        insights.sort(key=lambda x: severity_rank.get(x.severity, 2))
        
        # Max limit
        # For safety and clean coding, default limit is 5
        max_limit = 5
        return insights[:max_limit]
