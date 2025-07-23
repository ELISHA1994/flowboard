"""
Integration tests for analytics and reporting endpoints.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import (Category, Project, ProjectRole, Tag, Task,
                           TaskPriority, TaskStatus, TimeLog, User)
from app.services.project_service import ProjectService


class TestAnalyticsEndpoints:
    """Test analytics and reporting endpoints."""

    def test_log_time_to_task(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User,
    ):
        """Test logging time to a task."""
        # Create a task
        task = Task(id="task1", title="Test Task", user_id=test_user.id, actual_hours=0)
        test_db.add(task)
        test_db.commit()

        # Log time
        response = test_client.post(
            "/analytics/tasks/task1/time-log",
            headers=auth_headers,
            json={"hours": 2.5, "description": "Worked on implementation"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["hours"] == 2.5
        assert data["description"] == "Worked on implementation"
        assert data["task_id"] == "task1"
        assert data["user_id"] == test_user.id

        # Verify task's actual hours updated
        task = test_db.query(Task).filter_by(id="task1").first()
        assert task.actual_hours == 2.5

        # Log more time
        response = test_client.post(
            "/analytics/tasks/task1/time-log",
            headers=auth_headers,
            json={"hours": 1.5, "description": "Bug fixes"},
        )
        assert response.status_code == 200

        # Verify cumulative hours
        task = test_db.query(Task).filter_by(id="task1").first()
        assert task.actual_hours == 4.0

    def test_get_task_statistics(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User,
    ):
        """Test getting task statistics."""
        # Create tasks with various statuses and priorities
        now = datetime.now(timezone.utc)
        tasks = [
            Task(
                id="todo1",
                title="Todo Task 1",
                user_id=test_user.id,
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                created_at=now - timedelta(days=5),
            ),
            Task(
                id="todo2",
                title="Todo Task 2",
                user_id=test_user.id,
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                created_at=now - timedelta(days=3),
            ),
            Task(
                id="progress1",
                title="In Progress Task",
                user_id=test_user.id,
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                created_at=now - timedelta(days=2),
            ),
            Task(
                id="done1",
                title="Completed Task",
                user_id=test_user.id,
                status=TaskStatus.DONE,
                priority=TaskPriority.LOW,
                created_at=now - timedelta(days=7),
                completed_at=now - timedelta(days=1),
            ),
            Task(
                id="overdue1",
                title="Overdue Task",
                user_id=test_user.id,
                status=TaskStatus.TODO,
                priority=TaskPriority.URGENT,
                due_date=now - timedelta(days=2),
                created_at=now - timedelta(days=10),
            ),
        ]
        test_db.add_all(tasks)
        test_db.commit()

        # Get statistics
        response = test_client.get("/analytics/statistics", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Verify statistics
        assert data["total_tasks"] == 5
        assert data["tasks_by_status"]["todo"] == 3
        assert data["tasks_by_status"]["in_progress"] == 1
        assert data["tasks_by_status"]["done"] == 1
        assert data["tasks_by_priority"]["low"] == 1
        assert data["tasks_by_priority"]["medium"] == 1
        assert data["tasks_by_priority"]["high"] == 2
        assert data["tasks_by_priority"]["urgent"] == 1
        assert data["completion_rate"] == 20.0  # 1 out of 5
        assert data["overdue_tasks"] == 1

    def test_get_productivity_trends(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User,
    ):
        """Test getting productivity trends."""
        now = datetime.now(timezone.utc)

        # Create tasks and time logs across different periods
        for i in range(4):
            week_start = now - timedelta(weeks=i)

            # Create tasks
            task = Task(
                id=f"task_week{i}",
                title=f"Task Week {i}",
                user_id=test_user.id,
                created_at=week_start,
                completed_at=week_start + timedelta(days=3) if i % 2 == 0 else None,
                status=TaskStatus.DONE if i % 2 == 0 else TaskStatus.IN_PROGRESS,
            )
            test_db.add(task)

            # Add time logs
            if i < 3:  # Add time logs for recent weeks
                time_log = TimeLog(
                    task_id=task.id,
                    user_id=test_user.id,
                    hours=8.0 + i,
                    logged_at=week_start + timedelta(days=2),
                )
                test_db.add(time_log)

        test_db.commit()

        # Get productivity trends
        response = test_client.get(
            "/analytics/productivity-trends?period=week&lookback=4",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["period_type"] == "week"
        assert len(data["trends"]) == 4

        # Verify trends are in chronological order (oldest to newest)
        for i in range(1, 4):
            assert (
                data["trends"][i]["period_start"]
                > data["trends"][i - 1]["period_start"]
            )

    def test_time_tracking_report(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User,
    ):
        """Test time tracking report generation."""
        # Create tasks and time logs
        task1 = Task(id="t1", title="Task 1", user_id=test_user.id)
        task2 = Task(id="t2", title="Task 2", user_id=test_user.id)
        test_db.add_all([task1, task2])
        test_db.commit()

        now = datetime.now(timezone.utc)
        time_logs = [
            TimeLog(
                task_id="t1",
                user_id=test_user.id,
                hours=3.0,
                logged_at=now - timedelta(days=1),
            ),
            TimeLog(task_id="t1", user_id=test_user.id, hours=2.0, logged_at=now),
            TimeLog(task_id="t2", user_id=test_user.id, hours=4.0, logged_at=now),
        ]
        test_db.add_all(time_logs)
        test_db.commit()

        # Get report grouped by task
        response = test_client.post(
            "/analytics/time-tracking/report",
            headers=auth_headers,
            json={"group_by": "task"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["total_hours"] == 9.0
        assert data["group_by"] == "task"
        assert len(data["entries"]) == 2

        # Find task entries
        task1_entry = next(e for e in data["entries"] if e["task_id"] == "t1")
        task2_entry = next(e for e in data["entries"] if e["task_id"] == "t2")

        assert task1_entry["total_hours"] == 5.0
        assert task1_entry["log_count"] == 2
        assert task2_entry["total_hours"] == 4.0
        assert task2_entry["log_count"] == 1

    def test_category_distribution(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User,
    ):
        """Test getting task distribution by categories."""
        # Create categories
        cat1 = Category(id="cat1", name="Work", color="#0000FF", user_id=test_user.id)
        cat2 = Category(
            id="cat2", name="Personal", color="#00FF00", user_id=test_user.id
        )
        test_db.add_all([cat1, cat2])

        # Create tasks with categories
        task1 = Task(id="t1", title="Task 1", user_id=test_user.id)
        task2 = Task(id="t2", title="Task 2", user_id=test_user.id)
        task3 = Task(id="t3", title="Task 3", user_id=test_user.id)

        task1.categories.append(cat1)
        task2.categories.append(cat1)
        task3.categories.append(cat2)

        test_db.add_all([task1, task2, task3])
        test_db.commit()

        # Get distribution
        response = test_client.get(
            "/analytics/category-distribution", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        work_dist = next(d for d in data if d["category_name"] == "Work")
        personal_dist = next(d for d in data if d["category_name"] == "Personal")

        assert work_dist["task_count"] == 2
        assert work_dist["color"] == "#0000FF"
        assert personal_dist["task_count"] == 1
        assert personal_dist["color"] == "#00FF00"

    def test_export_tasks_csv(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User,
    ):
        """Test exporting tasks to CSV format."""
        # Create tasks
        task1 = Task(
            id="t1",
            title="Task 1",
            description="First task",
            user_id=test_user.id,
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
        )
        task2 = Task(
            id="t2",
            title="Task 2",
            description="Second task",
            user_id=test_user.id,
            status=TaskStatus.DONE,
            priority=TaskPriority.MEDIUM,
        )
        test_db.add_all([task1, task2])
        test_db.commit()

        # Export to CSV
        response = test_client.post(
            "/analytics/export", headers=auth_headers, json={"format": "csv"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

        # Verify CSV content
        csv_content = response.text
        lines = csv_content.strip().split("\n")
        assert len(lines) >= 3  # Header + 2 tasks
        assert "ID,Title,Description,Status,Priority" in lines[0]
        assert "t1,Task 1,First task,todo,high" in csv_content
        assert "t2,Task 2,Second task,done,medium" in csv_content

    def test_export_tasks_excel(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User,
    ):
        """Test exporting tasks to Excel format."""
        # Create a task
        task = Task(id="t1", title="Excel Task", user_id=test_user.id)
        test_db.add(task)
        test_db.commit()

        # Export to Excel
        response = test_client.post(
            "/analytics/export", headers=auth_headers, json={"format": "excel"}
        )
        assert response.status_code == 200
        assert (
            response.headers["content-type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert "attachment" in response.headers["content-disposition"]
        assert response.content[:4] == b"PK\x03\x04"  # Excel file signature

    def test_team_performance_report(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User,
        second_user: User,
    ):
        """Test team performance report for a project."""
        # Create project
        project = Project(id="proj1", name="Team Project", owner_id=test_user.id)
        test_db.add(project)
        test_db.commit()

        # Add team member
        ProjectService.add_member(
            test_db, project.id, second_user.id, ProjectRole.MEMBER
        )

        # Create tasks
        task1 = Task(
            id="t1",
            title="Task 1",
            project_id="proj1",
            assigned_to_id=test_user.id,
            user_id=test_user.id,
            status=TaskStatus.DONE,
        )
        task2 = Task(
            id="t2",
            title="Task 2",
            project_id="proj1",
            assigned_to_id=second_user.id,
            user_id=test_user.id,
            status=TaskStatus.IN_PROGRESS,
        )
        test_db.add_all([task1, task2])

        # Add time logs
        time_log = TimeLog(task_id="t1", user_id=test_user.id, hours=5.0)
        test_db.add(time_log)
        test_db.commit()

        # Get team performance
        response = test_client.get(
            f"/analytics/team-performance/{project.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["project_id"] == "proj1"
        assert data["project_name"] == "Team Project"
        assert len(data["team_members"]) == 2

        # Check owner stats
        owner_stats = next(
            m for m in data["team_members"] if m["user_id"] == test_user.id
        )
        assert owner_stats["role"] == "owner"
        assert owner_stats["tasks_assigned"] == 1
        assert owner_stats["tasks_completed"] == 1
        assert owner_stats["hours_logged"] == 5.0

        # Check member stats
        member_stats = next(
            m for m in data["team_members"] if m["user_id"] == second_user.id
        )
        assert member_stats["role"] == "member"
        assert member_stats["tasks_assigned"] == 1
        assert member_stats["tasks_completed"] == 0

    def test_analytics_access_control(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        second_auth_headers: dict,
        test_user: User,
        second_user: User,
    ):
        """Test access control for analytics endpoints."""
        # Create a task owned by test_user
        task = Task(id="private_task", title="Private Task", user_id=test_user.id)
        test_db.add(task)
        test_db.commit()

        # Try to log time as different user - should fail
        response = test_client.post(
            "/analytics/tasks/private_task/time-log",
            headers=second_auth_headers,
            json={"hours": 1.0},
        )
        assert response.status_code == 404

        # Statistics should only show user's own tasks
        response = test_client.get("/analytics/statistics", headers=second_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 0  # No tasks for second user
