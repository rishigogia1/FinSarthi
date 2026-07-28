"""
services/sync_connector_service.py — Stub provider interface for bank sync connectors.

Returns structured mock account details for experimental Phase 9 sandboxing.
"""
from app.schemas.sync import (
    SyncConnectRequest,
    SyncAccountResponse,
    SyncJobResponse
)


class SyncConnectorService:
    @staticmethod
    async def connect_external_provider(payload: SyncConnectRequest) -> dict:
        """Mock connection setup to standard API bank providers."""
        return {
            "success": True,
            "provider": payload.provider,
            "message": "Connection established successfully (experimental stub mode)."
        }

    @staticmethod
    async def get_external_accounts(user_id: str) -> list[SyncAccountResponse]:
        """Fetch mock bank accounts."""
        return [
            SyncAccountResponse(
                account_id="acc_mock_01",
                account_name="HDFC Checking Account",
                balance=145000.50,
                currency="INR"
            ),
            SyncAccountResponse(
                account_id="acc_mock_02",
                account_name="ICICI Savings account",
                balance=4200.75,
                currency="INR"
            )
        ]

    @staticmethod
    async def trigger_sync_job(user_id: str, account_id: str) -> SyncJobResponse:
        """Simulate a mock sync synchronization pipeline returning jobs metadata."""
        if account_id not in ("acc_mock_01", "acc_mock_02"):
            return SyncJobResponse(
                job_id="job_failed_999",
                status="failed",
                sync_count=0,
                error_message="Unknown external account identifier."
            )
            
        return SyncJobResponse(
            job_id="job_mock_123",
            status="completed",
            sync_count=0  # mock runs successfully but skips inserting to keep data consistent
        )
