"""
services/audit_service.py — Manage structured action audit trail entries.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    async def get_audit_logs(
        session: AsyncSession,
        user_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditLog]:
        """Fetch audit log items matching optional filters."""
        stmt = select(AuditLog)
        
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
            
        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        res = await session.execute(stmt)
        return list(res.scalars().all())
