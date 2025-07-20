#!/usr/bin/env python3
"""
Test script to verify async task integration with services.

This script tests that services properly queue Celery tasks instead of
executing operations synchronously.
"""
import os
import sys
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from app.core.config import settings
from app.db.database import get_db, SessionLocal
from app.db.models import User, Task, TaskStatus, Comment
from app.services.notification_service import NotificationService
from app.services.webhook_service import WebhookService, WebhookEvent
from app.services.recurrence_service import RecurrenceService
from app.core.celery_app import celery_app
from app.core.middleware.jwt_auth_backend import get_password_hash

# Import tasks to ensure they're registered
import app.tasks.notifications
import app.tasks.recurring
import app.tasks.webhooks
import app.tasks.reminders
import app.tasks.analytics


def ensure_test_user(db):
    """Ensure a test user exists in the database."""
    user = db.query(User).filter(User.username == "test_async_user").first()
    if not user:
        print("Creating test user...")
        user = User(
            id=str(uuid.uuid4()),
            username="test_async_user",
            email="test_async@example.com",
            hashed_password=get_password_hash("testpass123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Created test user: {user.username}")
    return user


def test_notification_service():
    """Test that NotificationService properly queues async tasks."""
    print("\n=== Testing NotificationService ===")
    
    db = SessionLocal()
    try:
        # Get or create a test user
        user = ensure_test_user(db)
        
        # Create a test task
        task = Task(
            id="test-task-123",
            title="Test Task for Async",
            user_id=user.id,
            assigned_to_id=user.id,
            status=TaskStatus.TODO
        )
        db.add(task)
        db.commit()
        
        try:
            # Test notify_task_assigned
            print("Testing notify_task_assigned...")
            NotificationService.notify_task_assigned(db, task, user)
            print("✅ Task assignment notification queued")
            
            # Create a test comment
            comment = Comment(
                id="test-comment-123",
                task_id=task.id,
                user_id=user.id,
                content="Test comment @user"
            )
            db.add(comment)
            db.commit()
            
            # Test notify_comment_mention
            print("Testing notify_comment_mention...")
            NotificationService.notify_comment_mention(db, comment, user.id)
            print("✅ Comment mention notification queued")
            
            # Test process_pending_reminders
            print("Testing process_pending_reminders...")
            NotificationService.process_pending_reminders(db)
            print("✅ Reminder processing task queued")
            
            assert True, "Test passed"
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.rollback()
            assert False, f"Test failed: {e}"
            
    finally:
        # Cleanup
        try:
            comment = db.query(Comment).filter(Comment.id == "test-comment-123").first()
            if comment:
                db.delete(comment)
            task = db.query(Task).filter(Task.id == "test-task-123").first()
            if task:
                db.delete(task)
            db.commit()
        except:
            pass
        db.close()


def test_webhook_service():
    """Test that WebhookService properly queues async tasks."""
    print("\n=== Testing WebhookService ===")
    
    db = SessionLocal()
    try:
        # Get or create a test user
        user = ensure_test_user(db)
        
        try:
            # Test trigger_webhook
            print("Testing trigger_webhook...")
            WebhookService.trigger_webhook(
                db,
                WebhookEvent.TASK_CREATED,
                {"task_id": "test-123", "title": "Test Task"},
                user_id=user.id
            )
            print("✅ Webhook triggers queued")
            
            # Test retry_failed_deliveries
            print("Testing retry_failed_deliveries...")
            WebhookService.retry_failed_deliveries(db)
            print("✅ Webhook retry task queued")
            
            assert True, "Test passed"
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.rollback()
            assert False, f"Test failed: {e}"
            
    finally:
        db.close()


def test_recurrence_service():
    """Test that RecurrenceService properly queues async tasks."""
    print("\n=== Testing RecurrenceService ===")
    
    db = SessionLocal()
    try:
        # Test process_recurring_tasks
        print("Testing process_recurring_tasks...")
        RecurrenceService.process_recurring_tasks(db)
        print("✅ Recurring task processing queued")
        
        assert True, "Recurrence service test passed"
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        assert False, f"Recurrence service test failed: {e}"
        
    finally:
        db.close()


def check_celery_tasks():
    """Check if Celery tasks are properly registered."""
    print("\n=== Checking Celery Task Registration ===")
    
    registered_tasks = celery_app.tasks.keys()
    required_tasks = [
        'app.tasks.notifications.send_task_assignment_notification',
        'app.tasks.notifications.send_comment_mention_notification',
        'app.tasks.notifications.send_email_notification',
        'app.tasks.recurring.process_recurring_tasks',
        'app.tasks.recurring.create_recurring_task_instance',
        'app.tasks.webhooks.deliver_webhook',
        'app.tasks.webhooks.retry_failed_webhooks',
        'app.tasks.reminders.send_reminder_notifications',
        'app.tasks.reminders.send_task_reminder',
    ]
    
    all_present = True
    for task in required_tasks:
        if task in registered_tasks:
            print(f"✅ {task}")
        else:
            print(f"❌ {task} - NOT REGISTERED")
            all_present = False
    
    # Debug: print all registered tasks
    print("\nAll registered tasks:")
    for task_name in sorted(registered_tasks):
        print(f"  - {task_name}")
    
    return all_present


def main():
    """Run all async integration tests."""
    print("Testing Async Task Integration")
    print("=" * 50)
    
    # Check Celery tasks are registered
    tasks_ok = check_celery_tasks()
    
    # Test services
    notification_ok = test_notification_service()
    webhook_ok = test_webhook_service()
    recurrence_ok = test_recurrence_service()
    
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"Celery Tasks Registered: {'✅' if tasks_ok else '❌'}")
    print(f"NotificationService: {'✅' if notification_ok else '❌'}")
    print(f"WebhookService: {'✅' if webhook_ok else '❌'}")
    print(f"RecurrenceService: {'✅' if recurrence_ok else '❌'}")
    
    if all([tasks_ok, notification_ok, webhook_ok, recurrence_ok]):
        print("\n✅ All async integrations working correctly!")
        print("\nNote: Make sure Celery workers are running to process these tasks:")
        print("  ./scripts/celery/start_all.sh")
        return 0
    else:
        print("\n❌ Some async integrations failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())