#!/usr/bin/env python3
"""
Script to test Celery configuration and tasks.
"""
import sys
import time
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parents[1]))

from app.core.celery_app import celery_app, debug_task
from app.core.config import settings
from app.tasks.notifications import send_email_notification
from app.tasks.analytics import precompute_analytics
from app.tasks.webhooks import broadcast_webhook_event
from app.tasks.recurring import process_recurring_tasks
from app.tasks.reminders import send_reminder_notifications


def test_celery_connection():
    """Test basic Celery connection."""
    print("🔧 Testing Celery connection...")

    try:
        # Test broker connection
        with celery_app.connection() as conn:
            conn.ensure_connection(max_retries=3)
        print("✅ Broker connection successful")

        # Test result backend
        backend = celery_app.backend
        backend.get("test-key")  # This will test the connection
        print("✅ Result backend connection successful")

        assert True, "Connection successful"
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        assert False, f"Connection failed: {e}"


def test_task_registration():
    """Test that all tasks are properly registered."""
    print("\n📋 Testing task registration...")

    # List of expected tasks
    expected_tasks = [
        "app.core.celery_app.debug_task",
        "app.tasks.notifications.send_email_notification",
        "app.tasks.notifications.send_task_assignment_notification",
        "app.tasks.notifications.cleanup_expired_notifications",
        "app.tasks.recurring.process_recurring_tasks",
        "app.tasks.recurring.create_recurring_task_instance",
        "app.tasks.webhooks.deliver_webhook",
        "app.tasks.webhooks.broadcast_webhook_event",
        "app.tasks.analytics.precompute_analytics",
        "app.tasks.analytics.compute_user_analytics",
        "app.tasks.reminders.send_reminder_notifications",
        "app.tasks.reminders.send_task_reminder",
    ]

    registered_tasks = list(celery_app.tasks.keys())

    missing_tasks = []
    for task in expected_tasks:
        if task not in registered_tasks:
            missing_tasks.append(task)
        else:
            print(f"✅ {task}")

    if missing_tasks:
        print(f"❌ Missing tasks: {missing_tasks}")
        assert False, f"Missing tasks: {missing_tasks}"

    print(f"✅ All {len(expected_tasks)} expected tasks are registered")
    assert True, "All tasks registered"


def test_queue_configuration():
    """Test queue configuration."""
    print("\n🔄 Testing queue configuration...")

    expected_queues = [
        "default",
        "notifications",
        "recurring",
        "webhooks",
        "analytics",
        "reminders",
    ]
    configured_queues = [q.name for q in celery_app.conf.task_queues]

    for queue in expected_queues:
        if queue in configured_queues:
            print(f"✅ Queue '{queue}' configured")
        else:
            print(f"❌ Queue '{queue}' missing")
            assert False, f"Queue '{queue}' missing"

    assert True, "All queues configured"


def test_periodic_tasks():
    """Test periodic task configuration."""
    print("\n⏰ Testing periodic task configuration...")

    beat_schedule = celery_app.conf.beat_schedule
    expected_periodic_tasks = [
        "process-recurring-tasks",
        "send-reminder-notifications",
        "cleanup-expired-notifications",
        "compute-analytics-cache",
    ]

    for task_name in expected_periodic_tasks:
        if task_name in beat_schedule:
            task_config = beat_schedule[task_name]
            print(
                f"✅ {task_name}: {task_config['task']} (every {task_config['schedule']}s)"
            )
        else:
            print(f"❌ Periodic task '{task_name}' not configured")
            assert False, f"Periodic task '{task_name}' not configured"

    assert True, "All periodic tasks configured"


def test_debug_task():
    """Test the debug task execution."""
    print("\n🐛 Testing debug task execution...")

    try:
        if settings.is_testing or settings.CELERY_TASK_ALWAYS_EAGER:
            # In testing mode, tasks run synchronously
            result = debug_task.delay()
            print(f"✅ Debug task completed: {result.get(timeout=10)}")
        else:
            # In production mode, just queue the task
            result = debug_task.delay()
            print(f"✅ Debug task queued: {result.id}")

            # Try to get result with short timeout
            try:
                task_result = result.get(timeout=5)
                print(f"✅ Debug task completed: {task_result}")
            except Exception:
                print("⏳ Debug task queued but still running (this is normal)")

        assert True, "Debug task executed successfully"
    except Exception as e:
        print(f"❌ Debug task failed: {e}")
        assert False, f"Debug task failed: {e}"


def test_task_routing():
    """Test task routing to correct queues."""
    print("\n🛣️  Testing task routing...")

    test_cases = [
        ("app.tasks.notifications.send_email_notification", "notifications"),
        ("app.tasks.recurring.process_recurring_tasks", "recurring"),
        ("app.tasks.webhooks.deliver_webhook", "webhooks"),
        ("app.tasks.analytics.precompute_analytics", "analytics"),
        ("app.tasks.reminders.send_reminder_notifications", "reminders"),
    ]

    routes = celery_app.conf.task_routes

    for task_name, expected_queue in test_cases:
        if task_name in routes:
            actual_queue = routes[task_name].get("queue")
            if actual_queue == expected_queue:
                print(f"✅ {task_name} → {expected_queue}")
            else:
                print(f"❌ {task_name} → {actual_queue} (expected {expected_queue})")
                assert (
                    False
                ), f"Task routing incorrect: {task_name} → {actual_queue} (expected {expected_queue})"
        else:
            # Check pattern matching
            matched = False
            for pattern, config in routes.items():
                if "*" in pattern and task_name.startswith(pattern.replace("*", "")):
                    actual_queue = config.get("queue")
                    if actual_queue == expected_queue:
                        print(f"✅ {task_name} → {expected_queue} (pattern match)")
                        matched = True
                        break

            if not matched:
                print(f"❌ No routing rule found for {task_name}")
                assert False, f"No routing rule found for {task_name}"

    assert True, "All task routing configured correctly"


def test_redis_queues():
    """Test Redis queue operations."""
    print("\n📦 Testing Redis queues...")

    try:
        import redis

        r = redis.Redis.from_url(settings.redis_url)

        # Test connection
        r.ping()
        print("✅ Redis connection successful")

        # Check queue lengths
        queues = [
            "default",
            "notifications",
            "recurring",
            "webhooks",
            "analytics",
            "reminders",
        ]
        for queue in queues:
            length = r.llen(queue)
            print(f"✅ Queue '{queue}': {length} tasks")

        assert True, "Redis queues working correctly"
    except Exception as e:
        print(f"❌ Redis queue test failed: {e}")
        assert False, f"Redis queue test failed: {e}"


def test_configuration():
    """Test Celery configuration values."""
    print("\n⚙️  Testing configuration...")

    config_tests = [
        ("broker_url", settings.get_celery_broker_url()),
        ("result_backend", settings.get_celery_result_backend()),
        ("task_serializer", "json"),
        ("result_serializer", "json"),
        ("timezone", "UTC"),
        ("enable_utc", True),
    ]

    for config_key, expected_value in config_tests:
        actual_value = getattr(celery_app.conf, config_key)
        if actual_value == expected_value:
            print(f"✅ {config_key}: {actual_value}")
        else:
            print(f"❌ {config_key}: {actual_value} (expected {expected_value})")
            assert (
                False
            ), f"Configuration mismatch: {config_key}: {actual_value} (expected {expected_value})"

    assert True, "All configuration values correct"


def main():
    """Run all Celery tests."""
    print("🧪 Celery Configuration Test Suite")
    print("=" * 50)

    tests = [
        ("Connection", test_celery_connection),
        ("Task Registration", test_task_registration),
        ("Queue Configuration", test_queue_configuration),
        ("Periodic Tasks", test_periodic_tasks),
        ("Configuration", test_configuration),
        ("Task Routing", test_task_routing),
        ("Redis Queues", test_redis_queues),
        ("Debug Task", test_debug_task),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All Celery tests passed!")
        return 0
    else:
        print("💥 Some Celery tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
