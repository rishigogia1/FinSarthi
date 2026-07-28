"""
repositories/audit_log_repository.py — Data access layer for append-only AuditLog model.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


class AuditLogRepository:
    @staticmethod
    async def create_audit_log(
        session: AsyncSession,
        user_id: str,
        action: str,
        before: dict | None = None,
        after: dict | None = None
    ) -> AuditLog:
        """Create a new append-only audit log entry."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            before=before,
            after=after
        )
        session.add(log)
        await session.flush()
        return log
