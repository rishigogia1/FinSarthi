"""
services/admin_service.py — Aggregates read-only dashboard analytics for admins.
"""
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.goal import Goal
from app.core.rate_limit import get_redis_client
from app.schemas.admin import AdminUserSummary, SystemSummaryResponse


class AdminService:
    @staticmethod
    async def list_users_summaries(session: AsyncSession) -> list[AdminUserSummary]:
        """Aggregate total counts across all user accounts."""
        stmt = select(User).order_by(User.created_at.desc())
        res = await session.execute(stmt)
        users = res.scalars().all()

        summaries = []
        for user in users:
            # Count transactions
            t_stmt = select(func.count(Transaction.id)).where(Transaction.user_id == user.id)
            t_res = await session.execute(t_stmt)
            t_count = t_res.scalar() or 0

            # Count budgets
            b_stmt = select(func.count(Budget.id)).where(Budget.user_id == user.id)
            b_res = await session.execute(b_stmt)
            b_count = b_res.scalar() or 0

            # Count goals
            g_stmt = select(func.count(Goal.id)).where(Goal.user_id == user.id)
            g_res = await session.execute(g_stmt)
            g_count = g_res.scalar() or 0

            summaries.append(
                AdminUserSummary(
                    user_id=user.id,
                    name=user.name,
                    email=user.email,
                    role=user.role,
                    last_login_at=user.last_login_at,
                    onboarding_completed=user.onboarding_completed,
                    transaction_count=t_count,
                    budget_count=b_count,
                    goal_count=g_count
                )
            )
        return summaries

    @staticmethod
    async def get_system_summary(session: AsyncSession) -> SystemSummaryResponse:
        """Fetch basic liveness metrics for DB and Redis configurations."""
        # 1. DB Liveness check
        db_ok = False
        try:
            await session.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            pass

        # 2. Redis Liveness check
        redis_ok = False
        try:
            client = get_redis_client()
            if client and client.ping():
                redis_ok = True
        except Exception:
            pass

        # 3. Counts
        u_count = (await session.execute(select(func.count(User.id)))).scalar() or 0
        t_count = (await session.execute(select(func.count(Transaction.id)))).scalar() or 0
        b_count = (await session.execute(select(func.count(Budget.id)))).scalar() or 0
        g_count = (await session.execute(select(func.count(Goal.id)))).scalar() or 0

        return SystemSummaryResponse(
            database_connected=db_ok,
            redis_connected=redis_ok,
            total_users=u_count,
            total_transactions=t_count,
            total_budgets=b_count,
            total_goals=g_count
        )
