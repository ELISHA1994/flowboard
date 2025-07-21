"""
Integration tests for recurring task endpoints.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import RecurrencePattern, Task, TaskStatus, User


class TestCreateRecurringTask:
    """Test creating recurring tasks"""

    def test_create_daily_recurring_task(
        self, test_client: TestClient, test_user_token: str
    ):
        """Test creating a daily recurring task"""
        task_data = {
            "title": "Daily Standup",
            "description": "Daily team standup meeting",
            "priority": "medium",
            "start_date": "2025-01-01T09:00:00Z",
            "due_date": "2025-01-01T09:30:00Z",
            "recurrence": {
                "pattern": "daily",
                "interval": 1,
                "end_date": "2025-12-31T23:59:59Z",
            },
        }

        response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 201
        task = response.json()
        assert task["title"] == "Daily Standup"
        assert task["is_recurring"] is True
        assert task["recurrence_pattern"] == "daily"
        assert task["recurrence_interval"] == 1
        assert task["recurrence_end_date"] == "2025-12-31T23:59:59"

    def test_create_weekly_recurring_task(
        self, test_client: TestClient, test_user_token: str
    ):
        """Test creating a weekly recurring task"""
        task_data = {
            "title": "Weekly Review",
            "description": "Weekly team review meeting",
            "priority": "high",
            "start_date": "2025-01-06T14:00:00Z",  # Monday
            "due_date": "2025-01-06T15:00:00Z",
            "recurrence": {
                "pattern": "weekly",
                "interval": 1,
                "days_of_week": [0, 2, 4],  # Mon, Wed, Fri
                "count": 12,  # 12 occurrences
            },
        }

        response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 201
        task = response.json()
        assert task["recurrence_pattern"] == "weekly"
        assert task["recurrence_days_of_week"] == "0,2,4"
        assert task["recurrence_count"] == 12

    def test_create_monthly_recurring_task(
        self, test_client: TestClient, test_user_token: str
    ):
        """Test creating a monthly recurring task"""
        task_data = {
            "title": "Monthly Report",
            "description": "Prepare monthly report",
            "priority": "high",
            "due_date": "2025-01-15T17:00:00Z",
            "recurrence": {"pattern": "monthly", "interval": 1, "day_of_month": 15},
        }

        response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 201
        task = response.json()
        assert task["recurrence_pattern"] == "monthly"
        assert task["recurrence_day_of_month"] == 15

    def test_create_yearly_recurring_task(
        self, test_client: TestClient, test_user_token: str
    ):
        """Test creating a yearly recurring task"""
        task_data = {
            "title": "Annual Review",
            "description": "Annual performance review",
            "priority": "urgent",
            "due_date": "2025-12-15T09:00:00Z",
            "recurrence": {
                "pattern": "yearly",
                "interval": 1,
                "day_of_month": 15,
                "month_of_year": 12,
            },
        }

        response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 201
        task = response.json()
        assert task["recurrence_pattern"] == "yearly"
        assert task["recurrence_day_of_month"] == 15
        assert task["recurrence_month_of_year"] == 12

    def test_create_weekdays_recurring_task(
        self, test_client: TestClient, test_user_token: str
    ):
        """Test creating a weekdays recurring task"""
        task_data = {
            "title": "Check Emails",
            "description": "Check and respond to emails",
            "priority": "medium",
            "start_date": "2025-01-06T08:00:00Z",
            "due_date": "2025-01-06T08:30:00Z",
            "recurrence": {"pattern": "weekdays", "interval": 1},
        }

        response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 201
        task = response.json()
        assert task["recurrence_pattern"] == "weekdays"

    def test_create_recurring_task_invalid_config(
        self, test_client: TestClient, test_user_token: str
    ):
        """Test creating recurring task with invalid configuration"""
        # Weekly without days_of_week
        task_data = {
            "title": "Invalid Weekly",
            "description": "Missing days_of_week",
            "recurrence": {"pattern": "weekly", "interval": 1},
        }

        response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 422
        assert "days_of_week must be provided" in response.text

        # Both end_date and count
        task_data = {
            "title": "Invalid End Config",
            "description": "Both end_date and count",
            "recurrence": {
                "pattern": "daily",
                "interval": 1,
                "end_date": "2025-12-31T23:59:59Z",
                "count": 10,
            },
        }

        response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 422
        assert "Cannot specify both end_date and count" in response.text


class TestUpdateRecurringTask:
    """Test updating recurring tasks"""

    def test_update_recurrence_pattern(
        self, test_client: TestClient, test_user_token: str
    ):
        """Test updating recurrence pattern"""
        # Create a daily recurring task
        task_data = {
            "title": "Recurring Task",
            "description": "Test recurring task",
            "recurrence": {"pattern": "daily", "interval": 1},
        }

        create_response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # Update to weekly
        update_data = {
            "recurrence": {"pattern": "weekly", "interval": 1, "days_of_week": [1, 3]}
        }

        response = test_client.put(
            f"/tasks/{task_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        updated_task = response.json()
        assert updated_task["recurrence_pattern"] == "weekly"
        assert updated_task["recurrence_days_of_week"] == "1,3"
        assert updated_task["is_recurring"] is True

    def test_remove_recurrence(self, test_client: TestClient, test_user_token: str):
        """Test removing recurrence from a task"""
        # Create a recurring task
        task_data = {
            "title": "Recurring Task",
            "description": "Test recurring task",
            "recurrence": {"pattern": "daily", "interval": 1},
        }

        create_response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # Remove recurrence
        update_data = {"recurrence": None}

        response = test_client.put(
            f"/tasks/{task_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        updated_task = response.json()
        assert updated_task["is_recurring"] is False
        assert updated_task["recurrence_pattern"] is None


class TestRecurringTaskInstances:
    """Test recurring task instances endpoints"""

    def test_get_recurring_task_instances(
        self, test_client: TestClient, test_user_token: str, test_db: Session
    ):
        """Test getting all instances of a recurring task"""
        # Create a recurring task
        task_data = {
            "title": "Daily Task",
            "description": "Test daily task",
            "recurrence": {"pattern": "daily", "interval": 1},
        }

        create_response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert create_response.status_code == 201
        parent_task = create_response.json()
        parent_id = parent_task["id"]

        # Create some instances manually (simulating background job)
        from app.services.recurrence_service import RecurrenceService

        parent_task_db = test_db.query(Task).filter(Task.id == parent_id).first()

        for i in range(3):
            occurrence_date = datetime.now(timezone.utc) + timedelta(days=i + 1)
            instance = RecurrenceService.create_recurring_instance(
                test_db, parent_task_db, occurrence_date
            )
            test_db.commit()

        # Get all instances
        response = test_client.get(
            f"/tasks/{parent_id}/recurrence/instances",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        instances = response.json()
        assert len(instances) == 4  # Parent + 3 instances
        assert all(task["title"] == "Daily Task" for task in instances)

        # Check parent is first
        assert instances[0]["id"] == parent_id
        assert instances[0]["is_recurring"] is True

        # Check instances
        for i in range(1, 4):
            assert instances[i]["recurrence_parent_id"] == parent_id
            assert instances[i]["is_recurring"] is False

    def test_get_instances_non_recurring_task(
        self, test_client: TestClient, test_user_token: str, test_task: Task
    ):
        """Test getting instances of non-recurring task"""
        response = test_client.get(
            f"/tasks/{test_task.id}/recurrence/instances",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 400
        error_data = response.json()
        assert "not a recurring task" in (
            error_data.get("detail", "") or error_data.get("message", "")
        )

    def test_get_instances_permission_denied(
        self, test_client: TestClient, test_user_token: str, second_user_token: str
    ):
        """Test getting instances without permission"""
        # Create a recurring task as first user
        task_data = {
            "title": "Private Recurring Task",
            "recurrence": {"pattern": "daily", "interval": 1},
        }

        create_response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # Try to get instances as second user
        response = test_client.get(
            f"/tasks/{task_id}/recurrence/instances",
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        assert response.status_code == 403


class TestNextOccurrence:
    """Test next occurrence calculation endpoint"""

    def test_get_next_occurrence_daily(
        self, test_client: TestClient, test_user_token: str
    ):
        """Test getting next occurrence for daily task"""
        # Create a daily recurring task
        task_data = {
            "title": "Daily Task",
            "recurrence": {"pattern": "daily", "interval": 2},
        }

        create_response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # Get next occurrence
        reference_date = "2025-01-01T10:00:00Z"
        response = test_client.post(
            f"/tasks/{task_id}/recurrence/next-occurrence",
            params={"reference_date": reference_date},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["pattern"] == "daily"
        assert result["interval"] == 2
        # Should be 2 days later
        assert result["next_occurrence"] in [
            "2025-01-03T10:00:00",
            "2025-01-03T10:00:00+00:00",
        ]

    def test_get_next_occurrence_weekly(
        self, test_client: TestClient, test_user_token: str
    ):
        """Test getting next occurrence for weekly task"""
        # Create a weekly recurring task
        task_data = {
            "title": "Weekly Task",
            "recurrence": {
                "pattern": "weekly",
                "interval": 1,
                "days_of_week": [2, 4],  # Wednesday and Friday
            },
        }

        create_response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # Get next occurrence from Monday
        reference_date = "2025-01-06T10:00:00Z"  # Monday
        response = test_client.post(
            f"/tasks/{task_id}/recurrence/next-occurrence",
            params={"reference_date": reference_date},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        result = response.json()
        # Next should be Wednesday
        assert result["next_occurrence"] in [
            "2025-01-08T10:00:00",
            "2025-01-08T10:00:00+00:00",
        ]

    def test_get_next_occurrence_non_recurring(
        self, test_client: TestClient, test_user_token: str, test_task: Task
    ):
        """Test getting next occurrence for non-recurring task"""
        response = test_client.post(
            f"/tasks/{test_task.id}/recurrence/next-occurrence",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 400
        error_data = response.json()
        assert "not a recurring task" in (
            error_data.get("detail", "") or error_data.get("message", "")
        )


class TestDeleteRecurrence:
    """Test delete recurrence endpoint"""

    def test_delete_recurrence_keep_instances(
        self, test_client: TestClient, test_user_token: str
    ):
        """Test deleting recurrence but keeping instances"""
        # Create a recurring task
        task_data = {
            "title": "Recurring Task",
            "recurrence": {"pattern": "daily", "interval": 1},
        }

        create_response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # Delete recurrence
        response = test_client.delete(
            f"/tasks/{task_id}/recurrence",
            params={"delete_instances": False},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["message"] == "Recurrence removed successfully"
        assert result["instances_deleted"] is False

        # Verify task is no longer recurring
        task_response = test_client.get(
            f"/tasks/{task_id}", headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert task_response.status_code == 200
        task = task_response.json()
        assert task["is_recurring"] is False

    def test_delete_recurrence_with_instances(
        self, test_client: TestClient, test_user_token: str, test_db: Session
    ):
        """Test deleting recurrence and instances"""
        # Create a recurring task
        task_data = {
            "title": "Recurring Task",
            "recurrence": {"pattern": "daily", "interval": 1},
        }

        create_response = test_client.post(
            "/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # Create some instances
        from app.services.recurrence_service import RecurrenceService

        parent_task = test_db.query(Task).filter(Task.id == task_id).first()

        for i in range(3):
            occurrence_date = datetime.now(timezone.utc) + timedelta(days=i + 1)
            RecurrenceService.create_recurring_instance(
                test_db, parent_task, occurrence_date
            )
        test_db.commit()

        # Delete recurrence with instances
        response = test_client.delete(
            f"/tasks/{task_id}/recurrence",
            params={"delete_instances": True},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["instances_deleted"] is True

        # Verify instances are deleted
        instances = (
            test_db.query(Task).filter(Task.recurrence_parent_id == task_id).all()
        )
        assert len(instances) == 0

    def test_delete_recurrence_non_recurring(
        self, test_client: TestClient, test_user_token: str, test_task: Task
    ):
        """Test deleting recurrence from non-recurring task"""
        response = test_client.delete(
            f"/tasks/{test_task.id}/recurrence",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 400
        error_data = response.json()
        assert "not a recurring task" in (
            error_data.get("detail", "") or error_data.get("message", "")
        )
