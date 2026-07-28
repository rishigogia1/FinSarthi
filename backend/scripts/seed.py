"""
scripts/seed.py — Seed database with demo data for local development and interview demos.

Usage:
    cd backend
    python -m scripts.seed

Creates one demo user with sample transactions, budgets, and a goal.
Idempotent: skips creation if the demo user already exists.
"""
import asyncio
import sys
import os
from datetime import date, timedelta

# Ensure backend root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.goal import Goal


DEMO_EMAIL = "demo@finsarthi.com"
DEMO_PASSWORD = "demo1234"
DEMO_NAME = "Demo User"


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        # Check if demo user already exists
        stmt = select(User).where(User.email == DEMO_EMAIL)
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            print(f"[OK] Demo user already exists (id={existing.id}). Skipping seed.")
            return

        # Create demo user
        user = User(
            name=DEMO_NAME,
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        session.add(user)
        await session.flush()
        uid = user.id
        print(f"[OK] Created demo user: {DEMO_EMAIL} / {DEMO_PASSWORD} (id={uid})")

        # Sample transactions
        today = date.today()
        transactions = [
            Transaction(user_id=uid, type="income", amount=75000.00, category="Salary", occurred_on=today - timedelta(days=30), source="seed"),
            Transaction(user_id=uid, type="income", amount=75000.00, category="Salary", occurred_on=today - timedelta(days=0), source="seed"),
            Transaction(user_id=uid, type="expense", amount=15000.00, category="Rent", occurred_on=today - timedelta(days=28), source="seed"),
            Transaction(user_id=uid, type="expense", amount=3200.00, category="Groceries", occurred_on=today - timedelta(days=25), source="seed"),
            Transaction(user_id=uid, type="expense", amount=1500.00, category="Transport", occurred_on=today - timedelta(days=22), source="seed"),
            Transaction(user_id=uid, type="expense", amount=4500.00, category="Dining", occurred_on=today - timedelta(days=18), source="seed"),
            Transaction(user_id=uid, type="expense", amount=2000.00, category="Entertainment", occurred_on=today - timedelta(days=14), source="seed"),
            Transaction(user_id=uid, type="expense", amount=800.00, category="Subscriptions", occurred_on=today - timedelta(days=10), source="seed"),
            Transaction(user_id=uid, type="expense", amount=6000.00, category="Shopping", occurred_on=today - timedelta(days=7), source="seed"),
            Transaction(user_id=uid, type="income", amount=12000.00, category="Freelance", occurred_on=today - timedelta(days=5), source="seed"),
            Transaction(user_id=uid, type="expense", amount=3500.00, category="Groceries", occurred_on=today - timedelta(days=3), source="seed"),
            Transaction(user_id=uid, type="expense", amount=1200.00, category="Transport", occurred_on=today - timedelta(days=1), source="seed"),
        ]
        session.add_all(transactions)
        print(f"[OK] Created {len(transactions)} sample transactions")

        # Budgets
        budgets = [
            Budget(
                user_id=uid, category="Groceries", limit_amount=8000.00, period="monthly",
                start_date=today.replace(day=1), end_date=today.replace(day=1) + timedelta(days=30), active=True,
            ),
            Budget(
                user_id=uid, category="Dining", limit_amount=5000.00, period="monthly",
                start_date=today.replace(day=1), end_date=today.replace(day=1) + timedelta(days=30), active=True,
            ),
        ]
        session.add_all(budgets)
        print(f"[OK] Created {len(budgets)} sample budgets")

        # Goal
        goal = Goal(
            user_id=uid,
            goal_name="Emergency Fund",
            target_amount=300000.00,
            current_amount=45000.00,
            deadline=today + timedelta(days=365),
        )
        session.add(goal)
        print("[OK] Created 1 sample goal")

        await session.commit()
        print("\n" + "=" * 50)
        print("Seed complete!")
        print(f"  Email:    {DEMO_EMAIL}")
        print(f"  Password: {DEMO_PASSWORD}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
