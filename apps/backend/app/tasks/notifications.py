"""
Background tasks for sending notifications and emails.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from celery import Task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.database import get_db
from app.db.models import Notification
from app.db.models import Task as TaskModel
from app.db.models import User
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task class that provides database session."""

    def __call__(self, *args, **kwargs):
        with get_db() as db:
            return self.run_with_db(db, *args, **kwargs)

    def run_with_db(self, db: Session, *args, **kwargs):
        """Override this method instead of run()"""
        raise NotImplementedError


@celery_app.task(bind=True, base=DatabaseTask, queue="notifications")
def send_email_notification(
    self,
    recipient_email: str,
    subject: str,
    content: str,
    notification_type: str = "info",
):
    """Send an email notification asynchronously."""
    try:
        logger.info(f"Sending email notification to {recipient_email}: {subject}")

        # For now, just log the email (in production, integrate with email service)
        logger.info(f"EMAIL TO: {recipient_email}")
        logger.info(f"SUBJECT: {subject}")
        logger.info(f"CONTENT: {content}")
        logger.info(f"TYPE: {notification_type}")

        # In production, integrate with SendGrid, AWS SES, or similar service
        # Example:
        # import sendgrid
        # sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        # from_email = Email("noreply@yourdomain.com")
        # to_email = To(recipient_email)
        # mail_content = Content("text/html", content)
        # mail = Mail(from_email, to_email, subject, mail_content)
        # response = sg.client.mail.send.post(request_body=mail.get())

        return {"success": True, "recipient": recipient_email, "subject": subject}

    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="notifications")
def send_task_assignment_notification(
    self, task_id: str, assigned_to_id: str, assigned_by_id: str
):
    """Send notification when a task is assigned to a user."""
    try:
        with get_db() as db:
            task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
            assigned_to = db.query(User).filter(User.id == assigned_to_id).first()
            assigned_by = db.query(User).filter(User.id == assigned_by_id).first()

            if not task or not assigned_to or not assigned_by:
                logger.warning(
                    f"Missing data for task assignment notification: task={task_id}, assigned_to={assigned_to_id}, assigned_by={assigned_by_id}"
                )
                return {"success": False, "reason": "Missing data"}

            # Create in-app notification
            notification = Notification(
                user_id=assigned_to_id,
                type="task_assigned",
                title="New Task Assigned",
                message=f"You have been assigned the task '{task.title}' by {assigned_by.username}",
                data=json.dumps(
                    {
                        "task_id": task_id,
                        "assigned_by": assigned_by.username,
                        "task_title": task.title,
                    }
                ),
            )
            db.add(notification)
            db.commit()

            # Send email notification if user has email notifications enabled
            # (Check user preferences in production)
            subject = f"New Task Assigned: {task.title}"
            content = f"""
            <h2>New Task Assigned</h2>
            <p>Hello {assigned_to.username},</p>
            <p>You have been assigned a new task by {assigned_by.username}:</p>
            <h3>{task.title}</h3>
            <p><strong>Description:</strong> {task.description or 'No description provided'}</p>
            <p><strong>Priority:</strong> {task.priority.value}</p>
            <p><strong>Due Date:</strong> {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No due date set'}</p>
            <p>Log in to view and manage your tasks.</p>
            """

            # Queue email sending
            send_email_notification.delay(
                assigned_to.email, subject, content, "task_assigned"
            )

            logger.info(
                f"Task assignment notification sent for task {task_id} to user {assigned_to_id}"
            )
            return {"success": True, "notification_id": notification.id}

    except Exception as e:
        logger.error(f"Failed to send task assignment notification: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="notifications")
def send_task_reminder_notification(self, db: Session, task_id: str, user_id: str):
    """Send reminder notification for a task that's due soon."""
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        user = db.query(User).filter(User.id == user_id).first()

        if not task or not user:
            logger.warning(
                f"Missing data for task reminder: task={task_id}, user={user_id}"
            )
            return {"success": False, "reason": "Missing data"}

        # Create in-app notification
        notification = Notification(
            user_id=user_id,
            type="task_reminder",
            title="Task Reminder",
            message=f"Reminder: Task '{task.title}' is due {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'soon'}",
            data={
                "task_id": task_id,
                "task_title": task.title,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            },
        )
        db.add(notification)
        db.commit()

        # Send email reminder
        subject = f"Task Reminder: {task.title}"
        content = f"""
        <h2>Task Reminder</h2>
        <p>Hello {user.username},</p>
        <p>This is a reminder about your task:</p>
        <h3>{task.title}</h3>
        <p><strong>Description:</strong> {task.description or 'No description provided'}</p>
        <p><strong>Priority:</strong> {task.priority.value}</p>
        <p><strong>Due Date:</strong> {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No due date set'}</p>
        <p><strong>Status:</strong> {task.status.value}</p>
        <p>Log in to update your task progress.</p>
        """

        send_email_notification.delay(user.email, subject, content, "task_reminder")

        logger.info(
            f"Task reminder notification sent for task {task_id} to user {user_id}"
        )
        return {"success": True, "notification_id": notification.id}

    except Exception as e:
        logger.error(f"Failed to send task reminder notification: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="notifications")
def send_project_invitation_notification(
    self, db: Session, project_id: str, invited_user_id: str, inviter_id: str
):
    """Send notification when a user is invited to a project."""
    try:
        from app.db.models import Project

        project = db.query(Project).filter(Project.id == project_id).first()
        invited_user = db.query(User).filter(User.id == invited_user_id).first()
        inviter = db.query(User).filter(User.id == inviter_id).first()

        if not project or not invited_user or not inviter:
            logger.warning(
                f"Missing data for project invitation: project={project_id}, invited_user={invited_user_id}, inviter={inviter_id}"
            )
            return {"success": False, "reason": "Missing data"}

        # Create in-app notification
        notification = Notification(
            user_id=invited_user_id,
            type="project_invitation",
            title="Project Invitation",
            message=f"You have been invited to join the project '{project.name}' by {inviter.username}",
            data={
                "project_id": project_id,
                "project_name": project.name,
                "inviter": inviter.username,
            },
        )
        db.add(notification)
        db.commit()

        # Send email notification
        subject = f"Project Invitation: {project.name}"
        content = f"""
        <h2>Project Invitation</h2>
        <p>Hello {invited_user.username},</p>
        <p>You have been invited to join a project:</p>
        <h3>{project.name}</h3>
        <p><strong>Description:</strong> {project.description or 'No description provided'}</p>
        <p><strong>Invited by:</strong> {inviter.username}</p>
        <p>Log in to accept or decline this invitation.</p>
        """

        send_email_notification.delay(
            invited_user.email, subject, content, "project_invitation"
        )

        logger.info(
            f"Project invitation notification sent for project {project_id} to user {invited_user_id}"
        )
        return {"success": True, "notification_id": notification.id}

    except Exception as e:
        logger.error(f"Failed to send project invitation notification: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="notifications")
def cleanup_expired_notifications(self, db: Session):
    """Clean up old read notifications."""
    try:
        # Delete read notifications older than 30 days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

        deleted_count = (
            db.query(Notification)
            .filter(
                Notification.read_at.isnot(None), Notification.created_at < cutoff_date
            )
            .delete()
        )

        db.commit()

        logger.info(f"Cleaned up {deleted_count} expired notifications")
        return {"success": True, "deleted_count": deleted_count}

    except Exception as e:
        logger.error(f"Failed to cleanup expired notifications: {str(e)}")
        raise self.retry(countdown=300, max_retries=3)


@celery_app.task(bind=True, queue="notifications")
def send_comment_mention_notification(self, comment_id: str, mentioned_user_id: str):
    """Send notification when a user is mentioned in a comment."""
    try:
        with get_db() as db:
            from app.db.models import Comment

            comment = db.query(Comment).filter(Comment.id == comment_id).first()
            mentioned_user = db.query(User).filter(User.id == mentioned_user_id).first()

            if not comment or not mentioned_user:
                logger.warning(
                    f"Missing data for mention notification: comment={comment_id}, mentioned_user={mentioned_user_id}"
                )
                return {"success": False, "reason": "Missing data"}

            # Get the task this comment belongs to
            task = comment.task
            commenter = comment.user

            # Create in-app notification
            notification = Notification(
                user_id=mentioned_user_id,
                type="comment_mention",
                title="You were mentioned",
                message=f"{commenter.username} mentioned you in a comment on task '{task.title}'",
                data=json.dumps(
                    {
                        "comment_id": comment_id,
                        "task_id": task.id,
                        "task_title": task.title,
                        "commenter": commenter.username,
                    }
                ),
            )
            db.add(notification)
            db.commit()

            # Send email notification
            subject = f"You were mentioned in a comment on '{task.title}'"
            content = f"""
            <h2>You were mentioned</h2>
            <p>Hello {mentioned_user.username},</p>
            <p>{commenter.username} mentioned you in a comment on the task '{task.title}':</p>
            <blockquote>{comment.content}</blockquote>
            <p>Log in to view the full conversation and respond.</p>
            """

            send_email_notification.delay(
                mentioned_user.email, subject, content, "comment_mention"
            )

            logger.info(
                f"Comment mention notification sent for comment {comment_id} to user {mentioned_user_id}"
            )
            return {"success": True, "notification_id": notification.id}

    except Exception as e:
        logger.error(f"Failed to send comment mention notification: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, queue="notifications")
def send_bulk_notifications(self, notification_data_list: List[Dict[str, Any]]):
    """Send multiple notifications in bulk for better performance."""
    try:
        results = []

        for notification_data in notification_data_list:
            notification_type = notification_data.get("type")

            if notification_type == "task_assigned":
                result = send_task_assignment_notification.delay(
                    notification_data["task_id"],
                    notification_data["assigned_to_id"],
                    notification_data["assigned_by_id"],
                )
            elif notification_type == "task_reminder":
                result = send_task_reminder_notification.delay(
                    notification_data["task_id"], notification_data["user_id"]
                )
            elif notification_type == "project_invitation":
                result = send_project_invitation_notification.delay(
                    notification_data["project_id"],
                    notification_data["invited_user_id"],
                    notification_data["inviter_id"],
                )
            elif notification_type == "comment_mention":
                result = send_comment_mention_notification.delay(
                    notification_data["comment_id"],
                    notification_data["mentioned_user_id"],
                )
            else:
                logger.warning(f"Unknown notification type: {notification_type}")
                continue

            results.append(result.id)

        logger.info(f"Queued {len(results)} bulk notifications")
        return {"success": True, "queued_tasks": results}

    except Exception as e:
        logger.error(f"Failed to send bulk notifications: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)
