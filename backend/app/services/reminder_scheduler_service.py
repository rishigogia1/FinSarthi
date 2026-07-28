"""
services/reminder_scheduler_service.py — Evaluates metrics trends and sets triggers.

Evaluates budget limits near 90% and upcoming goal deadlines (within lookahead period).
"""
import logging
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.services.analytics_service import AnalyticsService
from app.services.goal_health_service import GoalHealthService
from app.services.notification_service import NotificationService
from app.services.delivery_service import DeliveryService

logger = logging.getLogger(__name__)


class ReminderSchedulerService:
    @staticmethod
    async def check_and_schedule_reminders(
        session: AsyncSession,
        user_id: str
    ) -> int:
        """
        Scan user budgets and goals, generating alert notifications for due items.
        Returns:
            Count of newly created notifications.
        """
        created_count = 0
        
        # 1. Budget threshold checks
        budget_health = await AnalyticsService.get_budget_health(session, user_id)
        for b in budget_health:
            if b.usage_percentage >= 90.0:
                # Check for existing similar unread notification
                stmt = select(Notification).where(
                    Notification.user_id == user_id,
                    Notification.type == "budget_limit",
                    Notification.read == False,
                    Notification.title.like(f"%{b.category}%")
                )
                res = await session.execute(stmt)
                exists = res.scalars().all()
                if not exists:
                    # Create notification
                    notif = await NotificationService.create_notification(
                        session=session,
                        user_id=user_id,
                        title=f"Budget Alert: {b.category}",
                        message=f"You have used {round(b.usage_percentage, 2)}% of your INR {round(b.limit_amount, 2)} budget limit for {b.category}.",
                        type="budget_limit",
                        delivery_channel="in_app"
                    )
                    await DeliveryService.deliver_notification(session, notif)
                    created_count += 1
                    
        # 2. Goal deadline checks
        goals_health = await GoalHealthService.get_goals_health(session, user_id)
        for g in goals_health:
            # Re-fetch goals to get deadline metadata
            from app.repositories.goals_repository import GoalsRepository
            goal_objs = await GoalsRepository.get_user_goals(session, user_id)
            goal_obj = next((x for x in goal_objs if x.id == g.goal_id), None)
            
            if goal_obj and goal_obj.deadline:
                days_rem = (goal_obj.deadline - date.today()).days
                # Alert if deadline is within 7 days and goal is not fully complete
                if 0 <= days_rem <= 7 and g.completion_percentage < 100.0:
                    stmt = select(Notification).where(
                        Notification.user_id == user_id,
                        Notification.type == "goal_due",
                        Notification.read == False,
                        Notification.title.like(f"%{goal_obj.goal_name}%")
                    )
                    res = await session.execute(stmt)
                    exists = res.scalars().all()
                    if not exists:
                        notif = await NotificationService.create_notification(
                            session=session,
                            user_id=user_id,
                            title=f"Goal Deadline Approaching: {goal_obj.goal_name}",
                            message=f"Your goal '{goal_obj.goal_name}' deadline is in {days_rem} days ({goal_obj.deadline}). You are currently {round(g.completion_percentage, 2)}% complete.",
                            type="goal_due",
                            delivery_channel="in_app"
                        )
                        await DeliveryService.deliver_notification(session, notif)
                        created_count += 1
                        
        if created_count > 0:
            await session.commit()
            
        return created_count
