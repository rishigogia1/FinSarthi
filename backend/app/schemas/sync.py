"""
schemas/sync.py — Experimental/mock external account synchronization schemas.
"""
from pydantic import BaseModel


class SyncConnectRequest(BaseModel):
    provider: str
    credentials: dict


class SyncAccountResponse(BaseModel):
    account_id: str
    account_name: str
    balance: float
    currency: str = "INR"


class SyncJobResponse(BaseModel):
    job_id: str
    status: str  # "completed", "failed"
    sync_count: int
    error_message: str | None = None
