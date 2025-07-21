"""
Service layer for task activity tracking and audit logging.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.models import ActivityType, Task, TaskActivity, User


class ActivityService:
    """Service for managing task activity tracking"""

    @staticmethod
    def log_activity(
        db: Session,
        task_id: str,
        user_id: Optional[str],
        activity_type: ActivityType,
        details: Optional[Dict[str, Any]] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TaskActivity:
        """
        Log a task activity.

        Args:
            db: Database session
            task_id: ID of the task
            user_id: ID of the user performing the action (can be None for system actions)
            activity_type: Type of activity being logged
            details: Additional details as a dictionary (will be JSON serialized)
            old_value: Previous value for change activities
            new_value: New value for change activities
            ip_address: IP address of the user
            user_agent: User agent string

        Returns:
            Created TaskActivity instance
        """
        # Verify task exists
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Verify user exists if user_id provided
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

        activity = TaskActivity(
            id=str(uuid.uuid4()),
            task_id=task_id,
            user_id=user_id,
            activity_type=activity_type,
            details=json.dumps(details) if details else None,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
        )

        db.add(activity)
        db.commit()
        db.refresh(activity)

        logger.info(
            f"Logged activity {activity_type.value} for task {task_id} by user {user_id}"
        )
        return activity

    @staticmethod
    def get_task_activities(
        db: Session,
        task_id: str,
        limit: int = 50,
        offset: int = 0,
        activity_types: Optional[List[ActivityType]] = None,
    ) -> List[TaskActivity]:
        """
        Get activities for a specific task.

        Args:
            db: Database session
            task_id: ID of the task
            limit: Maximum number of activities to return
            offset: Number of activities to skip
            activity_types: Filter by specific activity types

        Returns:
            List of TaskActivity instances
        """
        from sqlalchemy.orm import joinedload

        query = (
            db.query(TaskActivity)
            .options(joinedload(TaskActivity.user))
            .filter(TaskActivity.task_id == task_id)
        )

        if activity_types:
            query = query.filter(TaskActivity.activity_type.in_(activity_types))

        return (
            query.order_by(desc(TaskActivity.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_user_activities(
        db: Session,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        activity_types: Optional[List[ActivityType]] = None,
    ) -> List[TaskActivity]:
        """
        Get activities performed by a specific user.

        Args:
            db: Database session
            user_id: ID of the user
            limit: Maximum number of activities to return
            offset: Number of activities to skip
            activity_types: Filter by specific activity types

        Returns:
            List of TaskActivity instances
        """
        from sqlalchemy.orm import joinedload

        query = (
            db.query(TaskActivity)
            .options(joinedload(TaskActivity.user))
            .filter(TaskActivity.user_id == user_id)
        )

        if activity_types:
            query = query.filter(TaskActivity.activity_type.in_(activity_types))

        return (
            query.order_by(desc(TaskActivity.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def log_task_created(
        db: Session,
        task_id: str,
        user_id: str,
        task_data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TaskActivity:
        """Log task creation activity."""
        return ActivityService.log_activity(
            db=db,
            task_id=task_id,
            user_id=user_id,
            activity_type=ActivityType.CREATED,
            details={
                "title": task_data.get("title"),
                "status": task_data.get("status"),
                "priority": task_data.get("priority"),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_status_change(
        db: Session,
        task_id: str,
        user_id: str,
        old_status: str,
        new_status: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TaskActivity:
        """Log task status change activity."""
        return ActivityService.log_activity(
            db=db,
            task_id=task_id,
            user_id=user_id,
            activity_type=ActivityType.STATUS_CHANGED,
            old_value=old_status,
            new_value=new_status,
            details={"from_status": old_status, "to_status": new_status},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_priority_change(
        db: Session,
        task_id: str,
        user_id: str,
        old_priority: str,
        new_priority: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TaskActivity:
        """Log task priority change activity."""
        return ActivityService.log_activity(
            db=db,
            task_id=task_id,
            user_id=user_id,
            activity_type=ActivityType.PRIORITY_CHANGED,
            old_value=old_priority,
            new_value=new_priority,
            details={"from_priority": old_priority, "to_priority": new_priority},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_assignment_change(
        db: Session,
        task_id: str,
        user_id: str,
        old_assignee_id: Optional[str],
        new_assignee_id: Optional[str],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TaskActivity:
        """Log task assignment change activity."""
        if old_assignee_id and new_assignee_id:
            # Reassignment
            activity_type = ActivityType.ASSIGNED
            details = {
                "old_assignee_id": old_assignee_id,
                "new_assignee_id": new_assignee_id,
                "action": "reassigned",
            }
        elif new_assignee_id:
            # Assignment
            activity_type = ActivityType.ASSIGNED
            details = {"assignee_id": new_assignee_id, "action": "assigned"}
        else:
            # Unassignment
            activity_type = ActivityType.UNASSIGNED
            details = {"old_assignee_id": old_assignee_id, "action": "unassigned"}

        return ActivityService.log_activity(
            db=db,
            task_id=task_id,
            user_id=user_id,
            activity_type=activity_type,
            old_value=old_assignee_id,
            new_value=new_assignee_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_due_date_change(
        db: Session,
        task_id: str,
        user_id: str,
        old_due_date: Optional[datetime],
        new_due_date: Optional[datetime],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TaskActivity:
        """Log task due date change activity."""
        old_value = old_due_date.isoformat() if old_due_date else None
        new_value = new_due_date.isoformat() if new_due_date else None

        return ActivityService.log_activity(
            db=db,
            task_id=task_id,
            user_id=user_id,
            activity_type=ActivityType.DUE_DATE_CHANGED,
            old_value=old_value,
            new_value=new_value,
            details={"old_due_date": old_value, "new_due_date": new_value},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_title_change(
        db: Session,
        task_id: str,
        user_id: str,
        old_title: str,
        new_title: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TaskActivity:
        """Log task title change activity."""
        return ActivityService.log_activity(
            db=db,
            task_id=task_id,
            user_id=user_id,
            activity_type=ActivityType.TITLE_CHANGED,
            old_value=old_title,
            new_value=new_title,
            details={"old_title": old_title, "new_title": new_title},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_description_change(
        db: Session,
        task_id: str,
        user_id: str,
        old_description: Optional[str],
        new_description: Optional[str],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TaskActivity:
        """Log task description change activity."""
        return ActivityService.log_activity(
            db=db,
            task_id=task_id,
            user_id=user_id,
            activity_type=ActivityType.DESCRIPTION_CHANGED,
            old_value=old_description,
            new_value=new_description,
            details={
                "old_description": old_description,
                "new_description": new_description,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_comment_added(
        db: Session,
        task_id: str,
        user_id: str,
        comment_id: str,
        comment_content: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TaskActivity:
        """Log comment addition activity."""
        return ActivityService.log_activity(
            db=db,
            task_id=task_id,
            user_id=user_id,
            activity_type=ActivityType.COMMENT_ADDED,
            details={
                "comment_id": comment_id,
                "comment_content": (
                    comment_content[:200] + "..."
                    if len(comment_content) > 200
                    else comment_content
                ),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_attachment_added(
        db: Session,
        task_id: str,
        user_id: str,
        attachment_id: str,
        filename: str,
        file_size: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TaskActivity:
        """Log file attachment activity."""
        return ActivityService.log_activity(
            db=db,
            task_id=task_id,
            user_id=user_id,
            activity_type=ActivityType.ATTACHMENT_ADDED,
            details={
                "attachment_id": attachment_id,
                "filename": filename,
                "file_size": file_size,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_time_logged(
        db: Session,
        task_id: str,
        user_id: str,
        hours: float,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TaskActivity:
        """Log time tracking activity."""
        return ActivityService.log_activity(
            db=db,
            task_id=task_id,
            user_id=user_id,
            activity_type=ActivityType.TIME_LOGGED,
            details={"hours": hours, "description": description},
            new_value=str(hours),
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_subtask_added(
        db: Session,
        task_id: str,
        user_id: str,
        subtask_id: str,
        subtask_title: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TaskActivity:
        """Log subtask addition activity."""
        return ActivityService.log_activity(
            db=db,
            task_id=task_id,
            user_id=user_id,
            activity_type=ActivityType.SUBTASK_ADDED,
            details={"subtask_id": subtask_id, "subtask_title": subtask_title},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_task_completed(
        db: Session,
        task_id: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TaskActivity:
        """Log task completion activity."""
        return ActivityService.log_activity(
            db=db,
            task_id=task_id,
            user_id=user_id,
            activity_type=ActivityType.COMPLETED,
            details={"completed_at": datetime.now(timezone.utc).isoformat()},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_task_shared(
        db: Session,
        task_id: str,
        user_id: str,
        shared_with_user_id: str,
        permission: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TaskActivity:
        """Log task sharing activity."""
        return ActivityService.log_activity(
            db=db,
            task_id=task_id,
            user_id=user_id,
            activity_type=ActivityType.SHARED,
            details={
                "shared_with_user_id": shared_with_user_id,
                "permission": permission,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def cleanup_old_activities(db: Session, days: int = 365) -> int:
        """
        Clean up old activity records to manage database size.

        Args:
            db: Database session
            days: Number of days to keep (default 1 year)

        Returns:
            Number of deleted records
        """
        from datetime import timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        deleted_count = (
            db.query(TaskActivity)
            .filter(TaskActivity.created_at < cutoff_date)
            .delete()
        )

        db.commit()

        logger.info(
            f"Cleaned up {deleted_count} old activity records older than {days} days"
        )
        return deleted_count
