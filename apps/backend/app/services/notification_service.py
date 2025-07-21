"""
Notification service for managing notifications and reminders.
"""

import json
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.models import (Comment, Notification, NotificationPreference, Task,
                           TaskReminder, User)


class NotificationType(str, Enum):
    """Types of notifications."""

    TASK_DUE = "task_due"
    TASK_OVERDUE = "task_overdue"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    TASK_UPDATED = "task_updated"
    COMMENT_ADDED = "comment_added"
    COMMENT_MENTION = "comment_mention"
    PROJECT_INVITE = "project_invite"
    PROJECT_UPDATE = "project_update"
    REMINDER_CUSTOM = "reminder_custom"
    REMINDER_DUE_DATE = "reminder_due_date"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""

    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"


class NotificationFrequency(str, Enum):
    """Notification frequency options."""

    IMMEDIATE = "immediate"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_DIGEST = "weekly_digest"


class NotificationService:
    """Service for managing notifications and reminders."""

    @staticmethod
    def create_notification(
        db: Session,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            data=json.dumps(data) if data else None,
            created_at=datetime.now(timezone.utc),
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        logger.info(f"Created notification {notification.id} for user {user_id}")
        return notification

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: str,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """Get notifications for a user."""
        query = db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.read == False)

        if notification_type:
            query = query.filter(Notification.type == notification_type)

        query = query.order_by(Notification.created_at.desc())

        return query.offset(offset).limit(limit).all()

    @staticmethod
    def mark_notification_read(db: Session, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read."""
        notification = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )

        if not notification:
            return False

        notification.read = True
        notification.read_at = datetime.now(timezone.utc)
        db.commit()

        return True

    @staticmethod
    def mark_all_notifications_read(
        db: Session, user_id: str, notification_type: Optional[str] = None
    ) -> int:
        """Mark all notifications as read for a user."""
        query = db.query(Notification).filter(
            Notification.user_id == user_id, Notification.read == False
        )

        if notification_type:
            query = query.filter(Notification.type == notification_type)

        count = query.update(
            {Notification.read: True, Notification.read_at: datetime.now(timezone.utc)}
        )

        db.commit()
        return count

    @staticmethod
    def delete_notification(db: Session, notification_id: str, user_id: str) -> bool:
        """Delete a notification."""
        notification = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )

        if not notification:
            return False

        db.delete(notification)
        db.commit()

        return True

    @staticmethod
    def get_notification_preferences(
        db: Session, user_id: str
    ) -> List[NotificationPreference]:
        """Get all notification preferences for a user."""
        return (
            db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == user_id)
            .all()
        )

    @staticmethod
    def update_notification_preference(
        db: Session,
        user_id: str,
        notification_type: str,
        channel: str,
        enabled: bool,
        frequency: str = NotificationFrequency.IMMEDIATE,
    ) -> NotificationPreference:
        """Update or create a notification preference."""
        preference = (
            db.query(NotificationPreference)
            .filter(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type == notification_type,
                NotificationPreference.channel == channel,
            )
            .first()
        )

        if preference:
            preference.enabled = enabled
            preference.frequency = frequency
            preference.updated_at = datetime.now(timezone.utc)
        else:
            preference = NotificationPreference(
                user_id=user_id,
                notification_type=notification_type,
                channel=channel,
                enabled=enabled,
                frequency=frequency,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(preference)

        db.commit()
        db.refresh(preference)

        return preference

    @staticmethod
    def should_send_notification(
        db: Session, user_id: str, notification_type: str, channel: str
    ) -> bool:
        """Check if a notification should be sent based on preferences."""
        preference = (
            db.query(NotificationPreference)
            .filter(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type == notification_type,
                NotificationPreference.channel == channel,
            )
            .first()
        )

        # Default to enabled if no preference exists
        return preference.enabled if preference else True

    @staticmethod
    def create_task_reminder(
        db: Session,
        task_id: str,
        user_id: str,
        remind_at: datetime,
        reminder_type: str = "due_date",
        offset_minutes: Optional[int] = None,
        message: Optional[str] = None,
    ) -> TaskReminder:
        """Create a task reminder."""
        reminder = TaskReminder(
            task_id=task_id,
            user_id=user_id,
            remind_at=remind_at,
            reminder_type=reminder_type,
            offset_minutes=offset_minutes,
            message=message,
            created_at=datetime.now(timezone.utc),
        )

        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        logger.info(f"Created reminder {reminder.id} for task {task_id}")
        return reminder

    @staticmethod
    def create_due_date_reminders(
        db: Session,
        task: Task,
        offset_minutes_list: List[int] = [60, 1440],  # 1 hour, 1 day before
    ) -> List[TaskReminder]:
        """Create reminders based on task due date."""
        if not task.due_date:
            return []

        reminders = []
        for offset_minutes in offset_minutes_list:
            # Ensure task.due_date is timezone-aware
            due_date = task.due_date
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)

            remind_at = due_date - timedelta(minutes=offset_minutes)

            # Don't create reminders in the past
            if remind_at > datetime.now(timezone.utc):
                reminder = NotificationService.create_task_reminder(
                    db, task.id, task.user_id, remind_at, "due_date", offset_minutes
                )
                reminders.append(reminder)

        return reminders

    @staticmethod
    def get_task_reminders(
        db: Session, task_id: str, user_id: str, include_sent: bool = False
    ) -> List[TaskReminder]:
        """Get reminders for a task."""
        query = db.query(TaskReminder).filter(
            TaskReminder.task_id == task_id, TaskReminder.user_id == user_id
        )

        if not include_sent:
            query = query.filter(TaskReminder.sent == False)

        return query.order_by(TaskReminder.remind_at).all()

    @staticmethod
    def get_pending_reminders(db: Session, limit: int = 100) -> List[TaskReminder]:
        """Get reminders that need to be sent."""
        now = datetime.now(timezone.utc)

        return (
            db.query(TaskReminder)
            .filter(TaskReminder.remind_at <= now, TaskReminder.sent == False)
            .limit(limit)
            .all()
        )

    @staticmethod
    def mark_reminder_sent(db: Session, reminder_id: str) -> bool:
        """Mark a reminder as sent."""
        reminder = db.query(TaskReminder).filter(TaskReminder.id == reminder_id).first()

        if not reminder:
            return False

        reminder.sent = True
        reminder.sent_at = datetime.now(timezone.utc)
        db.commit()

        return True

    @staticmethod
    def delete_task_reminder(db: Session, reminder_id: str, user_id: str) -> bool:
        """Delete a task reminder."""
        reminder = (
            db.query(TaskReminder)
            .filter(TaskReminder.id == reminder_id, TaskReminder.user_id == user_id)
            .first()
        )

        if not reminder:
            return False

        db.delete(reminder)
        db.commit()

        return True

    @staticmethod
    def notify_task_assigned(db: Session, task: Task, assigned_by: User):
        """Create notification for task assignment."""
        if task.assigned_to_id and task.assigned_to_id != assigned_by.id:
            # Queue the notification as a background task
            from app.tasks.notifications import \
                send_task_assignment_notification

            send_task_assignment_notification.delay(
                task.id, task.assigned_to_id, assigned_by.id
            )
            logger.info(f"Queued assignment notification for task {task.id}")

    @staticmethod
    def notify_comment_mention(db: Session, comment: Comment, mentioned_user_id: str):
        """Create notification for comment mention."""
        if mentioned_user_id != comment.user_id:
            # Queue the notification as a background task
            from app.tasks.notifications import \
                send_comment_mention_notification

            send_comment_mention_notification.delay(comment.id, mentioned_user_id)
            logger.info(f"Queued mention notification for comment {comment.id}")

    @staticmethod
    def notify_task_due_soon(db: Session, task: Task, hours_until_due: int):
        """Create notification for task due soon."""
        if NotificationService.should_send_notification(
            db, task.user_id, NotificationType.TASK_DUE, NotificationChannel.IN_APP
        ):
            time_str = f"{hours_until_due} hours" if hours_until_due > 1 else "1 hour"
            NotificationService.create_notification(
                db,
                task.user_id,
                NotificationType.TASK_DUE,
                f"Task due in {time_str}",
                f"Your task '{task.title}' is due in {time_str}",
                {"task_id": task.id, "due_date": task.due_date.isoformat()},
            )

    @staticmethod
    def notify_task_overdue(db: Session, task: Task):
        """Create notification for overdue task."""
        if NotificationService.should_send_notification(
            db, task.user_id, NotificationType.TASK_OVERDUE, NotificationChannel.IN_APP
        ):
            NotificationService.create_notification(
                db,
                task.user_id,
                NotificationType.TASK_OVERDUE,
                f"Task overdue: {task.title}",
                f"Your task '{task.title}' is overdue",
                {"task_id": task.id, "due_date": task.due_date.isoformat()},
            )

    @staticmethod
    def process_pending_reminders(db: Session):
        """Process and send pending reminders - Now handled by Celery periodic task."""
        # This method is replaced by the Celery periodic task
        # app.tasks.reminders.send_reminder_notifications
        logger.warning(
            "process_pending_reminders called directly - this should be handled by Celery periodic task"
        )

        # For backward compatibility, we can queue the Celery task
        from app.core.celery_app import celery_app

        celery_app.send_task("app.tasks.reminders.send_reminder_notifications")
        logger.info("Queued reminder processing task")
