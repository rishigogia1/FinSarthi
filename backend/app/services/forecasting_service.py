"""
services/forecasting_service.py — Service estimating short-term future cashflows and budget overrun risks.

Uses transparent, explainable moving-average heuristics and active recurring entries.
"""
from datetime import date, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.transaction_repository import TransactionRepository
from app.repositories.recurring_cashflow_repository import RecurringCashflowRepository
from app.repositories.budget_repository import BudgetRepository
from app.repositories.goals_repository import GoalsRepository
from app.schemas.forecasts import (
    MonthlyCashflowForecastResponse,
    BudgetRiskForecastResponse,
    GoalProjectionResponse
)

logger = logging.getLogger(__name__)


class ForecastingService:
    @staticmethod
    async def get_history_stats(session: AsyncSession, user_id: str):
        """Helper to get user's historical non-recurring averages and span data."""
        txs = await TransactionRepository.list_user_transactions(session, user_id)
        rcs = await RecurringCashflowRepository.list_user_cashflows(session, user_id)
        
        active_rc_inc = sum(float(r.amount) for r in rcs if r.active and r.type == "income")
        active_rc_exp = sum(float(r.amount) for r in rcs if r.active and r.type == "expense")
        
        if not txs:
            return 0.0, 0.0, active_rc_inc, active_rc_exp, len(txs), 0, "low"
            
        earliest_date = min(t.occurred_on for t in txs)
        days_span = (date.today() - earliest_date).days
        if days_span < 30:
            days_span = 30
            
        # Separate recurring transactions to get pure non-recurring averages
        non_recurring_income = 0.0
        non_recurring_expense = 0.0
        
        for tx in txs:
            # If there is a recurring configuration of same category, let's treat it as recurring, otherwise non-recurring
            is_recurring_cat = any(r.category.lower() == tx.category.lower() for r in rcs if r.active)
            amt = float(tx.amount)
            if tx.type == "income":
                if not is_recurring_cat:
                    non_recurring_income += amt
            elif tx.type == "expense":
                if not is_recurring_cat:
                    non_recurring_expense += amt
                    
        # Monthly non-recurring average
        avg_non_rec_inc = (non_recurring_income / days_span) * 30.4
        avg_non_rec_exp = (non_recurring_expense / days_span) * 30.4
        
        confidence = "low"
        if len(txs) >= 20 and days_span >= 90:
            confidence = "high"
        elif len(txs) >= 10:
            confidence = "medium"
            
        return avg_non_rec_inc, avg_non_rec_exp, active_rc_inc, active_rc_exp, len(txs), days_span, confidence

    @staticmethod
    async def forecast_monthly_cashflow(
        session: AsyncSession,
        user_id: str
    ) -> MonthlyCashflowForecastResponse:
        """Forecast next-month cashflow values using recurring flows and history averages."""
        stats = await ForecastingService.get_history_stats(session, user_id)
        avg_inc, avg_exp, rc_inc, rc_exp, tx_count, _, confidence = stats
        
        if tx_count < 10:
            # Low history fallback
            pred_inc = rc_inc
            pred_exp = rc_exp
            reason = "Low history: predictions are based solely on active recurring items."
            confidence = "low"
        else:
            pred_inc = rc_inc + avg_inc
            pred_exp = rc_exp + avg_exp
            reason = f"Combined projection: includes active recurring items and historical averages."
            
        return MonthlyCashflowForecastResponse(
            predicted_income=round(pred_inc, 2),
            predicted_expense=round(pred_exp, 2),
            predicted_net=round(pred_inc - pred_exp, 2),
            confidence=confidence,
            reason=reason
        )

    @staticmethod
    async def forecast_budget_risk(
        session: AsyncSession,
        user_id: str
    ) -> list[BudgetRiskForecastResponse]:
        """Project overrun risks of category budgets based on spending averages."""
        budgets = await BudgetRepository.list_user_budgets(session, user_id)
        txs = await TransactionRepository.list_user_transactions(session, user_id)
        rcs = await RecurringCashflowRepository.list_user_cashflows(session, user_id)
        
        active_budgets = [b for b in budgets if b.active]
        if not txs:
            # Low data fallback
            return [
                BudgetRiskForecastResponse(
                    category=b.category,
                    budget_limit=float(b.limit_amount),
                    predicted_spend=0.0,
                    overrun_risk="low",
                    confidence="low"
                ) for b in active_budgets
            ]
            
        earliest_date = min(t.occurred_on for t in txs)
        days_span = max(30, (date.today() - earliest_date).days)
        confidence = "high" if len(txs) >= 20 and days_span >= 90 else ("medium" if len(txs) >= 10 else "low")
        
        results = []
        for b in active_budgets:
            # Compute historical average for this specific category
            cat_sum = 0.0
            for tx in txs:
                if tx.type == "expense" and tx.category.lower() == b.category.lower():
                    cat_sum += float(tx.amount)
            avg_cat_spent = (cat_sum / days_span) * 30.4
            
            # Predict spend = category average
            pred_spend = avg_cat_spent
            limit = float(b.limit_amount)
            
            overrun_risk = "low"
            if limit > 0:
                ratio = pred_spend / limit
                if ratio > 1.0:
                    overrun_risk = "high"
                elif ratio >= 0.8:
                    overrun_risk = "medium"
                    
            results.append(
                BudgetRiskForecastResponse(
                    category=b.category,
                    budget_limit=limit,
                    predicted_spend=round(pred_spend, 2),
                    overrun_risk=overrun_risk,
                    confidence=confidence
                )
            )
            
        return results

    @staticmethod
    async def forecast_goal_projection(
        session: AsyncSession,
        user_id: str
    ) -> list[GoalProjectionResponse]:
        """Estimate goal completion dates based on overall monthly savings rate."""
        goals = await GoalsRepository.get_user_goals(session, user_id)
        txs = await TransactionRepository.list_user_transactions(session, user_id)
        
        # Calculate actual net savings rate
        user_monthly_savings = 0.0
        if txs:
            total_inc = sum(float(t.amount) for t in txs if t.type == "income")
            total_exp = sum(float(t.amount) for t in txs if t.type == "expense")
            net_savings = total_inc - total_exp
            earliest_date = min(t.occurred_on for t in txs)
            days_span = max(30, (date.today() - earliest_date).days)
            user_monthly_savings = (net_savings / days_span) * 30.4
            
        confidence = "high" if len(txs) >= 20 else ("medium" if len(txs) >= 10 else "low")
        results = []
        
        for g in goals:
            target = float(g.target_amount)
            current = float(g.current_amount)
            remaining = target - current
            
            if remaining <= 0:
                results.append(
                    GoalProjectionResponse(
                        goal_id=g.id,
                        goal_name=g.goal_name,
                        projected_completion_date=str(date.today()),
                        is_trackable=True,
                        confidence="high",
                        reason="Goal target already achieved."
                    )
                )
            elif user_monthly_savings <= 0:
                results.append(
                    GoalProjectionResponse(
                        goal_id=g.id,
                        goal_name=g.goal_name,
                        projected_completion_date=None,
                        is_trackable=False,
                        confidence=confidence,
                        reason="Zero or negative monthly savings pace; completion cannot be calculated."
                    )
                )
            else:
                months_needed = remaining / user_monthly_savings
                proj_days = int(months_needed * 30.4)
                # Cap future projection at 50 years to avoid overflow/absurdity
                if proj_days > 18250:
                    proj_days = 18250
                proj_date = date.today() + timedelta(days=proj_days)
                
                results.append(
                    GoalProjectionResponse(
                        goal_id=g.id,
                        goal_name=g.goal_name,
                        projected_completion_date=str(proj_date),
                        is_trackable=True,
                        confidence=confidence,
                        reason=f"Based on current savings pace of INR {round(user_monthly_savings, 2)}/mo."
                    )
                )
                
        return results
