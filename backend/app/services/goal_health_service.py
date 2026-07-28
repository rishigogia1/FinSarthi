"""
services/goal_health_service.py — Business logic evaluating deadline feasibility and goal progress.

Determines goal health labels (on_track, at_risk, off_track) grounded in user savings rates.
"""
from datetime import date, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.goals_repository import GoalsRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.analytics import GoalHealthResponse

logger = logging.getLogger(__name__)


class GoalHealthService:
    @staticmethod
    async def get_goals_health(session: AsyncSession, user_id: str) -> list[GoalHealthResponse]:
        """Assess target health status for all user goals based on financial trajectory."""
        goals = await GoalsRepository.get_user_goals(session, user_id)
        txs = await TransactionRepository.list_user_transactions(session, user_id)
        
        # Calculate user's actual historical monthly savings rate
        user_monthly_savings = 0.0
        if txs:
            total_income = sum(float(t.amount) for t in txs if t.type == "income")
            total_expenses = sum(float(t.amount) for t in txs if t.type == "expense")
            net_savings = total_income - total_expenses
            
            earliest_date = min(t.occurred_on for t in txs)
            days_span = (date.today() - earliest_date).days
            if days_span < 30:
                days_span = 30
            user_monthly_savings = (net_savings / days_span) * 30.4
            
        results = []
        for g in goals:
            target = float(g.target_amount)
            current = float(g.current_amount)
            
            completion_pct = 0.0
            if target > 0:
                completion_pct = (current / target) * 100.0
                
            status = "on_track"
            reason = "Progress is being made towards target."
            
            if current >= target:
                status = "on_track"
                reason = "Goal target has been achieved."
            elif g.deadline is not None:
                days_remaining = (g.deadline - date.today()).days
                
                if days_remaining <= 0:
                    status = "off_track"
                    reason = "Target deadline has passed without completion."
                else:
                    remaining_amt = target - current
                    required_monthly_savings = (remaining_amt / days_remaining) * 30.4
                    
                    if len(txs) < 10:
                        status = "at_risk"
                        reason = "Insufficient financial history to reliably calculate savings pace."
                    elif user_monthly_savings >= required_monthly_savings:
                        status = "on_track"
                        reason = f"Savings pace (INR {round(user_monthly_savings, 2)}/mo) is sufficient for deadline."
                    elif user_monthly_savings <= 0 or user_monthly_savings < (0.5 * required_monthly_savings):
                        status = "off_track"
                        reason = f"Savings pace (INR {round(user_monthly_savings, 2)}/mo) is far below target (INR {round(required_monthly_savings, 2)}/mo)."
                    else:
                        status = "at_risk"
                        reason = f"Savings pace (INR {round(user_monthly_savings, 2)}/mo) is slightly below target (INR {round(required_monthly_savings, 2)}/mo)."
            else:
                # No deadline specified
                if current == 0:
                    status = "at_risk"
                    reason = "No progress has been made yet, and no deadline is set."
                else:
                    status = "on_track"
                    reason = "Progress is being made (no deadline specified)."
                    
            results.append(
                GoalHealthResponse(
                    goal_id=g.id,
                    goal_name=g.goal_name,
                    target_amount=target,
                    current_amount=current,
                    completion_percentage=round(completion_pct, 2),
                    status=status,
                    reason=reason
                )
            )
            
        return results
