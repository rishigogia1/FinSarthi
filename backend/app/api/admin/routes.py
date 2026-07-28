"""
api/admin/routes.py — Router for administration context read-only controls.

Gated to users possessing the 'admin' role. Raises HTTP 403 Forbidden otherwise.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.admin import (
    AdminUserListResponse,
    SystemAuditLogResponse,
    SystemSummaryResponse
)
from app.services.admin_service import AdminService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["Admin Controls"])


def enforce_admin_privileges(user: User = Depends(get_current_user)) -> None:
    """Dependency guard verifying admin role."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "ACCESS_DENIED",
                    "message": "Administration privileges are required to access this resource."
                }
            }
        )


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    dependencies=[Depends(enforce_admin_privileges)]
)
async def list_users(
    db: AsyncSession = Depends(get_db)
) -> AdminUserListResponse:
    """List registration metadata and transaction counts across all user accounts."""
    summaries = await AdminService.list_users_summaries(db)
    return AdminUserListResponse(users=summaries)


@router.get(
    "/audit-logs",
    response_model=SystemAuditLogResponse,
    dependencies=[Depends(enforce_admin_privileges)]
)
async def list_audit_logs(
    user_id: str | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> SystemAuditLogResponse:
    """List system audit log action records."""
    logs = await AuditService.get_audit_logs(db, user_id=user_id, action=action, limit=limit, offset=offset)
    return SystemAuditLogResponse(logs=logs)


@router.get(
    "/system-summary",
    response_model=SystemSummaryResponse,
    dependencies=[Depends(enforce_admin_privileges)]
)
async def get_system_summary(
    db: AsyncSession = Depends(get_db)
) -> SystemSummaryResponse:
    """Query live count aggregates and service pings for Postgres and Redis."""
    return await AdminService.get_system_summary(db)
