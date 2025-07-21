"""
Background tasks for processing recurring tasks.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from celery import Task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.database import get_db
from app.db.models import Task as TaskModel
from app.db.models import TaskStatus
from app.services.recurrence_service import RecurrenceService

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task class that provides database session."""

    def __call__(self, *args, **kwargs):
        with get_db() as db:
            return self.run_with_db(db, *args, **kwargs)

    def run_with_db(self, db: Session, *args, **kwargs):
        """Override this method instead of run()"""
        raise NotImplementedError


@celery_app.task(bind=True, base=DatabaseTask, queue="recurring")
def process_recurring_tasks(self, db: Session):
    """Main periodic task to process all recurring tasks that need new instances."""
    try:
        now = datetime.now(timezone.utc)
        logger.info(f"Processing recurring tasks at {now}")

        # Get all active recurring tasks that might need new instances
        recurring_tasks = (
            db.query(TaskModel)
            .filter(
                TaskModel.is_recurring == True, TaskModel.recurrence_pattern.isnot(None)
            )
            .all()
        )

        created_count = 0
        processed_count = 0

        for task in recurring_tasks:
            try:
                # Check if this task needs a new instance
                if RecurrenceService.should_create_next_instance(db, task.id):
                    # Create the next instance asynchronously
                    create_recurring_task_instance.delay(task.id)
                    created_count += 1

                processed_count += 1

            except Exception as e:
                logger.error(f"Error processing recurring task {task.id}: {str(e)}")
                continue

        logger.info(
            f"Processed {processed_count} recurring tasks, queued {created_count} new instances"
        )
        return {
            "success": True,
            "processed_count": processed_count,
            "created_count": created_count,
            "timestamp": now.isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to process recurring tasks: {str(e)}")
        raise self.retry(countdown=300, max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="recurring")
def create_recurring_task_instance(self, db: Session, task_id: str):
    """Create a new instance of a recurring task."""
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            logger.warning(f"Recurring task {task_id} not found")
            return {"success": False, "reason": "Task not found"}

        if not task.is_recurring or not task.recurrence_pattern:
            logger.warning(f"Task {task_id} is not a recurring task")
            return {"success": False, "reason": "Not a recurring task"}

        # Use the recurrence service to create the next instance
        new_task = RecurrenceService.create_next_instance(db, task_id)

        if new_task:
            logger.info(
                f"Created new recurring task instance {new_task.id} from template {task_id}"
            )

            # If the task is assigned to someone, send a notification
            if new_task.assigned_to_id:
                from app.tasks.notifications import \
                    send_task_assignment_notification

                send_task_assignment_notification.delay(
                    new_task.id,
                    new_task.assigned_to_id,
                    new_task.user_id,  # Creator/owner assigns the task
                )

            return {
                "success": True,
                "new_task_id": new_task.id,
                "template_task_id": task_id,
            }
        else:
            logger.info(f"No new instance needed for recurring task {task_id}")
            return {"success": True, "reason": "No new instance needed"}

    except Exception as e:
        logger.error(
            f"Failed to create recurring task instance for {task_id}: {str(e)}"
        )
        raise self.retry(countdown=120, max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="recurring")
def update_recurring_task_template(
    self, db: Session, task_id: str, updates: Dict[str, Any]
):
    """Update a recurring task template and optionally apply changes to future instances."""
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            logger.warning(f"Recurring task template {task_id} not found")
            return {"success": False, "reason": "Task not found"}

        if not task.is_recurring:
            logger.warning(f"Task {task_id} is not a recurring task template")
            return {"success": False, "reason": "Not a recurring task"}

        # Update the template
        for field, value in updates.items():
            if hasattr(task, field):
                setattr(task, field, value)

        task.updated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"Updated recurring task template {task_id}")

        # Optionally update future instances
        apply_to_future = updates.get("apply_to_future_instances", False)
        if apply_to_future:
            # Find future instances (tasks with due_date in the future)
            future_instances = (
                db.query(TaskModel)
                .filter(
                    TaskModel.parent_task_id == task_id,
                    TaskModel.due_date > datetime.now(timezone.utc),
                    TaskModel.status == TaskStatus.TODO,  # Only update pending tasks
                )
                .all()
            )

            updated_instances = 0
            for instance in future_instances:
                for field, value in updates.items():
                    if field not in [
                        "apply_to_future_instances",
                        "id",
                        "created_at",
                        "parent_task_id",
                    ]:
                        if hasattr(instance, field):
                            setattr(instance, field, value)

                instance.updated_at = datetime.now(timezone.utc)
                updated_instances += 1

            db.commit()
            logger.info(
                f"Updated {updated_instances} future instances of recurring task {task_id}"
            )

            return {
                "success": True,
                "template_updated": True,
                "future_instances_updated": updated_instances,
            }

        return {
            "success": True,
            "template_updated": True,
            "future_instances_updated": 0,
        }

    except Exception as e:
        logger.error(f"Failed to update recurring task template {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="recurring")
def cleanup_completed_recurring_instances(
    self, db: Session, task_id: str, keep_last_n: int = 10
):
    """Clean up old completed instances of a recurring task, keeping the last N."""
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task or not task.is_recurring:
            logger.warning(f"Task {task_id} is not a recurring task template")
            return {"success": False, "reason": "Not a recurring task"}

        # Find completed instances, ordered by completion date (oldest first)
        completed_instances = (
            db.query(TaskModel)
            .filter(
                TaskModel.parent_task_id == task_id,
                TaskModel.status == TaskStatus.DONE,
                TaskModel.completed_at.isnot(None),
            )
            .order_by(TaskModel.completed_at.desc())
            .all()
        )

        # Keep the last N completed instances, delete the rest
        if len(completed_instances) > keep_last_n:
            instances_to_delete = completed_instances[keep_last_n:]
            deleted_count = 0

            for instance in instances_to_delete:
                # Check if the instance has any dependencies or important data
                # before deleting (comments, time logs, etc.)
                if instance.comments or instance.time_logs or instance.attachments:
                    # Archive instead of delete
                    instance.archived = True
                    instance.archived_at = datetime.now(timezone.utc)
                else:
                    # Safe to delete
                    db.delete(instance)
                    deleted_count += 1

            db.commit()

            archived_count = len(instances_to_delete) - deleted_count
            logger.info(
                f"Cleaned up recurring task {task_id}: deleted {deleted_count}, archived {archived_count}"
            )

            return {
                "success": True,
                "deleted_count": deleted_count,
                "archived_count": archived_count,
                "kept_count": keep_last_n,
            }

        return {
            "success": True,
            "deleted_count": 0,
            "archived_count": 0,
            "kept_count": len(completed_instances),
        }

    except Exception as e:
        logger.error(
            f"Failed to cleanup recurring task instances for {task_id}: {str(e)}"
        )
        raise self.retry(countdown=300, max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="recurring")
def pause_recurring_task(self, db: Session, task_id: str):
    """Pause a recurring task (stop creating new instances)."""
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            logger.warning(f"Task {task_id} not found")
            return {"success": False, "reason": "Task not found"}

        if not task.is_recurring:
            logger.warning(f"Task {task_id} is not a recurring task")
            return {"success": False, "reason": "Not a recurring task"}

        # Update task to pause recurrence
        if task.recurrence_pattern:
            # We can use a field to track if recurrence is paused
            # For now, we'll set recurrence_end_date to pause
            task.recurrence_end_date = datetime.now(timezone.utc)
            task.updated_at = datetime.now(timezone.utc)
            db.commit()

            logger.info(f"Paused recurring task {task_id}")
            return {"success": True, "action": "paused"}

        return {"success": False, "reason": "No recurrence pattern found"}

    except Exception as e:
        logger.error(f"Failed to pause recurring task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="recurring")
def resume_recurring_task(self, db: Session, task_id: str):
    """Resume a paused recurring task."""
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            logger.warning(f"Task {task_id} not found")
            return {"success": False, "reason": "Task not found"}

        if not task.is_recurring:
            logger.warning(f"Task {task_id} is not a recurring task")
            return {"success": False, "reason": "Not a recurring task"}

        # Update task to resume recurrence
        if task.recurrence_pattern:
            # Clear the end date to resume
            task.recurrence_end_date = None
            task.updated_at = datetime.now(timezone.utc)
            db.commit()

            logger.info(f"Resumed recurring task {task_id}")

            # Check if we need to create any missed instances
            if RecurrenceService.should_create_next_instance(db, task_id):
                create_recurring_task_instance.delay(task_id)

            return {"success": True, "action": "resumed"}

        return {"success": False, "reason": "No recurrence pattern found"}

    except Exception as e:
        logger.error(f"Failed to resume recurring task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="recurring")
def batch_create_recurring_instances(self, db: Session, task_ids: List[str]):
    """Create instances for multiple recurring tasks in batch."""
    try:
        results = []

        for task_id in task_ids:
            try:
                if RecurrenceService.should_create_next_instance(db, task_id):
                    result = create_recurring_task_instance.delay(task_id)
                    results.append(
                        {
                            "task_id": task_id,
                            "celery_task_id": result.id,
                            "status": "queued",
                        }
                    )
                else:
                    results.append({"task_id": task_id, "status": "no_instance_needed"})
            except Exception as e:
                logger.error(f"Error queuing recurring task {task_id}: {str(e)}")
                results.append({"task_id": task_id, "status": "error", "error": str(e)})

        logger.info(f"Batch created recurring instances for {len(task_ids)} tasks")
        return {"success": True, "results": results}

    except Exception as e:
        logger.error(f"Failed to batch create recurring instances: {str(e)}")
        raise self.retry(countdown=120, max_retries=3)
