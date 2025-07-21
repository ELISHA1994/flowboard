"""
Background tasks for logging task activities asynchronously.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.database import get_celery_db
from app.db.models import ActivityType
from app.db.models import Task as TaskModel
from app.db.models import TaskActivity, User
from app.services.activity_service import ActivityService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, queue="default")
def log_activity_async(
    self,
    task_id: str,
    user_id: Optional[str],
    activity_type: str,
    details: Optional[Dict[str, Any]] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """
    Log a task activity asynchronously.

    This is the main entry point for async activity logging.
    """
    try:
        with get_celery_db() as db:
            # Convert string activity_type back to enum
            activity_type_enum = ActivityType(activity_type)

            activity = ActivityService.log_activity(
                db=db,
                task_id=task_id,
                user_id=user_id,
                activity_type=activity_type_enum,
                details=details,
                old_value=old_value,
                new_value=new_value,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(
                f"Successfully logged activity {activity_type} for task {task_id}"
            )
            return {"success": True, "activity_id": activity.id}

    except Exception as e:
        logger.error(
            f"Failed to log activity {activity_type} for task {task_id}: {str(e)}"
        )
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def log_task_created_async(
    self,
    task_id: str,
    user_id: str,
    task_data: Dict[str, Any],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log task creation activity asynchronously."""
    try:
        with get_celery_db() as db:
            activity = ActivityService.log_task_created(
                db=db,
                task_id=task_id,
                user_id=user_id,
                task_data=task_data,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(f"Successfully logged task creation for task {task_id}")
            return {"success": True, "activity_id": activity.id}

    except Exception as e:
        logger.error(f"Failed to log task creation for task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def log_status_change_async(
    self,
    task_id: str,
    user_id: str,
    old_status: str,
    new_status: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log task status change activity asynchronously."""
    try:
        with get_celery_db() as db:
            activity = ActivityService.log_status_change(
                db=db,
                task_id=task_id,
                user_id=user_id,
                old_status=old_status,
                new_status=new_status,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(
                f"Successfully logged status change for task {task_id}: {old_status} -> {new_status}"
            )
            return {"success": True, "activity_id": activity.id}

    except Exception as e:
        logger.error(f"Failed to log status change for task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def log_priority_change_async(
    self,
    task_id: str,
    user_id: str,
    old_priority: str,
    new_priority: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log task priority change activity asynchronously."""
    try:
        with get_celery_db() as db:
            activity = ActivityService.log_priority_change(
                db=db,
                task_id=task_id,
                user_id=user_id,
                old_priority=old_priority,
                new_priority=new_priority,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(
                f"Successfully logged priority change for task {task_id}: {old_priority} -> {new_priority}"
            )
            return {"success": True, "activity_id": activity.id}

    except Exception as e:
        logger.error(f"Failed to log priority change for task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def log_assignment_change_async(
    self,
    task_id: str,
    user_id: str,
    old_assignee_id: Optional[str],
    new_assignee_id: Optional[str],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log task assignment change activity asynchronously."""
    try:
        with get_celery_db() as db:
            activity = ActivityService.log_assignment_change(
                db=db,
                task_id=task_id,
                user_id=user_id,
                old_assignee_id=old_assignee_id,
                new_assignee_id=new_assignee_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(f"Successfully logged assignment change for task {task_id}")
            return {"success": True, "activity_id": activity.id}

    except Exception as e:
        logger.error(f"Failed to log assignment change for task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def log_due_date_change_async(
    self,
    task_id: str,
    user_id: str,
    old_due_date: Optional[str],  # ISO format string
    new_due_date: Optional[str],  # ISO format string
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log task due date change activity asynchronously."""
    try:
        with get_celery_db() as db:
            # Convert ISO strings back to datetime objects
            old_dt = (
                datetime.fromisoformat(old_due_date.replace("Z", "+00:00"))
                if old_due_date
                else None
            )
            new_dt = (
                datetime.fromisoformat(new_due_date.replace("Z", "+00:00"))
                if new_due_date
                else None
            )

            activity = ActivityService.log_due_date_change(
                db=db,
                task_id=task_id,
                user_id=user_id,
                old_due_date=old_dt,
                new_due_date=new_dt,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(f"Successfully logged due date change for task {task_id}")
            return {"success": True, "activity_id": activity.id}

    except Exception as e:
        logger.error(f"Failed to log due date change for task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def log_title_change_async(
    self,
    task_id: str,
    user_id: str,
    old_title: str,
    new_title: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log task title change activity asynchronously."""
    try:
        with get_celery_db() as db:
            activity = ActivityService.log_title_change(
                db=db,
                task_id=task_id,
                user_id=user_id,
                old_title=old_title,
                new_title=new_title,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(f"Successfully logged title change for task {task_id}")
            return {"success": True, "activity_id": activity.id}

    except Exception as e:
        logger.error(f"Failed to log title change for task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def log_description_change_async(
    self,
    task_id: str,
    user_id: str,
    old_description: Optional[str],
    new_description: Optional[str],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log task description change activity asynchronously."""
    try:
        with get_celery_db() as db:
            activity = ActivityService.log_description_change(
                db=db,
                task_id=task_id,
                user_id=user_id,
                old_description=old_description,
                new_description=new_description,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(f"Successfully logged description change for task {task_id}")
            return {"success": True, "activity_id": activity.id}

    except Exception as e:
        logger.error(f"Failed to log description change for task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def log_comment_added_async(
    self,
    task_id: str,
    user_id: str,
    comment_id: str,
    comment_content: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log comment addition activity asynchronously."""
    print(
        f"[CELERY TASK] Starting log_comment_added_async for task {task_id}, user {user_id}, comment {comment_id}"
    )
    logger.info(
        f"Starting log_comment_added_async for task {task_id}, user {user_id}, comment {comment_id}"
    )

    try:
        print(f"[CELERY TASK] Getting database session...")
        with get_celery_db() as db:
            logger.info(f"Got database session for task {task_id}")
            print(f"[CELERY TASK] Got database session for task {task_id}")

            activity = ActivityService.log_comment_added(
                db=db,
                task_id=task_id,
                user_id=user_id,
                comment_id=comment_id,
                comment_content=comment_content,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(
                f"ActivityService.log_comment_added returned activity {activity.id} for task {task_id}"
            )
            print(
                f"[CELERY TASK] ActivityService.log_comment_added returned activity {activity.id}"
            )

            # Note: get_celery_db() automatically commits on successful completion
            logger.info(
                f"Transaction will be committed by context manager for activity {activity.id}"
            )
            print(
                f"[CELERY TASK] Transaction will be committed by context manager for activity {activity.id}"
            )

        logger.info(
            f"Successfully logged comment addition for task {task_id}, activity_id: {activity.id}"
        )
        print(
            f"[CELERY TASK] SUCCESS! Logged comment addition for task {task_id}, activity_id: {activity.id}"
        )
        return {"success": True, "activity_id": activity.id}

    except Exception as e:
        logger.error(
            f"Failed to log comment addition for task {task_id}: {str(e)}",
            exc_info=True,
        )
        print(f"[CELERY TASK] ERROR! Failed to log comment addition: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def log_attachment_added_async(
    self,
    task_id: str,
    user_id: str,
    attachment_id: str,
    filename: str,
    file_size: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log file attachment activity asynchronously."""
    try:
        with get_celery_db() as db:
            activity = ActivityService.log_attachment_added(
                db=db,
                task_id=task_id,
                user_id=user_id,
                attachment_id=attachment_id,
                filename=filename,
                file_size=file_size,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(f"Successfully logged attachment addition for task {task_id}")
            return {"success": True, "activity_id": activity.id}

    except Exception as e:
        logger.error(f"Failed to log attachment addition for task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def log_time_logged_async(
    self,
    task_id: str,
    user_id: str,
    hours: float,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log time tracking activity asynchronously."""
    try:
        with get_celery_db() as db:
            activity = ActivityService.log_time_logged(
                db=db,
                task_id=task_id,
                user_id=user_id,
                hours=hours,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(
                f"Successfully logged time tracking for task {task_id}: {hours} hours"
            )
            return {"success": True, "activity_id": activity.id}

    except Exception as e:
        logger.error(f"Failed to log time tracking for task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def log_subtask_added_async(
    self,
    task_id: str,
    user_id: str,
    subtask_id: str,
    subtask_title: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log subtask addition activity asynchronously."""
    try:
        with get_celery_db() as db:
            activity = ActivityService.log_subtask_added(
                db=db,
                task_id=task_id,
                user_id=user_id,
                subtask_id=subtask_id,
                subtask_title=subtask_title,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(f"Successfully logged subtask addition for task {task_id}")
            return {"success": True, "activity_id": activity.id}

    except Exception as e:
        logger.error(f"Failed to log subtask addition for task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def log_task_completed_async(
    self,
    task_id: str,
    user_id: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log task completion activity asynchronously."""
    try:
        with get_celery_db() as db:
            activity = ActivityService.log_task_completed(
                db=db,
                task_id=task_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(f"Successfully logged task completion for task {task_id}")
            return {"success": True, "activity_id": activity.id}

    except Exception as e:
        logger.error(f"Failed to log task completion for task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def log_task_shared_async(
    self,
    task_id: str,
    user_id: str,
    shared_with_user_id: str,
    permission: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log task sharing activity asynchronously."""
    try:
        with get_celery_db() as db:
            activity = ActivityService.log_task_shared(
                db=db,
                task_id=task_id,
                user_id=user_id,
                shared_with_user_id=shared_with_user_id,
                permission=permission,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(f"Successfully logged task sharing for task {task_id}")
            return {"success": True, "activity_id": activity.id}

    except Exception as e:
        logger.error(f"Failed to log task sharing for task {task_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def log_bulk_activities_async(self, activities: List[Dict[str, Any]]):
    """Log multiple activities in bulk for better performance."""
    try:
        with get_celery_db() as db:
            results = []

            for activity_data in activities:
                try:
                    activity_type = ActivityType(activity_data["activity_type"])

                    activity = ActivityService.log_activity(
                        db=db,
                        task_id=activity_data["task_id"],
                        user_id=activity_data.get("user_id"),
                        activity_type=activity_type,
                        details=activity_data.get("details"),
                        old_value=activity_data.get("old_value"),
                        new_value=activity_data.get("new_value"),
                        ip_address=activity_data.get("ip_address"),
                        user_agent=activity_data.get("user_agent"),
                    )

                    results.append({"success": True, "activity_id": activity.id})

                except Exception as e:
                    logger.error(f"Failed to log bulk activity: {str(e)}")
                    results.append({"success": False, "error": str(e)})

            logger.info(
                f"Processed {len(activities)} bulk activities, {sum(1 for r in results if r['success'])} successful"
            )
            return {"success": True, "results": results}

    except Exception as e:
        logger.error(f"Failed to process bulk activities: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="default")
def cleanup_old_activities_async(self, days: int = 365):
    """Clean up old activity records asynchronously."""
    try:
        with get_celery_db() as db:
            deleted_count = ActivityService.cleanup_old_activities(db, days)

            logger.info(f"Successfully cleaned up {deleted_count} old activity records")
            return {"success": True, "deleted_count": deleted_count}

    except Exception as e:
        logger.error(f"Failed to cleanup old activities: {str(e)}")
        raise self.retry(countdown=300, max_retries=3)


# Convenience functions for easier task queuing


def queue_activity_log(
    task_id: str,
    user_id: Optional[str],
    activity_type: ActivityType,
    details: Optional[Dict[str, Any]] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Queue an activity log task asynchronously."""
    return log_activity_async.delay(
        task_id=task_id,
        user_id=user_id,
        activity_type=activity_type.value,
        details=details,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def queue_status_change_log(
    task_id: str,
    user_id: str,
    old_status: str,
    new_status: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Queue a status change activity log task."""
    return log_status_change_async.delay(
        task_id=task_id,
        user_id=user_id,
        old_status=old_status,
        new_status=new_status,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def queue_task_creation_log(
    task_id: str,
    user_id: str,
    task_data: Dict[str, Any],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Queue a task creation activity log task."""
    return log_task_created_async.delay(
        task_id=task_id,
        user_id=user_id,
        task_data=task_data,
        ip_address=ip_address,
        user_agent=user_agent,
    )
