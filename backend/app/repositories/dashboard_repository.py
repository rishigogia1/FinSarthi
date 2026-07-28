from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.models.user import User
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.schemas.dashboard_context import AgentContext
from app.services.planner_analytics_service import PlannerAnalyticsService

class DashboardRepository:
    """
    Fetches raw data and analytics from the database required for the AI Team Dashboard.
    """
    
    @staticmethod
    async def get_agent_context(session: AsyncSession, user: User) -> AgentContext:
        # Fetch Budgets
        budgets_stmt = select(Budget).where(Budget.user_id == user.id)
        budgets_result = await session.execute(budgets_stmt)
        budgets = list(budgets_result.scalars().all())

        # Fetch Goals
        goals_stmt = select(Goal).where(Goal.user_id == user.id)
        goals_result = await session.execute(goals_stmt)
        goals = list(goals_result.scalars().all())

        # Fetch Recent Transactions (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        transactions_stmt = (
            select(Transaction)
            .where(Transaction.user_id == user.id, Transaction.occurred_on >= thirty_days_ago.date())
            .order_by(Transaction.occurred_on.desc())
            .limit(100)
        )
        transactions_result = await session.execute(transactions_stmt)
        transactions = list(transactions_result.scalars().all())
        
        # Fetch standardized Planner summary from PlannerAnalyticsService (Single Source of Truth)
        planner_summary = None
        try:
            planner_summary = await PlannerAnalyticsService.get_planner_summary(session, user.id)
        except Exception:
            pass

        return AgentContext(
            user=user,
            session=session,
            planner_summary=planner_summary,
            profile={},
            budgets=budgets,
            goals=goals,
            transactions=transactions,
            preferences={},
            analytics={}
        )
