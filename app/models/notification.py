"""
Pydantic models for notification functionality.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class NotificationTypeEnum(str, Enum):
    """Notification types."""
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


class NotificationChannelEnum(str, Enum):
    """Notification channels."""
    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"


class NotificationFrequencyEnum(str, Enum):
    """Notification frequencies."""
    IMMEDIATE = "immediate"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_DIGEST = "weekly_digest"


class NotificationResponse(BaseModel):
    """Model for notification response."""
    id: str
    user_id: str
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]]
    read: bool
    read_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NotificationMarkRead(BaseModel):
    """Model for marking notifications as read."""
    notification_ids: List[str] = Field(..., min_length=1, description="List of notification IDs to mark as read")


class NotificationPreferenceUpdate(BaseModel):
    """Model for updating notification preferences."""
    notification_type: NotificationTypeEnum = Field(..., description="Type of notification")
    channel: NotificationChannelEnum = Field(..., description="Notification channel")
    enabled: bool = Field(..., description="Whether this notification type/channel is enabled")
    frequency: NotificationFrequencyEnum = Field(default=NotificationFrequencyEnum.IMMEDIATE, description="Notification frequency")


class NotificationPreferenceResponse(BaseModel):
    """Model for notification preference response."""
    id: str
    user_id: str
    notification_type: str
    channel: str
    enabled: bool
    frequency: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskReminderCreate(BaseModel):
    """Model for creating a task reminder."""
    task_id: str = Field(..., description="Task ID to set reminder for")
    remind_at: datetime = Field(..., description="When to send the reminder")
    message: Optional[str] = Field(None, max_length=500, description="Custom reminder message")


class TaskReminderUpdate(BaseModel):
    """Model for updating a task reminder."""
    remind_at: Optional[datetime] = Field(None, description="New reminder time")
    message: Optional[str] = Field(None, max_length=500, description="Updated reminder message")


class TaskReminderResponse(BaseModel):
    """Model for task reminder response."""
    id: str
    task_id: str
    user_id: str
    remind_at: datetime
    reminder_type: str
    offset_minutes: Optional[int]
    message: Optional[str]
    sent: bool
    sent_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskDueDateRemindersCreate(BaseModel):
    """Model for creating due date reminders."""
    task_id: str = Field(..., description="Task ID to set reminders for")
    offset_minutes: List[int] = Field(
        default=[60, 1440],  # 1 hour, 1 day
        description="Minutes before due date to send reminders"
    )


class NotificationStats(BaseModel):
    """Model for notification statistics."""
    total: int = Field(..., description="Total number of notifications")
    unread: int = Field(..., description="Number of unread notifications")
    by_type: Dict[str, int] = Field(default_factory=dict, description="Count by notification type")