"""
schemas/imports.py — Request/Response models for parsing and tracking CSV file imports.
"""
from typing import Literal
from pydantic import BaseModel


class ImportJobResponse(BaseModel):
    id: str
    filename: str
    status: str  # "uploaded", "parsed", "confirmed", "failed", "cancelled"
    total_rows: int
    accepted_rows: int
    duplicate_rows: int
    rejected_rows: int


class ImportRowResult(BaseModel):
    row_index: int
    status: Literal["accepted", "duplicate", "rejected"]
    errors: list[str] | None = None
    normalized_row: dict | None = None  # Key-values representing mapped fields


class ImportPreviewResponse(BaseModel):
    job_id: str
    status: str
    total_rows: int
    preview_rows: list[ImportRowResult]


class ImportConfirmResponse(BaseModel):
    job_id: str
    status: str
    created_count: int
