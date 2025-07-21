from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.db.models import Task as TaskModel
from app.db.models import TaskPriority, TaskStatus, TimeLog
from app.services.cache_service import (cache_service, cached,
                                        invalidate_task_cache,
                                        invalidate_user_cache)


class TaskService:
    """Service layer for task-related business logic"""

    @staticmethod
    @cached(prefix=settings.CACHE_PREFIX_TASKS, ttl=300)  # Cache for 5 minutes
    def get_user_task_count(db: Session, user_id: str) -> int:
        """Get the total number of tasks for a user"""
        return db.query(TaskModel).filter(TaskModel.user_id == user_id).count()

    @staticmethod
    @cached(prefix=settings.CACHE_PREFIX_TASKS, ttl=180)  # Cache for 3 minutes
    def get_tasks_by_status(
        db: Session, user_id: str, status: TaskStatus
    ) -> List[TaskModel]:
        """Get all tasks for a user with a specific status"""
        return (
            db.query(TaskModel)
            .filter(TaskModel.user_id == user_id, TaskModel.status == status)
            .all()
        )

    @staticmethod
    def validate_task_limit(db: Session, user_id: str, limit: int = 100) -> bool:
        """Check if user has reached task limit"""
        count = TaskService.get_user_task_count(db, user_id)
        if count >= limit:
            logger.warning(f"User {user_id} has reached task limit of {limit}")
            return False
        return True

    @staticmethod
    def get_task_statistics(db: Session, user_id: str) -> dict:
        """Get task statistics for a user"""
        tasks = db.query(TaskModel).filter(TaskModel.user_id == user_id).all()

        stats = {
            "total": len(tasks),
            "by_status": {
                TaskStatus.TODO: 0,
                TaskStatus.IN_PROGRESS: 0,
                TaskStatus.DONE: 0,
            },
            "by_priority": {
                TaskPriority.LOW: 0,
                TaskPriority.MEDIUM: 0,
                TaskPriority.HIGH: 0,
                TaskPriority.URGENT: 0,
            },
            "overdue": 0,
            "due_today": 0,
            "due_this_week": 0,
            "completed_this_week": 0,
            "total_estimated_hours": 0.0,
            "total_actual_hours": 0.0,
        }

        today = datetime.now(timezone.utc).date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=7)

        for task in tasks:
            stats["by_status"][task.status] += 1
            # Handle tasks without priority (backward compatibility)
            if hasattr(task, "priority") and task.priority:
                stats["by_priority"][task.priority] += 1

            if task.estimated_hours:
                stats["total_estimated_hours"] += task.estimated_hours
            if hasattr(task, "actual_hours") and task.actual_hours is not None:
                stats["total_actual_hours"] += task.actual_hours

            if task.due_date:
                due_date = (
                    task.due_date.date()
                    if hasattr(task.due_date, "date")
                    else task.due_date
                )
                if due_date < today and task.status != TaskStatus.DONE:
                    stats["overdue"] += 1
                elif due_date == today:
                    stats["due_today"] += 1
                elif week_start <= due_date < week_end:
                    stats["due_this_week"] += 1

            if task.completed_at:
                completed_date = (
                    task.completed_at.date()
                    if hasattr(task.completed_at, "date")
                    else task.completed_at
                )
                if week_start <= completed_date < week_end:
                    stats["completed_this_week"] += 1

        return stats

    @staticmethod
    def get_overdue_tasks(db: Session, user_id: str) -> List[TaskModel]:
        """Get all overdue tasks for a user"""
        today = datetime.now(timezone.utc)
        return (
            db.query(TaskModel)
            .filter(
                and_(
                    TaskModel.user_id == user_id,
                    TaskModel.due_date < today,
                    TaskModel.status != TaskStatus.DONE,
                )
            )
            .all()
        )

    @staticmethod
    def get_upcoming_tasks(db: Session, user_id: str, days: int = 7) -> List[TaskModel]:
        """Get tasks due in the next N days"""
        today = datetime.now(timezone.utc)
        future_date = today + timedelta(days=days)

        return (
            db.query(TaskModel)
            .filter(
                and_(
                    TaskModel.user_id == user_id,
                    TaskModel.due_date >= today,
                    TaskModel.due_date <= future_date,
                    TaskModel.status != TaskStatus.DONE,
                )
            )
            .order_by(TaskModel.due_date)
            .all()
        )

    @staticmethod
    def update_task_positions(
        db: Session, user_id: str, task_id: str, new_position: int
    ) -> bool:
        """Update task positions when reordering"""
        tasks = (
            db.query(TaskModel)
            .filter(TaskModel.user_id == user_id)
            .order_by(TaskModel.position)
            .all()
        )

        # Find the task to move
        task_to_move = None
        old_position = None
        for i, task in enumerate(tasks):
            if task.id == task_id:
                task_to_move = task
                old_position = i
                break

        if not task_to_move:
            return False

        # Remove from old position
        tasks.pop(old_position)

        # Insert at new position
        tasks.insert(new_position, task_to_move)

        # Update positions
        for i, task in enumerate(tasks):
            task.position = i

        db.commit()
        return True

    @staticmethod
    def add_time_to_task(
        db: Session,
        task_id: str,
        user_id: str,
        hours: float,
        description: Optional[str] = None,
        logged_at: Optional[datetime] = None,
    ) -> Optional[TaskModel]:
        """Add time log to a task and update actual hours."""
        # Get the task
        task = TaskService.get_task_by_id(db, task_id, user_id)
        if not task:
            return None

        # Create time log entry
        time_log = TimeLog(
            task_id=task_id,
            user_id=user_id,
            hours=hours,
            description=description,
            logged_at=logged_at or datetime.now(timezone.utc),
        )

        # Update task's actual hours
        task.actual_hours = (task.actual_hours or 0) + hours

        # Add and commit
        db.add(time_log)
        db.commit()
        db.refresh(task)

        logger.info(f"Added {hours} hours to task {task_id}")
        return task

    @staticmethod
    def get_task_by_id(db: Session, task_id: str, user_id: str) -> Optional[TaskModel]:
        """Get a task by ID if user has access to it."""
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()

        if not task:
            return None

        # Check if user has access (owner, assigned, or shared)
        if task.user_id == user_id:
            return task

        if task.assigned_to_id == user_id:
            return task

        # Check if task is shared with user
        for share in task.shares:
            if share.shared_with_id == user_id:
                return task

        # Check if user has access through project
        if task.project and task.project.has_permission(user_id):
            return task

        return None
