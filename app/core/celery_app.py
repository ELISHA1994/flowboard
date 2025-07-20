"""
Celery application configuration for background task processing.
"""
import os
from celery import Celery
from kombu import Exchange, Queue

from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "task_manager",
    broker=settings.get_celery_broker_url(),
    backend=settings.get_celery_result_backend(),
    include=[
        "app.tasks.notifications",
        "app.tasks.recurring",
        "app.tasks.webhooks",
        "app.tasks.analytics",
        "app.tasks.reminders",
    ]
)

# Configure Celery
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.notifications.*": {"queue": "notifications"},
        "app.tasks.recurring.*": {"queue": "recurring"},
        "app.tasks.webhooks.*": {"queue": "webhooks"},
        "app.tasks.analytics.*": {"queue": "analytics"},
        "app.tasks.reminders.*": {"queue": "reminders"},
    },
    
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_always_eager=settings.is_testing,  # Run tasks synchronously in tests
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    
    # Result backend
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "retry_on_timeout": True,
        "retry_policy": {
            "timeout": 5.0
        }
    },
    
    # Worker configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Broker configuration
    broker_url=settings.get_celery_broker_url(),
    broker_transport_options={
        "retry_on_timeout": True,
        "retry_policy": {
            "timeout": 5.0
        }
    },
    
    # Queue definitions
    task_default_queue="default",
    task_default_exchange="default",
    task_default_exchange_type="direct",
    task_default_routing_key="default",
    
    task_queues=[
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("notifications", Exchange("notifications"), routing_key="notifications"),
        Queue("recurring", Exchange("recurring"), routing_key="recurring"),
        Queue("webhooks", Exchange("webhooks"), routing_key="webhooks"),
        Queue("analytics", Exchange("analytics"), routing_key="analytics"),
        Queue("reminders", Exchange("reminders"), routing_key="reminders"),
    ],
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Security
    worker_hijack_root_logger=False,
    worker_log_color=False,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "process-recurring-tasks": {
            "task": "app.tasks.recurring.process_recurring_tasks",
            "schedule": float(settings.RECURRING_TASK_CHECK_INTERVAL),
            "options": {"queue": "recurring"}
        },
        "send-reminder-notifications": {
            "task": "app.tasks.reminders.send_reminder_notifications",
            "schedule": float(settings.REMINDER_CHECK_INTERVAL),
            "options": {"queue": "reminders"}
        },
        "cleanup-expired-notifications": {
            "task": "app.tasks.notifications.cleanup_expired_notifications",
            "schedule": float(settings.NOTIFICATION_CLEANUP_INTERVAL),
            "options": {"queue": "notifications"}
        },
        "compute-analytics-cache": {
            "task": "app.tasks.analytics.precompute_analytics",
            "schedule": float(settings.ANALYTICS_CACHE_INTERVAL),
            "options": {"queue": "analytics"}
        },
    },
    beat_schedule_filename="celerybeat-schedule",
)

# Configure logging
if not settings.is_testing:
    celery_app.conf.update(
        worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
        worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    )


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup."""
    print(f'Request: {self.request!r}')
    return "Debug task completed successfully"


def get_celery_app():
    """Get the Celery application instance."""
    return celery_app