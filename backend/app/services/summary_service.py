"""
services/summary_service.py — Service computing dashboard aggregates for transactions history.

Deterministic computations scoped strictly to the current user. Does not contain any AI components.
"""
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.transaction_repository import TransactionRepository
from app.schemas.summaries import (
    OverviewSummaryResponse,
    CategoryBreakdownResponse,
    MonthlyCashflowPoint
)


class SummaryService:
    @staticmethod
    async def get_overview(session: AsyncSession, user_id: str) -> OverviewSummaryResponse:
        """Compute user total income, total expense, and net cashflow."""
        txs = await TransactionRepository.list_user_transactions(session, user_id)
        
        total_income = 0.0
        total_expenses = 0.0
        
        for tx in txs:
            amt = float(tx.amount)
            if tx.type == "income":
                total_income += amt
            elif tx.type == "expense":
                total_expenses += amt
                
        return OverviewSummaryResponse(
            total_income=total_income,
            total_expenses=total_expenses,
            net_cashflow=total_income - total_expenses
        )

    @staticmethod
    async def get_category_breakdown(session: AsyncSession, user_id: str) -> list[CategoryBreakdownResponse]:
        """Produce user category breakdown with allocation percentage."""
        txs = await TransactionRepository.list_user_transactions(session, user_id)
        
        groups = defaultdict(float)  # Key: (category, type)
        total_income = 0.0
        total_expenses = 0.0
        
        for tx in txs:
            amt = float(tx.amount)
            groups[(tx.category, tx.type)] += amt
            if tx.type == "income":
                total_income += amt
            elif tx.type == "expense":
                total_expenses += amt
                
        results = []
        for (cat, tx_type), total in groups.items():
            percentage = 0.0
            if tx_type == "expense" and total_expenses > 0:
                percentage = (total / total_expenses) * 100.0
            elif tx_type == "income" and total_income > 0:
                percentage = (total / total_income) * 100.0
                
            results.append(
                CategoryBreakdownResponse(
                    category=cat,
                    total_amount=total,
                    percentage=round(percentage, 2),
                    type=tx_type
                )
            )
            
        # Sort by total_amount descending
        results.sort(key=lambda x: x.total_amount, reverse=True)
        return results

    @staticmethod
    async def get_monthly_cashflow(session: AsyncSession, user_id: str) -> list[MonthlyCashflowPoint]:
        """Aggregate monthly cashflow histories (income, expense, and net totals)."""
        txs = await TransactionRepository.list_user_transactions(session, user_id)
        
        # Monthly aggregates
        monthly_data = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
        
        for tx in txs:
            month_str = tx.occurred_on.strftime("%Y-%m")
            amt = float(tx.amount)
            if tx.type == "income":
                monthly_data[month_str]["income"] += amt
            elif tx.type == "expense":
                monthly_data[month_str]["expense"] += amt
                
        points = []
        for month_str in sorted(monthly_data.keys()):
            inc = monthly_data[month_str]["income"]
            exp = monthly_data[month_str]["expense"]
            points.append(
                MonthlyCashflowPoint(
                    month=month_str,
                    income=inc,
                    expense=exp,
                    net=inc - exp
                )
            )
            
        return points
