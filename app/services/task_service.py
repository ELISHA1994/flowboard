from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.db.models import Task as TaskModel, TaskStatus, TaskPriority
from app.core.logging import logger

class TaskService:
    """Service layer for task-related business logic"""
    
    @staticmethod
    def get_user_task_count(db: Session, user_id: str) -> int:
        """Get the total number of tasks for a user"""
        return db.query(TaskModel).filter(TaskModel.user_id == user_id).count()
    
    @staticmethod
    def get_tasks_by_status(db: Session, user_id: str, status: TaskStatus) -> List[TaskModel]:
        """Get all tasks for a user with a specific status"""
        return db.query(TaskModel).filter(
            TaskModel.user_id == user_id,
            TaskModel.status == status
        ).all()
    
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
                TaskStatus.DONE: 0
            },
            "by_priority": {
                TaskPriority.LOW: 0,
                TaskPriority.MEDIUM: 0,
                TaskPriority.HIGH: 0,
                TaskPriority.URGENT: 0
            },
            "overdue": 0,
            "due_today": 0,
            "due_this_week": 0,
            "completed_this_week": 0,
            "total_estimated_hours": 0.0,
            "total_actual_hours": 0.0
        }
        
        today = datetime.now(timezone.utc).date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=7)
        
        for task in tasks:
            stats["by_status"][task.status] += 1
            # Handle tasks without priority (backward compatibility)
            if hasattr(task, 'priority') and task.priority:
                stats["by_priority"][task.priority] += 1
            
            if task.estimated_hours:
                stats["total_estimated_hours"] += task.estimated_hours
            if hasattr(task, 'actual_hours') and task.actual_hours is not None:
                stats["total_actual_hours"] += task.actual_hours
            
            if task.due_date:
                due_date = task.due_date.date() if hasattr(task.due_date, 'date') else task.due_date
                if due_date < today and task.status != TaskStatus.DONE:
                    stats["overdue"] += 1
                elif due_date == today:
                    stats["due_today"] += 1
                elif week_start <= due_date < week_end:
                    stats["due_this_week"] += 1
            
            if task.completed_at:
                completed_date = task.completed_at.date() if hasattr(task.completed_at, 'date') else task.completed_at
                if week_start <= completed_date < week_end:
                    stats["completed_this_week"] += 1
        
        return stats
    
    @staticmethod
    def get_overdue_tasks(db: Session, user_id: str) -> List[TaskModel]:
        """Get all overdue tasks for a user"""
        today = datetime.now(timezone.utc)
        return db.query(TaskModel).filter(
            and_(
                TaskModel.user_id == user_id,
                TaskModel.due_date < today,
                TaskModel.status != TaskStatus.DONE
            )
        ).all()
    
    @staticmethod
    def get_upcoming_tasks(db: Session, user_id: str, days: int = 7) -> List[TaskModel]:
        """Get tasks due in the next N days"""
        today = datetime.now(timezone.utc)
        future_date = today + timedelta(days=days)
        
        return db.query(TaskModel).filter(
            and_(
                TaskModel.user_id == user_id,
                TaskModel.due_date >= today,
                TaskModel.due_date <= future_date,
                TaskModel.status != TaskStatus.DONE
            )
        ).order_by(TaskModel.due_date).all()
    
    @staticmethod
    def update_task_positions(db: Session, user_id: str, task_id: str, new_position: int) -> bool:
        """Update task positions when reordering"""
        tasks = db.query(TaskModel).filter(
            TaskModel.user_id == user_id
        ).order_by(TaskModel.position).all()
        
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