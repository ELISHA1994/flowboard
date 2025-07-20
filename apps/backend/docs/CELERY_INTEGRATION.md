# Celery Integration Documentation

## Overview

This document describes the Celery integration for background task processing in the Task Management API.

## Architecture

### Celery Configuration
- **Broker**: Redis (using existing Redis instance)
- **Result Backend**: Redis
- **Task Serialization**: JSON
- **Timezone**: UTC

### Task Queues
The following queues are configured for different types of tasks:
- `default` - General purpose tasks
- `notifications` - Email and in-app notifications
- `recurring` - Processing recurring tasks
- `webhooks` - Webhook deliveries
- `analytics` - Analytics computation and reports
- `reminders` - Task reminders and summaries

## Background Tasks

### Notification Tasks (`app.tasks.notifications`)
- `send_task_assignment_notification` - Sends notification when a task is assigned
- `send_comment_mention_notification` - Sends notification for @mentions in comments
- `send_email_notification` - Generic email sending task
- `cleanup_expired_notifications` - Periodic task to clean old notifications

### Recurring Task Processing (`app.tasks.recurring`)
- `process_recurring_tasks` - Periodic task to check and create recurring task instances
- `create_recurring_task_instance` - Creates a new instance of a recurring task
- `update_recurring_task_template` - Updates recurring task template and future instances
- `cleanup_completed_recurring_instances` - Archives/deletes old completed instances

### Webhook Delivery (`app.tasks.webhooks`)
- `deliver_webhook` - Delivers webhook to a subscription URL with retry logic
- `retry_failed_webhooks` - Periodic task to retry failed webhook deliveries
- `cleanup_old_webhook_deliveries` - Periodic task to clean old delivery records

### Reminders (`app.tasks.reminders`)
- `send_reminder_notifications` - Periodic task to process due reminders
- `send_task_reminder` - Sends individual task reminder
- `send_daily_task_summary` - Sends daily task summary to users
- `send_weekly_productivity_report` - Sends weekly productivity reports

### Analytics (`app.tasks.analytics`)
- `compute_user_analytics` - Computes analytics for a specific user
- `compute_project_analytics` - Computes analytics for a project
- `precompute_analytics` - Periodic task to precompute analytics cache
- `export_tasks_async` - Exports tasks to CSV/Excel in background

## Service Integration

### NotificationService
- `notify_task_assigned()` - Queues `send_task_assignment_notification` task
- `notify_comment_mention()` - Queues `send_comment_mention_notification` task
- `process_pending_reminders()` - Queues `send_reminder_notifications` task

### WebhookService
- `trigger_webhook()` - Queues `deliver_webhook` tasks for each subscription
- `retry_failed_deliveries()` - Queues `retry_failed_webhooks` task

### RecurrenceService
- `process_recurring_tasks()` - Queues `process_recurring_tasks` task
- Enhanced methods for checking and creating recurring instances

## Periodic Tasks (Celery Beat)

The following tasks run automatically when the beat scheduler is active:

| Task | Schedule | Description |
|------|----------|-------------|
| Process Recurring Tasks | Every 5 minutes | Creates new instances of recurring tasks |
| Send Reminder Notifications | Every 15 minutes | Sends task reminders |
| Cleanup Expired Notifications | Every hour | Removes old notifications |
| Precompute Analytics Cache | Every 30 minutes | Updates analytics cache |
| Retry Failed Webhooks | Every 10 minutes | Retries failed webhook deliveries |
| Cleanup Old Webhook Deliveries | Daily at 2 AM | Removes old webhook records |

## Running Celery

### Start All Infrastructure
```bash
./scripts/celery/start_all.sh
```

### Start Individual Components
```bash
# Start a worker
./scripts/celery/start_worker.sh

# Start beat scheduler
./scripts/celery/start_beat.sh

# Monitor tasks
./scripts/celery/monitor.sh watch
```

### Testing
```bash
# Test Celery configuration
python scripts/test_celery.py

# Test async integration
python scripts/test_async_integration.py
```

## Benefits

1. **Performance**: Long-running operations don't block API requests
2. **Reliability**: Failed tasks can be retried automatically
3. **Scalability**: Can scale workers independently based on queue load
4. **Monitoring**: Built-in task monitoring and status tracking
5. **Scheduling**: Periodic tasks run automatically without cron jobs

## Error Handling

- Tasks implement retry logic with exponential backoff
- Failed tasks are logged with detailed error information
- Database tasks use proper session management with rollback on errors
- Webhook deliveries track retry count and failure reasons

## Security Considerations

- Task serialization uses JSON (not pickle) for security
- Webhook signatures use HMAC-SHA256 for verification
- Sensitive data is not logged in task arguments
- Database connections are properly managed per task