"""
api/coach/routes.py — Single consolidated API router for Coach agent endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.coach import CoachSummaryResponseSchema
from app.services.coach_service import CoachService

router = APIRouter(prefix="/coach", tags=["Coach Agent"])


@router.get(
    "/summary",
    response_model=CoachSummaryResponseSchema
)
async def get_coach_summary(
    year: int | None = Query(None),
    month: int | None = Query(None, ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CoachSummaryResponseSchema:
    """
    Retrieve consolidated Coach Summary:
    - Adaptive state (Learning vs Active)
    - Readiness progress stats
    - Coach Score & reasoning (when Active)
    - Deterministic habit breakdown
    - Financial rule recommendations
    - AI-formatted coaching advice
    """
    return await CoachService.get_coach_summary(db, current_user.id, year, month)
