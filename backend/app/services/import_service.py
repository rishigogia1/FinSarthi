"""
services/import_service.py — Coordinates CSV transaction ingestion and status transitions.

Applies file size/rows checks, transient preview storage, and confirms transactions writes.
"""
import os
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.import_job import ImportJob
from app.models.transaction import Transaction
from app.services.csv_parser_service import CSVParserService
from app.services.transaction_normalizer_service import TransactionNormalizerService
from app.services.deduplication_service import DeduplicationService
from app.repositories.audit_log_repository import AuditLogRepository

logger = logging.getLogger(__name__)


class ImportServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ImportService:
    TEMP_DIR = "temp_imports"

    @staticmethod
    def _get_temp_filepath(job_id: str) -> str:
        os.makedirs(ImportService.TEMP_DIR, exist_ok=True)
        return os.path.join(ImportService.TEMP_DIR, f"{job_id}.csv")

    @staticmethod
    def _cleanup_temp_file(job_id: str) -> None:
        path = ImportService._get_temp_filepath(job_id)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                logger.warning("Failed to remove temp file %s: %s", path, e)

    @staticmethod
    async def get_job_by_id(session: AsyncSession, user_id: str, job_id: str) -> ImportJob:
        """Fetch import job verifying ownership."""
        stmt = select(ImportJob).where(ImportJob.id == job_id, ImportJob.user_id == user_id)
        res = await session.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise ImportServiceError("JOB_NOT_FOUND", "Import job not found or foreign-owned.", status_code=404)
        return job

    @staticmethod
    async def create_import_job(
        session: AsyncSession,
        user_id: str,
        filename: str,
        file_content: str
    ) -> ImportJob:
        """Parse raw CSV, detect duplicates, cache preview rows, and save to DB."""
        # 1. Enforce file size check (1MB = 1048576 bytes)
        file_size_mb = len(file_content.encode("utf-8")) / (1024 * 1024)
        if file_size_mb > settings.MAX_IMPORT_FILE_SIZE_MB:
            raise ImportServiceError(
                "FILE_TOO_LARGE",
                f"File size exceeds maximum allowed of {settings.MAX_IMPORT_FILE_SIZE_MB}MB.",
                status_code=413
            )
            
        # Parse CSV rows
        parsed_rows, parse_errors = CSVParserService.parse_csv_data(file_content)
        
        job = ImportJob(
            user_id=user_id,
            filename=filename,
            status="uploaded"
        )
        session.add(job)
        await session.flush()
        
        # Save temporary file on disk for transient validation lookup
        temp_path = ImportService._get_temp_filepath(job.id)
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(file_content)
            
        if not parsed_rows and parse_errors and parse_errors[0]["row"] == 0:
            # Missing header error
            job.status = "failed"
            job.error_summary = parse_errors[0]["message"]
            await session.commit()
            ImportService._cleanup_temp_file(job.id)
            return job
            
        # Flag duplicates
        row_evaluations = await DeduplicationService.flag_duplicates(session, user_id, parsed_rows)
        
        # Calculate counts
        total = len(parsed_rows) + len(parse_errors)
        duplicates = sum(1 for r in row_evaluations if r["status"] == "duplicate")
        rejected = len(parse_errors)
        accepted = len(parsed_rows) - duplicates
        
        job.total_rows = total
        job.accepted_rows = accepted
        job.duplicate_rows = duplicates
        job.rejected_rows = rejected
        
        if parse_errors:
            job.error_summary = f"Ingestion has {len(parse_errors)} row errors."
            
        # Capped preview payload
        preview_capped = row_evaluations[:settings.IMPORT_PREVIEW_ROW_LIMIT]
        job.raw_data = {"preview": preview_capped}
        
        if accepted > 0:
            job.status = "parsed"
        else:
            job.status = "failed"
            if not job.error_summary:
                job.error_summary = "All uploaded transaction rows are flagged duplicates."
            ImportService._cleanup_temp_file(job.id)
            
        await session.commit()
        return job

    @staticmethod
    async def confirm_import(
        session: AsyncSession,
        user_id: str,
        job_id: str
    ) -> ImportJob:
        """Write all accepted non-duplicate rows of the job into transactions."""
        job = await ImportService.get_job_by_id(session, user_id, job_id)
        
        if job.status != "parsed":
            raise ImportServiceError(
                "INVALID_STATUS_TRANSITION",
                f"Cannot confirm job with status '{job.status}'. Must be 'parsed'.",
                status_code=409
            )
            
        temp_path = ImportService._get_temp_filepath(job.id)
        if not os.path.exists(temp_path):
            raise ImportServiceError(
                "TEMP_FILE_MISSING",
                "Transient CSV import file has expired or was removed.",
                status_code=500
            )
            
        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        parsed_rows, _ = CSVParserService.parse_csv_data(content)
        row_evaluations = await DeduplicationService.flag_duplicates(session, user_id, parsed_rows)
        
        created_count = 0
        inserted_txs_meta = []
        for eval_row in row_evaluations:
            if eval_row["status"] == "accepted":
                normalized = TransactionNormalizerService.normalize_row_data(eval_row["normalized_row"])
                
                tx = Transaction(
                    user_id=user_id,
                    type=normalized["type"],
                    amount=normalized["amount"],
                    category=normalized["category"],
                    occurred_on=normalized["occurred_on"],
                    note=normalized["note"],
                    source=normalized["source"]
                )
                session.add(tx)
                created_count += 1
                inserted_txs_meta.append({
                    "category": tx.category,
                    "amount": tx.amount,
                    "type": tx.type,
                    "occurred_on": str(tx.occurred_on)
                })
                
        job.status = "confirmed"
        job.updated_at = datetime.utcnow()
        
        # Log Audit event
        await AuditLogRepository.create_audit_log(
            session=session,
            user_id=user_id,
            action="import.confirmed",
            before=None,
            after={
                "job_id": job.id,
                "filename": job.filename,
                "inserted_count": created_count,
                "transactions": inserted_txs_meta
            }
        )
        
        await session.commit()
        ImportService._cleanup_temp_file(job.id)
        return job

    @staticmethod
    async def cancel_import(
        session: AsyncSession,
        user_id: str,
        job_id: str
    ) -> ImportJob:
        """Cancel the pending transaction import job."""
        job = await ImportService.get_job_by_id(session, user_id, job_id)
        
        if job.status != "parsed":
            raise ImportServiceError(
                "INVALID_STATUS_TRANSITION",
                f"Cannot cancel job with status '{job.status}'. Must be 'parsed'.",
                status_code=409
            )
            
        job.status = "cancelled"
        job.updated_at = datetime.utcnow()
        await session.commit()
        
        ImportService._cleanup_temp_file(job.id)
        return job
