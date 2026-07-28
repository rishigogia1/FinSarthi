"""
services/export_service.py — Service compiling database records into CSV downloads.
"""
import os
import csv
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.goal import Goal
from app.services.insight_service import InsightService

logger = logging.getLogger(__name__)


class ExportService:
    TEMP_DIR = "temp_exports"

    @staticmethod
    def _ensure_temp_dir() -> str:
        os.makedirs(ExportService.TEMP_DIR, exist_ok=True)
        return ExportService.TEMP_DIR

    @staticmethod
    async def export_transactions_csv(session: AsyncSession, user_id: str) -> str:
        """Query user transactions up to max limit and write to a temp CSV file."""
        ExportService._ensure_temp_dir()
        filename = f"export_{user_id}_transactions_{int(datetime.utcnow().timestamp())}.csv"
        filepath = os.path.join(ExportService.TEMP_DIR, filename)

        stmt = select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.occurred_on.desc()).limit(settings.MAX_EXPORT_ROWS)
        res = await session.execute(stmt)
        txs = res.scalars().all()

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Type", "Amount", "Category", "Note", "Source"])
            for tx in txs:
                writer.writerow([
                    str(tx.occurred_on),
                    tx.type,
                    str(tx.amount),
                    tx.category,
                    tx.note or "",
                    tx.source or "manual"
                ])

        return filepath

    @staticmethod
    async def export_budgets_csv(session: AsyncSession, user_id: str) -> str:
        """Query user budgets up to max limit and write to a temp CSV file."""
        ExportService._ensure_temp_dir()
        filename = f"export_{user_id}_budgets_{int(datetime.utcnow().timestamp())}.csv"
        filepath = os.path.join(ExportService.TEMP_DIR, filename)

        stmt = select(Budget).where(Budget.user_id == user_id).order_by(Budget.created_at.desc()).limit(settings.MAX_EXPORT_ROWS)
        res = await session.execute(stmt)
        budgets = res.scalars().all()

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Limit Amount", "Period", "Start Date", "End Date", "Active"])
            for b in budgets:
                writer.writerow([
                    b.category,
                    str(b.limit_amount),
                    b.period,
                    str(b.start_date),
                    str(b.end_date),
                    "true" if b.active else "false"
                ])

        return filepath

    @staticmethod
    async def export_goals_csv(session: AsyncSession, user_id: str) -> str:
        """Query user goals up to max limit and write to a temp CSV file."""
        ExportService._ensure_temp_dir()
        filename = f"export_{user_id}_goals_{int(datetime.utcnow().timestamp())}.csv"
        filepath = os.path.join(ExportService.TEMP_DIR, filename)

        stmt = select(Goal).where(Goal.user_id == user_id).limit(settings.MAX_EXPORT_ROWS)
        res = await session.execute(stmt)
        goals = res.scalars().all()

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Goal Name", "Target Amount", "Current Amount", "Deadline", "Status"])
            for g in goals:
                writer.writerow([
                    g.goal_name,
                    str(g.target_amount),
                    str(g.current_amount),
                    str(g.deadline) if g.deadline else "",
                    g.status
                ])

        return filepath

    @staticmethod
    async def export_insights_csv(session: AsyncSession, user_id: str) -> str:
        """Query user insights and compile into CSV download."""
        ExportService._ensure_temp_dir()
        filename = f"export_{user_id}_insights_{int(datetime.utcnow().timestamp())}.csv"
        filepath = os.path.join(ExportService.TEMP_DIR, filename)

        insights = await InsightService.get_structured_insights(session, user_id)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Message", "Type", "Severity", "Confidence"])
            for ins in insights:
                writer.writerow([
                    ins.title,
                    ins.message or "",
                    ins.type,
                    ins.severity,
                    str(ins.confidence)
                ])

        return filepath
