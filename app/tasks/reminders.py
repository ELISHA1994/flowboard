"""
Background tasks for sending reminder notifications.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from celery import Task

from app.core.celery_app import celery_app
from app.db.database import get_db
from app.db.models import Task as TaskModel, TaskStatus, User, Notification, NotificationPreference
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task class that provides database session."""
    
    def __call__(self, *args, **kwargs):
        with get_db() as db:
            return self.run_with_db(db, *args, **kwargs)
    
    def run_with_db(self, db: Session, *args, **kwargs):
        """Override this method instead of run()"""
        raise NotImplementedError


@celery_app.task(bind=True, base=DatabaseTask, queue="reminders")
def send_reminder_notifications(self, db: Session):
    """Main periodic task to send reminder notifications for due tasks."""
    try:
        now = datetime.now(timezone.utc)
        logger.info(f"Processing reminder notifications at {now}")
        
        # Get tasks that need reminders
        reminder_tasks = get_tasks_needing_reminders(db, now)
        
        sent_count = 0
        processed_count = 0
        
        for task_info in reminder_tasks:
            try:
                # Send the reminder
                send_task_reminder.delay(task_info["task_id"], task_info["user_id"], task_info["reminder_type"])
                sent_count += 1
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error queuing reminder for task {task_info['task_id']}: {str(e)}")
                processed_count += 1
                continue
        
        logger.info(f"Processed {processed_count} tasks, sent {sent_count} reminders")
        return {
            "success": True,
            "processed_count": processed_count,
            "sent_count": sent_count,
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to process reminder notifications: {str(e)}")
        raise self.retry(countdown=300, max_retries=3)


def get_tasks_needing_reminders(db: Session, now: datetime) -> List[Dict[str, Any]]:
    """Get tasks that need reminders based on due dates and user preferences."""
    reminder_tasks = []
    
    # Define reminder intervals
    reminder_intervals = {
        "1_day": timedelta(days=1),
        "3_hours": timedelta(hours=3),
        "1_hour": timedelta(hours=1),
        "overdue": timedelta(0)
    }
    
    for reminder_type, interval in reminder_intervals.items():
        # Calculate the target time for this reminder type
        if reminder_type == "overdue":
            # For overdue tasks, check tasks past due date
            target_time = now
            query = db.query(TaskModel, User).join(User, TaskModel.assigned_to_id == User.id).filter(
                TaskModel.due_date < target_time,
                TaskModel.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
            )
        else:
            # For future reminders, check tasks due at specific intervals
            target_time = now + interval
            query = db.query(TaskModel, User).join(User, TaskModel.assigned_to_id == User.id).filter(
                TaskModel.due_date <= target_time,
                TaskModel.due_date > now,
                TaskModel.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
            )
        
        # Check if we haven't already sent this type of reminder recently
        recent_reminders_cutoff = now - timedelta(hours=1)
        
        tasks_and_users = query.all()
        
        for task, user in tasks_and_users:
            # Check user preferences for reminders
            if not should_send_reminder(db, user.id, reminder_type):
                continue
            
            # Check if we've already sent this type of reminder recently
            recent_reminder = db.query(Notification).filter(
                Notification.user_id == user.id,
                Notification.type == "task_reminder",
                Notification.data.contains({"task_id": task.id}),
                Notification.created_at >= recent_reminders_cutoff
            ).first()
            
            if recent_reminder:
                continue
            
            reminder_tasks.append({
                "task_id": task.id,
                "user_id": user.id,
                "reminder_type": reminder_type,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "task_title": task.title
            })
    
    return reminder_tasks


def should_send_reminder(db: Session, user_id: str, reminder_type: str) -> bool:
    """Check if user wants to receive this type of reminder."""
    try:
        # Get user preferences
        preference = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id,
            NotificationPreference.notification_type == f"reminder_{reminder_type}"
        ).first()
        
        if preference:
            return preference.enabled
        
        # Default to enabled if no preference set
        return True
        
    except Exception as e:
        logger.warning(f"Error checking reminder preference for user {user_id}: {str(e)}")
        return True


@celery_app.task(bind=True, base=DatabaseTask, queue="reminders")
def send_task_reminder(self, db: Session, task_id: str, user_id: str, reminder_type: str):
    """Send a reminder notification for a specific task."""
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        
        if not task or not user:
            logger.warning(f"Missing data for reminder: task={task_id}, user={user_id}")
            return {"success": False, "reason": "Missing data"}
        
        # Skip if task is already completed
        if task.status == TaskStatus.DONE:
            return {"success": False, "reason": "Task already completed"}
        
        # Determine reminder message based on type
        if reminder_type == "overdue":
            title = "Overdue Task"
            if task.due_date:
                days_overdue = (datetime.now(timezone.utc) - task.due_date).days
                message = f"Task '{task.title}' is {days_overdue} day(s) overdue"
            else:
                message = f"Task '{task.title}' is overdue"
        elif reminder_type == "1_day":
            title = "Task Due Tomorrow"
            message = f"Task '{task.title}' is due tomorrow"
        elif reminder_type == "3_hours":
            title = "Task Due Soon"
            message = f"Task '{task.title}' is due in 3 hours"
        elif reminder_type == "1_hour":
            title = "Task Due Very Soon"
            message = f"Task '{task.title}' is due in 1 hour"
        else:
            title = "Task Reminder"
            message = f"Reminder: Task '{task.title}'"
        
        # Create notification
        notification = Notification(
            user_id=user_id,
            type="task_reminder",
            title=title,
            message=message,
            data={
                "task_id": task_id,
                "task_title": task.title,
                "reminder_type": reminder_type,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "priority": task.priority.value
            }
        )
        db.add(notification)
        db.commit()
        
        # Queue email notification if user prefers email reminders
        from app.tasks.notifications import send_email_notification
        
        if should_send_email_reminder(db, user_id):
            subject = f"{title}: {task.title}"
            content = f"""
            <h2>{title}</h2>
            <p>Hello {user.username},</p>
            <p>{message}</p>
            <h3>{task.title}</h3>
            <p><strong>Description:</strong> {task.description or 'No description provided'}</p>
            <p><strong>Priority:</strong> {task.priority.value}</p>
            <p><strong>Due Date:</strong> {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'No due date set'}</p>
            <p><strong>Current Status:</strong> {task.status.value}</p>
            <p>Log in to update your task progress.</p>
            """
            
            send_email_notification.delay(user.email, subject, content, "task_reminder")
        
        logger.info(f"Sent {reminder_type} reminder for task {task_id} to user {user_id}")
        return {
            "success": True,
            "notification_id": notification.id,
            "reminder_type": reminder_type,
            "task_id": task_id,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Failed to send reminder for task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


def should_send_email_reminder(db: Session, user_id: str) -> bool:
    """Check if user wants to receive email reminders."""
    try:
        preference = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id,
            NotificationPreference.notification_type == "email_reminders"
        ).first()
        
        if preference:
            return preference.enabled
        
        # Default to enabled
        return True
        
    except Exception as e:
        logger.warning(f"Error checking email reminder preference for user {user_id}: {str(e)}")
        return True


@celery_app.task(bind=True, base=DatabaseTask, queue="reminders")
def send_daily_task_summary(self, db: Session, user_id: str):
    """Send daily task summary to a user."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "reason": "User not found"}
        
        # Check if user wants daily summaries
        if not should_send_daily_summary(db, user_id):
            return {"success": False, "reason": "User disabled daily summaries"}
        
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Get user's tasks for today
        todays_tasks = db.query(TaskModel).filter(
            or_(
                TaskModel.user_id == user_id,
                TaskModel.assigned_to_id == user_id
            ),
            or_(
                and_(TaskModel.due_date >= today_start, TaskModel.due_date < today_end),
                TaskModel.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
            )
        ).all()
        
        # Categorize tasks
        due_today = [t for t in todays_tasks if t.due_date and today_start <= t.due_date < today_end]
        overdue = [t for t in todays_tasks if t.due_date and t.due_date < today_start and t.status != TaskStatus.DONE]
        in_progress = [t for t in todays_tasks if t.status == TaskStatus.IN_PROGRESS]
        
        # Create summary notification
        summary_parts = []
        if due_today:
            summary_parts.append(f"{len(due_today)} task(s) due today")
        if overdue:
            summary_parts.append(f"{len(overdue)} overdue task(s)")
        if in_progress:
            summary_parts.append(f"{len(in_progress)} task(s) in progress")
        
        if not summary_parts:
            summary_message = "No urgent tasks for today. Great job staying on top of things!"
        else:
            summary_message = "Daily task summary: " + ", ".join(summary_parts)
        
        # Create notification
        notification = Notification(
            user_id=user_id,
            type="daily_summary",
            title="Daily Task Summary",
            message=summary_message,
            data={
                "date": now.date().isoformat(),
                "due_today_count": len(due_today),
                "overdue_count": len(overdue),
                "in_progress_count": len(in_progress),
                "total_tasks": len(todays_tasks)
            }
        )
        db.add(notification)
        db.commit()
        
        # Send email summary
        from app.tasks.notifications import send_email_notification
        
        subject = f"Daily Task Summary - {now.strftime('%B %d, %Y')}"
        content = f"""
        <h2>Daily Task Summary</h2>
        <p>Hello {user.username},</p>
        <p>Here's your task summary for {now.strftime('%B %d, %Y')}:</p>
        
        <h3>📋 Overview</h3>
        <ul>
            <li><strong>Due Today:</strong> {len(due_today)} task(s)</li>
            <li><strong>Overdue:</strong> {len(overdue)} task(s)</li>
            <li><strong>In Progress:</strong> {len(in_progress)} task(s)</li>
        </ul>
        """
        
        # Add due today tasks
        if due_today:
            content += "<h3>⏰ Due Today</h3><ul>"
            for task in due_today[:5]:  # Limit to 5 tasks
                content += f"<li><strong>{task.title}</strong> - {task.priority.value} priority</li>"
            if len(due_today) > 5:
                content += f"<li>... and {len(due_today) - 5} more</li>"
            content += "</ul>"
        
        # Add overdue tasks
        if overdue:
            content += "<h3>🚨 Overdue Tasks</h3><ul>"
            for task in overdue[:5]:  # Limit to 5 tasks
                days_overdue = (now - task.due_date).days if task.due_date else 0
                content += f"<li><strong>{task.title}</strong> - {days_overdue} day(s) overdue</li>"
            if len(overdue) > 5:
                content += f"<li>... and {len(overdue) - 5} more</li>"
            content += "</ul>"
        
        content += "<p>Log in to manage your tasks and stay productive!</p>"
        
        send_email_notification.delay(user.email, subject, content, "daily_summary")
        
        logger.info(f"Sent daily task summary to user {user_id}")
        return {
            "success": True,
            "notification_id": notification.id,
            "user_id": user_id,
            "summary": {
                "due_today": len(due_today),
                "overdue": len(overdue),
                "in_progress": len(in_progress)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to send daily summary to user {user_id}: {str(e)}")
        raise self.retry(countdown=120, max_retries=3)


def should_send_daily_summary(db: Session, user_id: str) -> bool:
    """Check if user wants to receive daily summaries."""
    try:
        preference = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id,
            NotificationPreference.notification_type == "daily_summary"
        ).first()
        
        if preference:
            return preference.enabled
        
        # Default to disabled for daily summaries
        return False
        
    except Exception as e:
        logger.warning(f"Error checking daily summary preference for user {user_id}: {str(e)}")
        return False


@celery_app.task(bind=True, base=DatabaseTask, queue="reminders")
def send_weekly_productivity_report(self, db: Session, user_id: str):
    """Send weekly productivity report to a user."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "reason": "User not found"}
        
        # Check if user wants weekly reports
        if not should_send_weekly_report(db, user_id):
            return {"success": False, "reason": "User disabled weekly reports"}
        
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=7)
        
        # Get user's task activity for the past week
        completed_tasks = db.query(TaskModel).filter(
            or_(
                TaskModel.user_id == user_id,
                TaskModel.assigned_to_id == user_id
            ),
            TaskModel.status == TaskStatus.DONE,
            TaskModel.completed_at >= week_start,
            TaskModel.completed_at <= now
        ).count()
        
        created_tasks = db.query(TaskModel).filter(
            TaskModel.user_id == user_id,
            TaskModel.created_at >= week_start,
            TaskModel.created_at <= now
        ).count()
        
        # Calculate productivity metrics
        report_data = {
            "week_ending": now.date().isoformat(),
            "tasks_completed": completed_tasks,
            "tasks_created": created_tasks,
            "productivity_score": min(100, (completed_tasks / max(1, created_tasks)) * 100)
        }
        
        # Create notification
        notification = Notification(
            user_id=user_id,
            type="weekly_report",
            title="Weekly Productivity Report",
            message=f"This week: {completed_tasks} tasks completed, {created_tasks} tasks created",
            data=report_data
        )
        db.add(notification)
        db.commit()
        
        logger.info(f"Sent weekly productivity report to user {user_id}")
        return {"success": True, "notification_id": notification.id, "report": report_data}
        
    except Exception as e:
        logger.error(f"Failed to send weekly report to user {user_id}: {str(e)}")
        raise self.retry(countdown=120, max_retries=3)


def should_send_weekly_report(db: Session, user_id: str) -> bool:
    """Check if user wants to receive weekly reports."""
    try:
        preference = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id,
            NotificationPreference.notification_type == "weekly_report"
        ).first()
        
        if preference:
            return preference.enabled
        
        # Default to disabled
        return False
        
    except Exception as e:
        logger.warning(f"Error checking weekly report preference for user {user_id}: {str(e)}")
        return False


@celery_app.task(bind=True, base=DatabaseTask, queue="reminders")
def send_bulk_daily_summaries(self, db: Session):
    """Send daily summaries to all users who have opted in."""
    try:
        # Get users who want daily summaries
        users_with_summaries = db.query(User).join(NotificationPreference).filter(
            NotificationPreference.notification_type == "daily_summary",
            NotificationPreference.enabled == True
        ).all()
        
        sent_count = 0
        for user in users_with_summaries:
            try:
                send_daily_task_summary.delay(user.id)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to queue daily summary for user {user.id}: {str(e)}")
        
        logger.info(f"Queued daily summaries for {sent_count} users")
        return {"success": True, "sent_count": sent_count}
        
    except Exception as e:
        logger.error(f"Failed to send bulk daily summaries: {str(e)}")
        raise self.retry(countdown=300, max_retries=2)