"""
repositories/goals_repository.py — Data access layer for Goal model.
"""
from datetime import date
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.goal import Goal


class GoalsRepository:
    @staticmethod
    async def get_goal(session: AsyncSession, goal_id: str) -> Goal | None:
        """Retrieve a specific goal by ID."""
        stmt = select(Goal).where(Goal.id == goal_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_goals(session: AsyncSession, user_id: str) -> list[Goal]:
        """List all goals belonging to a specific user."""
        stmt = select(Goal).where(Goal.user_id == user_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_goal(
        session: AsyncSession,
        user_id: str,
        goal_name: str,
        target_amount: float,
        current_amount: float,
        deadline: date | None = None,
        status: str = "active"
    ) -> Goal:
        """Create a new financial goal."""
        goal = Goal(
            user_id=user_id,
            goal_name=goal_name,
            target_amount=target_amount,
            current_amount=current_amount,
            deadline=deadline,
            status=status
        )
        session.add(goal)
        await session.flush()
        return goal

    @staticmethod
    async def delete_goal(session: AsyncSession, goal_id: str) -> None:
        """Remove a goal from the database."""
        stmt = delete(Goal).where(Goal.id == goal_id)
        await session.execute(stmt)
