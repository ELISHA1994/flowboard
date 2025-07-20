"""
Service layer for handling recurring task operations.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.models import Task, RecurrencePattern, TaskStatus
from app.models.task import RecurrenceConfig
from app.core.logging import logger


class RecurrenceService:
    """Service for handling recurring task operations"""
    
    @staticmethod
    def calculate_next_occurrence(
        base_date: datetime,
        pattern: RecurrencePattern,
        interval: int = 1,
        days_of_week: Optional[List[int]] = None,
        day_of_month: Optional[int] = None,
        month_of_year: Optional[int] = None
    ) -> Optional[datetime]:
        """
        Calculate the next occurrence date based on recurrence pattern.
        
        Args:
            base_date: The reference date to calculate from
            pattern: The recurrence pattern
            interval: The interval for the pattern
            days_of_week: Days of week for weekly pattern (0=Monday, 6=Sunday)
            day_of_month: Day of month for monthly pattern
            month_of_year: Month for yearly pattern
            
        Returns:
            The next occurrence date or None if no valid date found
        """
        if pattern == RecurrencePattern.DAILY:
            return base_date + timedelta(days=interval)
            
        elif pattern == RecurrencePattern.WEEKLY:
            if not days_of_week:
                return None
                
            # Find next occurrence on specified days of week
            current_day = base_date.weekday()
            days_ahead = []
            
            for target_day in sorted(days_of_week):
                if target_day > current_day:
                    days_ahead.append(target_day - current_day)
                else:
                    # Add days until next week's occurrence
                    days_ahead.append(7 * interval - current_day + target_day)
            
            if days_ahead:
                return base_date + timedelta(days=min(days_ahead))
                
        elif pattern == RecurrencePattern.WEEKDAYS:
            # Skip to next weekday
            next_date = base_date + timedelta(days=1)
            while next_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                next_date += timedelta(days=1)
            return next_date
            
        elif pattern == RecurrencePattern.MONTHLY:
            if not day_of_month:
                return None
                
            # Calculate next month occurrence
            year = base_date.year
            month = base_date.month + interval
            
            while month > 12:
                month -= 12
                year += 1
                
            try:
                return base_date.replace(year=year, month=month, day=day_of_month)
            except ValueError:
                # Handle invalid dates like Feb 31
                # Move to last day of month
                if month == 2:
                    # Check for leap year
                    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                        return base_date.replace(year=year, month=month, day=29)
                    else:
                        return base_date.replace(year=year, month=month, day=28)
                elif month in [4, 6, 9, 11]:
                    return base_date.replace(year=year, month=month, day=30)
                    
        elif pattern == RecurrencePattern.YEARLY:
            if not day_of_month or not month_of_year:
                return None
                
            year = base_date.year + interval
            try:
                return base_date.replace(year=year, month=month_of_year, day=day_of_month)
            except ValueError:
                # Handle leap year edge case
                if month_of_year == 2 and day_of_month == 29:
                    return base_date.replace(year=year, month=month_of_year, day=28)
                    
        return None
    
    @staticmethod
    def should_create_next_occurrence(
        task: Task,
        current_date: datetime
    ) -> bool:
        """
        Check if a new occurrence should be created for a recurring task.
        """
        if not task.is_recurring:
            return False
            
        # Check if recurrence has ended
        if task.recurrence_end_date and current_date > task.recurrence_end_date:
            return False
            
        # Check occurrence count
        if task.recurrence_count:
            # Count existing instances
            instance_count = len([t for t in task.recurrence_instances if t.id != task.id])
            if instance_count >= task.recurrence_count:
                return False
                
        return True
    
    @staticmethod
    def create_recurring_instance(
        db: Session,
        parent_task: Task,
        occurrence_date: datetime
    ) -> Task:
        """
        Create a new instance of a recurring task.
        """
        # Create new task instance
        new_task = Task(
            id=str(uuid.uuid4()),
            title=parent_task.title,
            description=parent_task.description,
            status=TaskStatus.TODO,
            priority=parent_task.priority,
            user_id=parent_task.user_id,
            project_id=parent_task.project_id,
            assigned_to_id=parent_task.assigned_to_id,
            estimated_hours=parent_task.estimated_hours,
            position=parent_task.position,
            # Set dates based on occurrence
            start_date=occurrence_date if parent_task.start_date else None,
            due_date=None,
            # Link to parent recurring task
            recurrence_parent_id=parent_task.id,
            # Not a recurring task itself
            is_recurring=False
        )
        
        # Calculate due date if original had one
        if parent_task.due_date and parent_task.start_date:
            # Maintain the same duration between start and due dates
            duration = parent_task.due_date - parent_task.start_date
            new_task.due_date = occurrence_date + duration
        elif parent_task.due_date:
            # If no start date, just set due date to occurrence date
            new_task.due_date = occurrence_date
            
        db.add(new_task)
        
        # Copy categories
        for category in parent_task.categories:
            new_task.categories.append(category)
            
        # Copy tags
        for tag in parent_task.tags:
            new_task.tags.append(tag)
            
        return new_task
    
    @staticmethod
    def create_task_with_recurrence(
        db: Session,
        task_data: Dict[str, Any],
        recurrence_config: RecurrenceConfig,
        user_id: str
    ) -> Task:
        """
        Create a task with recurrence configuration.
        """
        # Create the parent recurring task
        task = Task(
            id=str(uuid.uuid4()),
            user_id=user_id,
            is_recurring=True,
            recurrence_pattern=recurrence_config.pattern,
            recurrence_interval=recurrence_config.interval,
            recurrence_end_date=recurrence_config.end_date,
            recurrence_count=recurrence_config.count,
            **task_data
        )
        
        # Set pattern-specific fields
        if recurrence_config.pattern == RecurrencePattern.WEEKLY and recurrence_config.days_of_week:
            task.recurrence_days_of_week = ','.join(map(str, recurrence_config.days_of_week))
        elif recurrence_config.pattern == RecurrencePattern.MONTHLY and recurrence_config.day_of_month:
            task.recurrence_day_of_month = recurrence_config.day_of_month
        elif recurrence_config.pattern == RecurrencePattern.YEARLY:
            task.recurrence_day_of_month = recurrence_config.day_of_month
            task.recurrence_month_of_year = recurrence_config.month_of_year
            
        db.add(task)
        db.flush()
        
        return task
    
    @staticmethod
    def update_recurrence(
        db: Session,
        task: Task,
        recurrence_config: RecurrenceConfig
    ) -> Task:
        """
        Update recurrence configuration for a task.
        """
        if not task.is_recurring:
            # Convert to recurring task
            task.is_recurring = True
            
        # Update recurrence fields
        task.recurrence_pattern = recurrence_config.pattern
        task.recurrence_interval = recurrence_config.interval
        task.recurrence_end_date = recurrence_config.end_date
        task.recurrence_count = recurrence_config.count
        
        # Clear previous pattern-specific fields
        task.recurrence_days_of_week = None
        task.recurrence_day_of_month = None
        task.recurrence_month_of_year = None
        
        # Set new pattern-specific fields
        if recurrence_config.pattern == RecurrencePattern.WEEKLY and recurrence_config.days_of_week:
            task.recurrence_days_of_week = ','.join(map(str, recurrence_config.days_of_week))
        elif recurrence_config.pattern == RecurrencePattern.MONTHLY and recurrence_config.day_of_month:
            task.recurrence_day_of_month = recurrence_config.day_of_month
        elif recurrence_config.pattern == RecurrencePattern.YEARLY:
            task.recurrence_day_of_month = recurrence_config.day_of_month
            task.recurrence_month_of_year = recurrence_config.month_of_year
            
        return task
    
    @staticmethod
    def delete_recurrence(
        db: Session,
        task: Task,
        delete_instances: bool = False
    ) -> None:
        """
        Remove recurrence from a task.
        
        Args:
            db: Database session
            task: The recurring task
            delete_instances: Whether to delete future instances
        """
        if not task.is_recurring:
            return
            
        # Remove recurrence configuration
        task.is_recurring = False
        task.recurrence_pattern = None
        task.recurrence_interval = None
        task.recurrence_days_of_week = None
        task.recurrence_day_of_month = None
        task.recurrence_month_of_year = None
        task.recurrence_end_date = None
        task.recurrence_count = None
        
        if delete_instances:
            # Delete uncompleted future instances
            for instance in task.recurrence_instances:
                if instance.status != TaskStatus.DONE:
                    db.delete(instance)
    
    @staticmethod
    def get_recurring_tasks_to_process(
        db: Session,
        current_date: datetime
    ) -> List[Task]:
        """
        Get recurring tasks that need processing for creating new instances.
        This would be called by a background job.
        """
        # Get all active recurring tasks
        recurring_tasks = db.query(Task).filter(
            Task.is_recurring == True,
            Task.recurrence_parent_id == None  # Only parent tasks
        ).all()
        
        tasks_to_process = []
        
        for task in recurring_tasks:
            if RecurrenceService.should_create_next_occurrence(task, current_date):
                # Check if we need to create a new instance
                # This logic would depend on your business requirements
                # For example, create instances X days in advance
                tasks_to_process.append(task)
                
        return tasks_to_process
    
    @staticmethod
    def process_recurring_tasks(db: Session):
        """Process recurring tasks - Now handled by Celery periodic task."""
        # This method is replaced by the Celery periodic task
        # app.tasks.recurring.process_recurring_tasks
        logger.warning("process_recurring_tasks called directly - this should be handled by Celery periodic task")
        
        # For backward compatibility, we can queue the Celery task
        from app.core.celery_app import celery_app
        celery_app.send_task('app.tasks.recurring.process_recurring_tasks')
        logger.info("Queued recurring task processing")
    
    @staticmethod
    def should_create_next_instance(db: Session, task_id: str) -> bool:
        """
        Check if a new instance should be created for a recurring task.
        Enhanced version that checks for existing instances.
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
            
        if not task.is_recurring or not task.recurrence_pattern:
            return False
            
        # Check if recurrence has ended
        if task.recurrence_end_date and datetime.now(timezone.utc) > task.recurrence_end_date:
            return False
            
        # Check occurrence count
        if task.recurrence_count:
            # Count existing instances
            instance_count = db.query(Task).filter(
                Task.recurrence_parent_id == task_id
            ).count()
            if instance_count >= task.recurrence_count:
                return False
        
        # Check if we already have a pending instance for the next occurrence
        # Get the last created instance
        last_instance = db.query(Task).filter(
            Task.recurrence_parent_id == task_id
        ).order_by(Task.created_at.desc()).first()
        
        if last_instance and last_instance.status != TaskStatus.DONE:
            # We already have a pending instance
            return False
            
        return True
    
    @staticmethod
    def create_next_instance(db: Session, task_id: str) -> Optional[Task]:
        """
        Create the next instance of a recurring task if needed.
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task or not RecurrenceService.should_create_next_instance(db, task_id):
            return None
            
        # Calculate the next occurrence date
        base_date = datetime.now(timezone.utc)
        
        # If we have previous instances, base the next occurrence on the last one
        last_instance = db.query(Task).filter(
            Task.recurrence_parent_id == task_id
        ).order_by(Task.created_at.desc()).first()
        
        if last_instance and last_instance.due_date:
            base_date = last_instance.due_date
        elif task.due_date:
            base_date = task.due_date
            
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date,
            task.recurrence_pattern,
            task.recurrence_interval or 1,
            [int(x) for x in task.recurrence_days_of_week.split(',')] if task.recurrence_days_of_week else None,
            task.recurrence_day_of_month,
            task.recurrence_month_of_year
        )
        
        if not next_date:
            return None
            
        # Create the new instance
        new_instance = RecurrenceService.create_recurring_instance(db, task, next_date)
        db.commit()
        
        return new_instance