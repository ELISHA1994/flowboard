"""
Notification and reminder API endpoints.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.middleware.jwt_auth_backend import get_current_user
from app.db.database import get_db
from app.db.models import Notification, Task, TaskReminder, User
from app.models.notification import (NotificationMarkRead,
                                     NotificationPreferenceResponse,
                                     NotificationPreferenceUpdate,
                                     NotificationResponse, NotificationStats,
                                     TaskDueDateRemindersCreate,
                                     TaskReminderCreate, TaskReminderResponse,
                                     TaskReminderUpdate)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    notification_type: Optional[str] = Query(
        None, description="Filter by notification type"
    ),
    skip: int = Query(0, ge=0, description="Number of notifications to skip"),
    limit: int = Query(
        50, ge=1, le=100, description="Number of notifications to return"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get notifications for the current user."""
    notifications = NotificationService.get_user_notifications(
        db,
        current_user.id,
        unread_only=unread_only,
        notification_type=notification_type,
        limit=limit,
        offset=skip,
    )

    # Parse JSON data if present
    for notification in notifications:
        if notification.data:
            try:
                notification.data = json.loads(notification.data)
            except:
                notification.data = None

    return notifications


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get notification statistics for the current user."""
    # Get total and unread counts
    total = (
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == current_user.id)
        .scalar()
    )

    unread = (
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == current_user.id, Notification.read == False)
        .scalar()
    )

    # Get counts by type
    type_counts = (
        db.query(Notification.type, func.count(Notification.id))
        .filter(Notification.user_id == current_user.id)
        .group_by(Notification.type)
        .all()
    )

    by_type = {notification_type: count for notification_type, count in type_counts}

    return NotificationStats(total=total or 0, unread=unread or 0, by_type=by_type)


@router.put("/read/{notification_id}")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a notification as read."""
    success = NotificationService.mark_notification_read(
        db, notification_id, current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"message": "Notification marked as read"}


@router.put("/read")
async def mark_multiple_notifications_read(
    mark_read: NotificationMarkRead,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark multiple notifications as read."""
    count = 0
    for notification_id in mark_read.notification_ids:
        if NotificationService.mark_notification_read(
            db, notification_id, current_user.id
        ):
            count += 1

    return {"message": f"Marked {count} notifications as read"}


@router.put("/read-all")
async def mark_all_notifications_read(
    notification_type: Optional[str] = Query(
        None, description="Only mark specific type as read"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read."""
    count = NotificationService.mark_all_notifications_read(
        db, current_user.id, notification_type
    )

    return {"message": f"Marked {count} notifications as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a notification."""
    success = NotificationService.delete_notification(
        db, notification_id, current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"message": "Notification deleted"}


# Notification preferences endpoints
@router.get("/preferences", response_model=List[NotificationPreferenceResponse])
async def get_notification_preferences(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get notification preferences for the current user."""
    preferences = NotificationService.get_notification_preferences(db, current_user.id)

    return preferences


@router.put("/preferences")
async def update_notification_preference(
    preference: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update notification preferences."""
    updated_preference = NotificationService.update_notification_preference(
        db,
        current_user.id,
        preference.notification_type,
        preference.channel,
        preference.enabled,
        preference.frequency,
    )

    return updated_preference


# Task reminder endpoints
@router.post("/reminders", response_model=TaskReminderResponse)
async def create_task_reminder(
    reminder: TaskReminderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a custom task reminder."""
    # Verify task exists and user has access
    task = (
        db.query(Task)
        .filter(Task.id == reminder.task_id, Task.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Don't create reminders in the past
    if reminder.remind_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400, detail="Reminder time must be in the future"
        )

    task_reminder = NotificationService.create_task_reminder(
        db,
        reminder.task_id,
        current_user.id,
        reminder.remind_at,
        "custom",
        None,
        reminder.message,
    )

    return task_reminder


@router.post("/reminders/due-date", response_model=List[TaskReminderResponse])
async def create_due_date_reminders(
    reminders: TaskDueDateRemindersCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create due date reminders for a task."""
    # Verify task exists and user has access
    task = (
        db.query(Task)
        .filter(Task.id == reminders.task_id, Task.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.due_date:
        raise HTTPException(status_code=400, detail="Task must have a due date")

    created_reminders = NotificationService.create_due_date_reminders(
        db, task, reminders.offset_minutes
    )

    return created_reminders


@router.get("/reminders", response_model=List[TaskReminderResponse])
async def get_task_reminders(
    task_id: str = Query(..., description="Task ID to get reminders for"),
    include_sent: bool = Query(False, description="Include sent reminders"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get reminders for a task."""
    reminders = NotificationService.get_task_reminders(
        db, task_id, current_user.id, include_sent
    )

    return reminders


@router.put("/reminders/{reminder_id}", response_model=TaskReminderResponse)
async def update_task_reminder(
    reminder_id: str,
    update: TaskReminderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a task reminder."""
    reminder = (
        db.query(TaskReminder)
        .filter(TaskReminder.id == reminder_id, TaskReminder.user_id == current_user.id)
        .first()
    )

    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    if reminder.sent:
        raise HTTPException(status_code=400, detail="Cannot update sent reminder")

    if update.remind_at is not None:
        if update.remind_at <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400, detail="Reminder time must be in the future"
            )
        reminder.remind_at = update.remind_at

    if update.message is not None:
        reminder.message = update.message

    db.commit()
    db.refresh(reminder)

    return reminder


@router.delete("/reminders/{reminder_id}")
async def delete_task_reminder(
    reminder_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a task reminder."""
    success = NotificationService.delete_task_reminder(db, reminder_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")

    return {"message": "Reminder deleted"}


@router.post("/process-reminders")
async def process_pending_reminders(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually trigger processing of pending reminders (admin only)."""
    # In production, this would be restricted to admin users
    # For now, we'll allow any authenticated user to trigger it

    def process_reminders():
        NotificationService.process_pending_reminders(db)

    background_tasks.add_task(process_reminders)

    return {"message": "Processing reminders in background"}
