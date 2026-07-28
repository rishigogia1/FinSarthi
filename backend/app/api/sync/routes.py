"""
api/sync/routes.py — Experimental/mock endpoints for external bank integrations.

All routes require bearer JWT guards.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.sync import (
    SyncConnectRequest,
    SyncAccountResponse,
    SyncJobResponse
)
from app.services.sync_connector_service import SyncConnectorService

router = APIRouter(prefix="/sync", tags=["External Bank Sync (Experimental Stub)"])


@router.post(
    "/connect",
    status_code=status.HTTP_200_OK
)
async def connect_sync_provider(
    payload: SyncConnectRequest,
    current_user: User = Depends(get_current_user)
) -> dict:
    """[EXPERIMENTAL STUB] Establish authorization link with external fintech aggregators."""
    return await SyncConnectorService.connect_external_provider(payload)


@router.get(
    "/accounts",
    response_model=list[SyncAccountResponse]
)
async def get_sync_accounts(
    current_user: User = Depends(get_current_user)
) -> list[SyncAccountResponse]:
    """[EXPERIMENTAL STUB] List mock linked external bank accounts."""
    return await SyncConnectorService.get_external_accounts(current_user.id)


@router.post(
    "/jobs/{account_id}/run",
    response_model=SyncJobResponse
)
async def run_account_sync_job(
    account_id: str,
    current_user: User = Depends(get_current_user)
) -> SyncJobResponse:
    """[EXPERIMENTAL STUB] Trigger a mock sync pipeline synchronization attempt."""
    return await SyncConnectorService.trigger_sync_job(current_user.id, account_id)


@router.get(
    "/jobs/{job_id}",
    response_model=SyncJobResponse
)
async def get_sync_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
) -> SyncJobResponse:
    """[EXPERIMENTAL STUB] Query execution status of bank synchronization jobs."""
    if job_id != "job_mock_123":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SYNC_JOB_NOT_FOUND",
                    "message": f"Sync job '{job_id}' not found."
                }
            }
        )
    return SyncJobResponse(
        job_id="job_mock_123",
        status="completed",
        sync_count=0
    )
