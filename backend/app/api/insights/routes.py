"""
api/insights/routes.py — Router for historical analytics, future forecasting, and AI insight endpoints.

Protected by Bearer JWT authorization.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import settings
from app.core.rate_limit import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.analytics import (
    OverviewAnalyticsResponse,
    CategoryTrendResponse,
    BudgetHealthResponse,
    GoalHealthResponse
)
from app.schemas.forecasts import (
    MonthlyCashflowForecastResponse,
    BudgetRiskForecastResponse,
    GoalProjectionResponse
)
from app.schemas.insights import InsightResponse, InsightListResponse
from app.schemas.recommendations import (
    RecommendationResponse,
    RecommendationListResponse,
    InsightFeedbackRequest
)
from app.schemas.summaries import MonthlyCashflowPoint
from app.services.analytics_service import AnalyticsService
from app.services.goal_health_service import GoalHealthService
from app.services.forecasting_service import ForecastingService
from app.services.insight_service import InsightService
from app.services.ai_explanation_service import AIExplanationService
from app.services.summary_service import SummaryService
from app.services.transaction_service import FinanceServiceError

router = APIRouter(prefix="/insights", tags=["Analytics, Forecasting & Insights"])


def raise_http_exception(e: FinanceServiceError) -> None:
    raise HTTPException(
        status_code=e.status_code,
        detail={
            "error": {
                "code": e.code,
                "message": e.message
            }
        }
    )


# ---------------------------------------------------------------------------
# Core Analytics
# ---------------------------------------------------------------------------
@router.get(
    "/overview",
    response_model=OverviewAnalyticsResponse
)
async def get_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> OverviewAnalyticsResponse:
    """Get calculated historical metrics (totals and savings rate)."""
    return await AnalyticsService.get_overview(db, current_user.id)


@router.get(
    "/spending-trends",
    response_model=CategoryTrendResponse
)
async def get_spending_trends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CategoryTrendResponse:
    """Get category-wise allocations breakdown."""
    return await AnalyticsService.get_spending_trends(db, current_user.id)


@router.get(
    "/income-expense-trends",
    response_model=list[MonthlyCashflowPoint]
)
async def get_income_expense_trends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[MonthlyCashflowPoint]:
    """Get chronological monthly income/expense trends data points."""
    return await SummaryService.get_monthly_cashflow(db, current_user.id)


@router.get(
    "/budget-health",
    response_model=list[BudgetHealthResponse]
)
async def get_budget_health(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[BudgetHealthResponse]:
    """Get utilization status on active user budgets."""
    return await AnalyticsService.get_budget_health(db, current_user.id)


@router.get(
    "/goal-health",
    response_model=list[GoalHealthResponse]
)
async def get_goal_health(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[GoalHealthResponse]:
    """Get savings pace progress evaluations on user goals."""
    return await GoalHealthService.get_goals_health(db, current_user.id)


# ---------------------------------------------------------------------------
# Forecasting
# ---------------------------------------------------------------------------
@router.get(
    "/forecast/monthly-cashflow",
    response_model=MonthlyCashflowForecastResponse
)
async def forecast_monthly_cashflow(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MonthlyCashflowForecastResponse:
    """Forecast next month cashflow details."""
    return await ForecastingService.forecast_monthly_cashflow(db, current_user.id)


@router.get(
    "/forecast/budget-risk",
    response_model=list[BudgetRiskForecastResponse]
)
async def forecast_budget_risk(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[BudgetRiskForecastResponse]:
    """Project next-month overspending risk on budgets."""
    return await ForecastingService.forecast_budget_risk(db, current_user.id)


@router.get(
    "/forecast/goal-projection",
    response_model=list[GoalProjectionResponse]
)
async def forecast_goal_projection(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[GoalProjectionResponse]:
    """Estimate goal completion dates chronologically."""
    return await ForecastingService.forecast_goal_projection(db, current_user.id)


# ---------------------------------------------------------------------------
# Insight Delivery
# ---------------------------------------------------------------------------
# Rate limiter: 20 recommendation requests per 15 minutes per IP
recommendations_limiter = RateLimiter(
    "insight_recommendations",
    settings.RATE_LIMIT_INSIGHT_RECOMMENDATIONS,
    settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
)

@router.get(
    "/recommendations",
    response_model=RecommendationListResponse,
    dependencies=[Depends(recommendations_limiter)],
)
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RecommendationListResponse:
    """Get prioritized actionable suggested recomendations."""
    insights = await InsightService.get_structured_insights(db, current_user.id)
    
    recommendations = []
    for insight in insights:
        if insight.type == "budget_alert":
            recommendations.append(
                RecommendationResponse(
                    title=f"Adjust Budget: {insight.evidence.get('category')}",
                    description=f"Your expenses are high. Consider review of recent purchases and defer discretionary spending.",
                    type="budget",
                    priority="high"
                )
            )
        elif insight.type == "goal_warning":
            recommendations.append(
                RecommendationResponse(
                    title="Optimize Goal Savings",
                    description=f"Your savings speed is below target. You can push the target date out or increase monthly contribution.",
                    type="goal",
                    priority="medium"
                )
            )
            
    # Standard baseline recommendations if none generated
    if not recommendations:
        recommendations.append(
            RecommendationResponse(
                title="Establish Emergency Fund",
                description="Save at least 3 months of expenses for buffer coverages.",
                type="general",
                priority="medium"
            )
        )
        
    return RecommendationListResponse(recommendations=recommendations)


@router.get(
    "/highlights",
    response_model=InsightListResponse
)
async def get_highlights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> InsightListResponse:
    """Get active severity-ranked highlights with AI-enriched descriptions."""
    insights = await InsightService.get_structured_insights(db, current_user.id)
    
    enriched_insights = []
    for insight in insights:
        # Enrich the structured message using our AI Explanation service
        ai_message = await AIExplanationService.generate_explanation(db, current_user.id, insight)
        
        enriched_insights.append(
            InsightResponse(
                title=insight.title,
                message=ai_message,
                type=insight.type,
                severity=insight.severity,
                confidence=insight.confidence,
                evidence=insight.evidence,
                action_hint=insight.action_hint
            )
        )
        
    return InsightListResponse(insights=enriched_insights)


@router.get(
    "/anomalies",
    response_model=InsightListResponse
)
async def get_anomalies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> InsightListResponse:
    """Query warnings anomalies (type budget_alert or goal_warning)."""
    insights = await InsightService.get_structured_insights(db, current_user.id)
    
    anomalies = [i for i in insights if i.type in ("budget_alert", "goal_warning")]
    
    enriched = []
    for insight in anomalies:
        ai_message = await AIExplanationService.generate_explanation(db, current_user.id, insight)
        enriched.append(
            InsightResponse(
                title=insight.title,
                message=ai_message,
                type=insight.type,
                severity=insight.severity,
                confidence=insight.confidence,
                evidence=insight.evidence,
                action_hint=insight.action_hint
            )
        )
        
    return InsightListResponse(insights=enriched)


# ---------------------------------------------------------------------------
# Feedback Callback
# ---------------------------------------------------------------------------
@router.post(
    "/feedback",
    status_code=200
)
async def log_insight_feedback(
    payload: InsightFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Log user feedback on insight recommendations in the audit table."""
    feedback_data = {
        "insight_title": payload.insight_title,
        "score": payload.feedback_score,
        "comments": payload.comments
    }
    
    # Store feedback in the append-only AuditLog
    await AuditLogRepository.create_audit_log(
        session=db,
        user_id=current_user.id,
        action="insight.feedback_logged",
        before=None,
        after=feedback_data
    )
    await db.commit()
    
    return {"success": True}
