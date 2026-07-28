"""
api/demo/routes.py — Router triggering showcase reset/reseeding routines.

Protected by Bearer JWT authorization. Gated strictly by environment/config checks.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.demo_service import DemoService

router = APIRouter(prefix="/demo", tags=["Demo Mode & Reseeding"])


@router.post(
    "/reset",
    status_code=200
)
async def reset_demo(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Wipe all active user transactions/budgets/goals and reseed with clean demo data."""
    await DemoService.reset_demo_data(db, current_user)
    return {
        "success": True,
        "message": "Demo data wiped and successfully reseeded."
    }


@router.get(
    "/status",
    status_code=200
)
async def get_demo_status() -> dict:
    """Return status of demo capabilities settings."""
    return {
        "demo_mode_enabled": settings.DEMO_MODE_ENABLED,
        "environment": settings.ENVIRONMENT
    }
