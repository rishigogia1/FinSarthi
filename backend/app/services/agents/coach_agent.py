"""
services/agents/coach_agent.py — Coach Agent implementing BaseAgent interface.
"""
from datetime import datetime, timezone
from app.services.agents.base_agent import BaseAgent
from app.services.agents.registry import AgentRegistry
from app.schemas.dashboard import AgentDashboardResponse
from app.schemas.dashboard_context import AgentContext
from app.services.coach_service import CoachService


class CoachAgent(BaseAgent):
    async def generate(self, context: AgentContext) -> AgentDashboardResponse:
        agent_id = "coach"
        name = "Coach"
        role = "Habits & Behavior"
        desc = "Coach observes your spending behavior, detects patterns, and provides personalized coaching based on transaction history."

        # Fetch Coach summary if session and user are available
        if getattr(context, "session", None) is not None and getattr(context, "user", None) is not None:
            summary = await CoachService.get_coach_summary(context.session, context.user.id)
            status_str = "Active" if summary.status == "Active" else "Learning"
            ready = summary.readiness.ready

            requirements = [
                {"name": f"Minimum 20 transactions ({summary.readiness.tx_count}/20 collected)", "met": summary.readiness.tx_count >= 20},
                {"name": f"Minimum 30 days history ({summary.readiness.days_history}/30 days)", "met": summary.readiness.days_history >= 30},
            ]

            metrics = {
                "status": summary.status,
                "ready": ready,
                "progressPercentage": summary.readiness.progress_percentage,
                "txCount": summary.readiness.tx_count,
                "requiredTx": summary.readiness.required_tx,
                "daysHistory": summary.readiness.days_history,
                "coachScore": summary.score.score if summary.score else None,
                "coachRating": summary.score.rating if summary.score else None,
                "biggestHabit": summary.habits.largest_category or "None",
                "mostFrequentCategory": summary.habits.most_frequent_category or "None",
                "avgDailySpend": summary.habits.avg_daily_spend,
                "avgWeeklySpend": summary.habits.avg_weekly_spend,
            }

            activities = [summary.ai_coaching] if summary.ai_coaching else []
            recs = [r.recommendation for r in summary.recommendations]

            return AgentDashboardResponse(
                id=agent_id,
                name=name,
                role=role,
                description=desc,
                implementation_status=status_str,
                current_phase="V2",
                requirements=requirements if not ready else [],
                metrics=metrics,
                recommendations=recs,
                activities=activities,
                actions=[],
                last_updated=summary.last_updated
            )

        # Fallback if no session
        return AgentDashboardResponse(
            id=agent_id,
            name=name,
            role=role,
            description=desc,
            implementation_status="Learning",
            current_phase="V2",
            requirements=[
                {"name": "Minimum 20 transactions", "met": False},
                {"name": "Minimum 30 days history", "met": False},
            ],
            metrics={"status": "Learning", "progressPercentage": 0.0},
            recommendations=[],
            activities=["Collecting transaction history to analyze spending habits."],
            actions=[],
            last_updated=datetime.now(timezone.utc)
        )


AgentRegistry.register(CoachAgent)
