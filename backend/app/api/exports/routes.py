"""
api/exports/routes.py — Router compiling and serving database reports as CSV files.

Gated behind JWT authorization. Returns standard synchronous FileResponse downloads.
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.export_service import ExportService
from app.repositories.audit_log_repository import AuditLogRepository

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.get(
    "/transactions",
    response_class=FileResponse
)
async def export_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """Generate and download a CSV file containing all user transactions."""
    try:
        path = await ExportService.export_transactions_csv(db, current_user.id)
        if not os.path.exists(path):
            raise HTTPException(status_code=500, detail="Failed to compile CSV export file.")

        # Log audit trail event
        await AuditLogRepository.create_audit_log(
            session=db,
            user_id=current_user.id,
            action="export.transactions",
            before=None,
            after={"filename": os.path.basename(path)}
        )
        await db.commit()

        return FileResponse(
            path=path,
            filename=os.path.basename(path),
            media_type="text/csv"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate transactions report: {str(e)}"
        )


@router.get(
    "/budgets",
    response_class=FileResponse
)
async def export_budgets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """Generate and download a CSV file containing all active user budgets."""
    try:
        path = await ExportService.export_budgets_csv(db, current_user.id)
        if not os.path.exists(path):
            raise HTTPException(status_code=500, detail="Failed to compile CSV export file.")

        await AuditLogRepository.create_audit_log(
            session=db,
            user_id=current_user.id,
            action="export.budgets",
            before=None,
            after={"filename": os.path.basename(path)}
        )
        await db.commit()

        return FileResponse(
            path=path,
            filename=os.path.basename(path),
            media_type="text/csv"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate budgets report: {str(e)}"
        )


@router.get(
    "/goals",
    response_class=FileResponse
)
async def export_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """Generate and download a CSV file containing all active user goals."""
    try:
        path = await ExportService.export_goals_csv(db, current_user.id)
        if not os.path.exists(path):
            raise HTTPException(status_code=500, detail="Failed to compile CSV export file.")

        await AuditLogRepository.create_audit_log(
            session=db,
            user_id=current_user.id,
            action="export.goals",
            before=None,
            after={"filename": os.path.basename(path)}
        )
        await db.commit()

        return FileResponse(
            path=path,
            filename=os.path.basename(path),
            media_type="text/csv"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate goals report: {str(e)}"
        )


@router.get(
    "/insights",
    response_class=FileResponse
)
async def export_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """Generate and download a CSV file containing all compiled user insights."""
    try:
        path = await ExportService.export_insights_csv(db, current_user.id)
        if not os.path.exists(path):
            raise HTTPException(status_code=500, detail="Failed to compile CSV export file.")

        await AuditLogRepository.create_audit_log(
            session=db,
            user_id=current_user.id,
            action="export.insights",
            before=None,
            after={"filename": os.path.basename(path)}
        )
        await db.commit()

        return FileResponse(
            path=path,
            filename=os.path.basename(path),
            media_type="text/csv"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights report: {str(e)}"
        )
