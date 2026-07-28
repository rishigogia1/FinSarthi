"""
repositories/budget_repository.py — Data access layer for Budget model.
"""
from datetime import date
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.budget import Budget


class BudgetRepository:
    @staticmethod
    async def get_user_budget(
        session: AsyncSession,
        user_id: str,
        budget_id: str
    ) -> Budget | None:
        """Retrieve user's specific budget."""
        stmt = select(Budget).where(
            Budget.id == budget_id,
            Budget.user_id == user_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_user_budgets(
        session: AsyncSession,
        user_id: str
    ) -> list[Budget]:
        """List all budgets belonging to a user."""
        stmt = select(Budget).where(Budget.user_id == user_id).order_by(Budget.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_budget(
        session: AsyncSession,
        user_id: str,
        category: str,
        limit_amount: float,
        period: str,
        start_date: date,
        end_date: date | None = None,
        active: bool = True
    ) -> Budget:
        """Create a new category budget."""
        budget = Budget(
            user_id=user_id,
            category=category,
            limit_amount=limit_amount,
            period=period,
            start_date=start_date,
            end_date=end_date,
            active=active
        )
        session.add(budget)
        await session.flush()
        return budget

    @staticmethod
    async def delete_budget(session: AsyncSession, budget_id: str) -> None:
        """Remove a budget configuration from database."""
        stmt = delete(Budget).where(Budget.id == budget_id)
        await session.execute(stmt)

    @staticmethod
    async def get_active_overlapping_budgets(
        session: AsyncSession,
        user_id: str,
        category: str,
        start_date: date,
        end_date: date | None,
        exclude_budget_id: str | None = None
    ) -> list[Budget]:
        """
        Find any other active budget in the same category that overlaps this date range.
        Two intervals [S1, E1] and [S2, E2] overlap if:
          S1 <= E2 (or E2 is null) AND S2 <= E1 (or E1 is null)
        """
        stmt = select(Budget).where(
            Budget.user_id == user_id,
            Budget.category == category,
            Budget.active == True
        )
        if exclude_budget_id:
            stmt = stmt.where(Budget.id != exclude_budget_id)
            
        if end_date is not None:
            stmt = stmt.where(Budget.start_date <= end_date)
            
        stmt = stmt.where(or_(Budget.end_date == None, start_date <= Budget.end_date))
        
        result = await session.execute(stmt)
        return list(result.scalars().all())
