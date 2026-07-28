"""
api/imports/routes.py — CRUD endpoints managing CSV transaction ingestion jobs.

All routes require bearer JWT authorization guards.
Import upload is rate-limited. Import confirm supports idempotency keys.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user
from app.core.rate_limit import RateLimiter
from app.core.idempotency import check_idempotency_key, mark_idempotency_key_used
from app.core.metrics import metrics
from app.models.user import User
from app.schemas.imports import (
    ImportJobResponse,
    ImportPreviewResponse,
    ImportConfirmResponse
)
from app.services.import_service import ImportService, ImportServiceError

router = APIRouter(prefix="/imports", tags=["Imports"])

# Rate limiter: 10 CSV uploads per 15 minutes per IP
import_upload_limiter = RateLimiter(
    "import_upload",
    settings.RATE_LIMIT_IMPORT_UPLOAD,
    settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
)


def raise_http_exception(e: ImportServiceError) -> None:
    from app.core.middleware import request_id_ctx
    raise HTTPException(
        status_code=e.status_code,
        detail={
            "error": {
                "code": e.code,
                "message": e.message,
                "request_id": request_id_ctx.get(""),
            }
        }
    )


@router.post(
    "/transactions/csv",
    response_model=ImportJobResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(import_upload_limiter)],
)
async def upload_transactions_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ImportJobResponse:
    """Upload transactions CSV and trigger parsed validations."""
    metrics.inc("requests_total", {"endpoint": "import_upload"})
    try:
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "INVALID_FILE_ENCODING",
                    "message": "Failed to decode CSV file as UTF-8."
                }
            }
        )
        
    try:
        job = await ImportService.create_import_job(
            session=db,
            user_id=current_user.id,
            filename=file.filename or "unknown.csv",
            file_content=content
        )
        return job
    except ImportServiceError as e:
        raise_http_exception(e)


@router.get(
    "/jobs/{job_id}",
    response_model=ImportJobResponse
)
async def get_import_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ImportJobResponse:
    """Fetch status on the ingestion job."""
    try:
        return await ImportService.get_job_by_id(db, current_user.id, job_id)
    except ImportServiceError as e:
        raise_http_exception(e)


@router.get(
    "/jobs/{job_id}/preview",
    response_model=ImportPreviewResponse
)
async def get_import_job_preview(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ImportPreviewResponse:
    """Retrieve normalized preview rows and potential duplicate flags."""
    try:
        job = await ImportService.get_job_by_id(db, current_user.id, job_id)
        if job.status not in ("parsed", "confirmed", "cancelled"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "PREVIEW_UNAVAILABLE",
                        "message": f"Ingestion preview is not available for job status '{job.status}'."
                    }
                }
            )
            
        preview_data = job.raw_data or {}
        preview_rows = preview_data.get("preview", [])
        
        return ImportPreviewResponse(
            job_id=job.id,
            status=job.status,
            total_rows=job.total_rows,
            preview_rows=preview_rows
        )
    except ImportServiceError as e:
        raise_http_exception(e)


@router.post(
    "/jobs/{job_id}/confirm",
    response_model=ImportConfirmResponse
)
async def confirm_import_job(
    job_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ImportConfirmResponse:
    """
    Write accepted preview rows into the user transactions history.

    Supports Idempotency-Key header: if the same key is sent twice,
    returns the current persisted job state instead of re-executing.
    """
    metrics.inc("requests_total", {"endpoint": "import_confirm"})

    idem_key = check_idempotency_key(request)

    if idem_key:
        is_new = mark_idempotency_key_used(idem_key, job_id)
        if not is_new:
            # Duplicate request — return current persisted job state
            try:
                job = await ImportService.get_job_by_id(db, current_user.id, job_id)
                return ImportConfirmResponse(
                    job_id=job.id,
                    status=job.status,
                    created_count=job.accepted_rows if job.status == "confirmed" else 0,
                )
            except ImportServiceError as e:
                raise_http_exception(e)

    try:
        job = await ImportService.confirm_import(db, current_user.id, job_id)
        return ImportConfirmResponse(
            job_id=job.id,
            status=job.status,
            created_count=job.accepted_rows
        )
    except ImportServiceError as e:
        raise_http_exception(e)


@router.post(
    "/jobs/{job_id}/cancel",
    response_model=ImportJobResponse
)
async def cancel_import_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ImportJobResponse:
    """Discard raw transient preview structures and close ingestion job."""
    try:
        return await ImportService.cancel_import(db, current_user.id, job_id)
    except ImportServiceError as e:
        raise_http_exception(e)
