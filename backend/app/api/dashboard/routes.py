from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.dashboard import TeamDashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["AI Team Dashboard"])

@router.get("/team", response_model=TeamDashboardResponse)
async def get_team_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TeamDashboardResponse:
    """
    Retrieve the dynamic AI Team Dashboard.
    Executes multiple agents in parallel to fetch metrics and insights.
    """
    return await DashboardService.get_team_dashboard(db, current_user)
