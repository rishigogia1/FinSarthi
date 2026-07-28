"""
services/analytics_service.py — Service compiling deterministic user-scoped financial analytics.

Computes savings rates, rolling trends, category distributions, and budget adherence percentages.
"""
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.transaction_repository import TransactionRepository
from app.repositories.budget_repository import BudgetRepository
from app.schemas.analytics import (
    OverviewAnalyticsResponse,
    SpendingTrendPoint,
    CategoryTrendResponse,
    BudgetHealthResponse
)


class AnalyticsService:
    @staticmethod
    async def get_overview(session: AsyncSession, user_id: str) -> OverviewAnalyticsResponse:
        """Compute rolling totals and net savings rate over all user transactions."""
        txs = await TransactionRepository.list_user_transactions(session, user_id)
        
        total_income = 0.0
        total_expenses = 0.0
        
        for tx in txs:
            amt = float(tx.amount)
            if tx.type == "income":
                total_income += amt
            elif tx.type == "expense":
                total_expenses += amt
                
        net_savings = total_income - total_expenses
        savings_rate = 0.0
        if total_income > 0:
            savings_rate = (net_savings / total_income) * 100.0
            
        return OverviewAnalyticsResponse(
            total_income=total_income,
            total_expenses=total_expenses,
            net_savings=net_savings,
            savings_rate=round(savings_rate, 2)
        )

    @staticmethod
    async def get_spending_trends(session: AsyncSession, user_id: str) -> CategoryTrendResponse:
        """Compute category-wise breakdown of expenses."""
        txs = await TransactionRepository.list_user_transactions(session, user_id)
        
        category_sums = defaultdict(float)
        total_expenses = 0.0
        
        for tx in txs:
            if tx.type == "expense":
                amt = float(tx.amount)
                category_sums[tx.category] += amt
                total_expenses += amt
                
        trends = []
        for cat, amt in category_sums.items():
            pct = 0.0
            if total_expenses > 0:
                pct = (amt / total_expenses) * 100.0
            trends.append(
                SpendingTrendPoint(
                    category=cat,
                    total_amount=amt,
                    percentage=round(pct, 2)
                )
            )
            
        # Sort by total spent descending
        trends.sort(key=lambda x: x.total_amount, reverse=True)
        return CategoryTrendResponse(trends=trends)

    @staticmethod
    async def get_budget_health(session: AsyncSession, user_id: str) -> list[BudgetHealthResponse]:
        """Compute utilization rates of active budgets based on actual transactions."""
        budgets = await BudgetRepository.list_user_budgets(session, user_id)
        txs = await TransactionRepository.list_user_transactions(session, user_id)
        
        active_budgets = [b for b in budgets if b.active]
        results = []
        
        for b in active_budgets:
            actual_spent = 0.0
            for tx in txs:
                # Matches category and falls within budget dates (inclusive)
                if (tx.type == "expense" and 
                        tx.category.lower() == b.category.lower() and 
                        tx.occurred_on >= b.start_date):
                    if b.end_date is None or tx.occurred_on <= b.end_date:
                        actual_spent += float(tx.amount)
                        
            limit = float(b.limit_amount)
            usage_pct = 0.0
            if limit > 0:
                usage_pct = (actual_spent / limit) * 100.0
                
            status = "normal"
            if usage_pct > 100.0:
                status = "exceeded"
            elif usage_pct >= 90.0:
                status = "warning"
                
            results.append(
                BudgetHealthResponse(
                    category=b.category,
                    limit_amount=limit,
                    actual_spent=actual_spent,
                    usage_percentage=round(usage_pct, 2),
                    status=status
                )
            )
            
        return results
