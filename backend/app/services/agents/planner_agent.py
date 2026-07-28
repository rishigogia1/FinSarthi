from datetime import datetime, timezone
from app.services.agents.base_agent import BaseAgent
from app.services.agents.registry import AgentRegistry
from app.schemas.dashboard import AgentDashboardResponse
from app.schemas.dashboard_context import AgentContext
from app.services.planner_analytics_service import PlannerAnalyticsService

class PlannerAgent(BaseAgent):
    async def generate(self, context: AgentContext) -> AgentDashboardResponse:
        agent_id = "planner"
        name = "Planner"
        role = "Budget & Goals"
        desc = "Planner analyzes your real transaction data to calculate monthly spending, income, net cashflow, and top category breakdown."
        
        # 1. Safely retrieve or compute Planner analytics summary
        if getattr(context, "planner_summary", None) is not None:
            summary = context.planner_summary
        elif getattr(context, "session", None) is not None:
            summary = await PlannerAnalyticsService.get_planner_summary(context.session, context.user.id)
        else:
            # Fallback mock summary if neither session nor summary is supplied
            from app.schemas.planner import (
                PlannerSummaryResponseSchema, PlannerOverviewSchema,
                PlannerCategoryAggregateSchema, PlannerActivitySchema, PlannerAnalyticsMetricsSchema
            )
            summary = PlannerSummaryResponseSchema(
                overview=PlannerOverviewSchema(monthly_expense=0.0, monthly_income=0.0, net_cashflow=0.0, savings_rate=0.0),
                categories=[],
                activity=PlannerActivitySchema(today_count=0, latest_category=None, last_transaction_amount=None, last_transaction_type=None),
                analytics=PlannerAnalyticsMetricsSchema(avg_daily_spend=0.0, weekly_spend=0.0, largest_category=None, largest_category_amount=0.0, total_transactions=0),
                generated_at=datetime.now(timezone.utc)
            )
        
        # 2. Build requirements checklist
        requirements = [
            {"name": "Authentication", "met": True},
            {"name": "User Profile", "met": True},
            {"name": "Transactions", "met": True},
            {"name": "Planner Engine", "met": True},
        ]
        
        # 3. Assemble metrics
        metrics = {
            "monthlyExpense": summary.overview.monthly_expense,
            "monthlyIncome": summary.overview.monthly_income,
            "netCashflow": summary.overview.net_cashflow,
            "savingsRate": summary.overview.savings_rate,
            "largestCategory": summary.analytics.largest_category or "None",
            "largestCategoryAmount": summary.analytics.largest_category_amount,
            "totalTransactions": summary.analytics.total_transactions,
            "avgDailySpend": summary.analytics.avg_daily_spend,
            "weeklySpend": summary.analytics.weekly_spend,
        }
        
        # 4. Concise activities summary
        activities = []
        if summary.activity.today_count > 0:
            activities.append(f"{summary.activity.today_count} expense(s) recorded today")
        else:
            activities.append("No transactions recorded today")
            
        if summary.activity.latest_category:
            amt_fmt = f"₹{summary.activity.last_transaction_amount:,.2f}".replace(".00", "")
            activities.append(f"Latest category: {summary.activity.latest_category} ({amt_fmt})")
            
        if summary.analytics.largest_category:
            top_fmt = f"₹{summary.analytics.largest_category_amount:,.2f}".replace(".00", "")
            activities.append(f"Top spend category: {summary.analytics.largest_category} ({top_fmt})")

        return AgentDashboardResponse(
            id=agent_id,
            name=name,
            role=role,
            description=desc,
            implementation_status="Active",
            current_phase="V2",
            requirements=requirements,
            metrics=metrics,
            recommendations=[],
            activities=activities,
            actions=[],
            last_updated=summary.generated_at
        )

# Register the agent
AgentRegistry.register(PlannerAgent)
