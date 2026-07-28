"""
services/demo_service.py — Manage reset and reseeding of user databases.
"""
from datetime import date, timedelta
from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.notification import Notification
from app.models.import_job import ImportJob
from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


class DemoService:
    @staticmethod
    async def reset_demo_data(session: AsyncSession, user: User) -> bool:
        """
        Wipe all user-scoped records and reseed demo data.
        Enforces strict safety gates:
          1. DEMO_MODE_ENABLED is True.
          2. ENVIRONMENT != "prod".
          3. User role is "admin" OR email is "demo@finsarthi.com".
        """
        # Safety gate 1 & 2
        if not settings.DEMO_MODE_ENABLED or settings.ENVIRONMENT == "prod":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "DEMO_MODE_DISABLED",
                        "message": "Demo mode operations are not permitted in this configuration or environment."
                    }
                }
            )

        # Safety gate 3
        if user.role != "admin" and user.email != "demo@finsarthi.com":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "ACCESS_DENIED",
                        "message": "Demo reset is restricted to admin accounts or the designated demo user."
                    }
                }
            )

        # 1. Flush existing records
        await session.execute(delete(Transaction).where(Transaction.user_id == user.id))
        await session.execute(delete(Budget).where(Budget.user_id == user.id))
        await session.execute(delete(Goal).where(Goal.user_id == user.id))
        await session.execute(delete(Notification).where(Notification.user_id == user.id))
        await session.execute(delete(ImportJob).where(ImportJob.user_id == user.id))
        await session.execute(delete(AuditLog).where(AuditLog.user_id == user.id))

        # 2. Reseed records
        today = date.today()
        transactions = [
            Transaction(user_id=user.id, type="income", amount=75000.00, category="Salary", occurred_on=today - timedelta(days=30), source="demo_seed"),
            Transaction(user_id=user.id, type="income", amount=75000.00, category="Salary", occurred_on=today - timedelta(days=0), source="demo_seed"),
            Transaction(user_id=user.id, type="expense", amount=15000.00, category="Rent", occurred_on=today - timedelta(days=28), source="demo_seed"),
            Transaction(user_id=user.id, type="expense", amount=3200.00, category="Groceries", occurred_on=today - timedelta(days=25), source="demo_seed"),
            Transaction(user_id=user.id, type="expense", amount=1500.00, category="Transport", occurred_on=today - timedelta(days=22), source="demo_seed"),
            Transaction(user_id=user.id, type="expense", amount=4500.00, category="Dining", occurred_on=today - timedelta(days=18), source="demo_seed"),
            Transaction(user_id=user.id, type="expense", amount=2000.00, category="Entertainment", occurred_on=today - timedelta(days=14), source="demo_seed"),
            Transaction(user_id=user.id, type="expense", amount=800.00, category="Subscriptions", occurred_on=today - timedelta(days=10), source="demo_seed"),
            Transaction(user_id=user.id, type="expense", amount=6000.00, category="Shopping", occurred_on=today - timedelta(days=7), source="demo_seed"),
            Transaction(user_id=user.id, type="income", amount=12000.00, category="Freelance", occurred_on=today - timedelta(days=5), source="demo_seed"),
            Transaction(user_id=user.id, type="expense", amount=3500.00, category="Groceries", occurred_on=today - timedelta(days=3), source="demo_seed"),
            Transaction(user_id=user.id, type="expense", amount=1200.00, category="Transport", occurred_on=today - timedelta(days=1), source="demo_seed"),
        ]
        session.add_all(transactions)

        budgets = [
            Budget(
                user_id=user.id, category="Groceries", limit_amount=8000.00, period="monthly",
                start_date=today.replace(day=1), end_date=today.replace(day=1) + timedelta(days=30), active=True
            ),
            Budget(
                user_id=user.id, category="Dining", limit_amount=5000.00, period="monthly",
                start_date=today.replace(day=1), end_date=today.replace(day=1) + timedelta(days=30), active=True
            )
        ]
        session.add_all(budgets)

        goal = Goal(
            user_id=user.id,
            goal_name="Emergency Fund",
            target_amount=300000.00,
            current_amount=45000.00,
            deadline=today + timedelta(days=365)
        )
        session.add(goal)

        # 3. Create AuditLog event
        await AuditLogRepository.create_audit_log(
            session=session,
            user_id=user.id,
            action="demo.reset",
            before=None,
            after={
                "transactions_seeded": len(transactions),
                "budgets_seeded": len(budgets),
                "goals_seeded": 1
            }
        )

        await session.commit()
        return True
