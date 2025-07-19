"""
Integration tests for enhanced task endpoints with priority, dates, and time tracking.
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models import User, Task, TaskStatus, TaskPriority
from app.core.middleware.jwt_auth_backend import create_access_token
import uuid


@pytest.mark.integration
class TestEnhancedTaskCreation:
    """Test enhanced task creation with new fields"""
    
    def test_create_task_with_priority(self, test_client: TestClient, test_user: User, auth_headers: dict):
        """Test creating task with priority"""
        task_data = {
            "title": "High Priority Task",
            "description": "This is urgent",
            "priority": "high"
        }
        
        response = test_client.post("/tasks/", json=task_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["priority"] == "high"
        assert data["title"] == "High Priority Task"
    
    def test_create_task_with_dates(self, test_client: TestClient, test_user: User, auth_headers: dict):
        """Test creating task with due date and start date"""
        start_date = datetime.now(timezone.utc)
        due_date = start_date + timedelta(days=7)
        
        task_data = {
            "title": "Scheduled Task",
            "start_date": start_date.isoformat(),
            "due_date": due_date.isoformat(),
            "estimated_hours": 8.5
        }
        
        response = test_client.post("/tasks/", json=task_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["start_date"] is not None
        assert data["due_date"] is not None
        assert data["estimated_hours"] == 8.5
    
    def test_create_task_with_invalid_dates(self, test_client: TestClient, test_user: User, auth_headers: dict):
        """Test validation when due date is before start date"""
        start_date = datetime.now(timezone.utc)
        due_date = start_date - timedelta(days=1)
        
        task_data = {
            "title": "Invalid Date Task",
            "start_date": start_date.isoformat(),
            "due_date": due_date.isoformat()
        }
        
        response = test_client.post("/tasks/", json=task_data, headers=auth_headers)
        
        assert response.status_code == 422
        assert "Due date must be after start date" in str(response.json())


@pytest.mark.integration
class TestTaskTimeTracking:
    """Test task time tracking functionality"""
    
    def test_add_time_to_task(self, test_client: TestClient, test_user: User, test_task: Task, auth_headers: dict):
        """Test adding time to a task"""
        time_data = {"hours_to_add": 2.5}
        
        response = test_client.post(
            f"/tasks/{test_task.id}/time",
            json=time_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["actual_hours"] == 2.5
    
    def test_add_time_invalid_amount(self, test_client: TestClient, test_user: User, test_task: Task, auth_headers: dict):
        """Test validation for invalid time amounts"""
        # Negative hours
        response = test_client.post(
            f"/tasks/{test_task.id}/time",
            json={"hours_to_add": -1},
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Too many hours
        response = test_client.post(
            f"/tasks/{test_task.id}/time",
            json={"hours_to_add": 25},
            headers=auth_headers
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestTaskStatusAndCompletion:
    """Test task status changes and completion tracking"""
    
    def test_mark_task_done_sets_completed_at(self, test_client: TestClient, test_user: User, test_task: Task, auth_headers: dict):
        """Test that marking task as done sets completed_at"""
        update_data = {"status": "done"}
        
        response = test_client.put(
            f"/tasks/{test_task.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["completed_at"] is not None
    
    def test_reopen_task_clears_completed_at(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test that reopening a task clears completed_at"""
        # Create a completed task
        completed_task = Task(
            id=str(uuid.uuid4()),
            title="Completed Task",
            status=TaskStatus.DONE,
            priority=TaskPriority.MEDIUM,
            user_id=test_user.id,
            completed_at=datetime.now(timezone.utc),
            actual_hours=0.0,
            position=0
        )
        test_db.add(completed_task)
        test_db.commit()
        
        # Reopen the task
        update_data = {"status": "todo"}
        
        response = test_client.put(
            f"/tasks/{completed_task.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "todo"
        assert data["completed_at"] is None


@pytest.mark.integration
class TestTaskFiltering:
    """Test enhanced task filtering"""
    
    def test_filter_by_priority(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test filtering tasks by priority"""
        # Create tasks with different priorities
        for priority in [TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH, TaskPriority.URGENT]:
            task = Task(
                id=str(uuid.uuid4()),
                title=f"{priority.value} priority task",
                status=TaskStatus.TODO,
                priority=priority,
                user_id=test_user.id,
                actual_hours=0.0,
                position=0
            )
            test_db.add(task)
        test_db.commit()
        
        # Filter by high priority
        response = test_client.get("/tasks/?priority=high", headers=auth_headers)
        
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 1
        assert all(task["priority"] == "high" for task in tasks)
    
    def test_filter_by_due_date(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test filtering tasks by due date"""
        today = datetime.now(timezone.utc)
        
        # Create tasks with different due dates
        tasks_data = [
            (today - timedelta(days=1), "Overdue task"),
            (today + timedelta(days=1), "Due tomorrow"),
            (today + timedelta(days=7), "Due next week"),
            (None, "No due date")
        ]
        
        for due_date, title in tasks_data:
            task = Task(
                id=str(uuid.uuid4()),
                title=title,
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                due_date=due_date,
                user_id=test_user.id,
                actual_hours=0.0,
                position=0
            )
            test_db.add(task)
        test_db.commit()
        
        # Filter tasks due before next week
        next_week = today + timedelta(days=7)
        # Use strftime to format the date properly for URL parameters
        due_before_str = next_week.strftime("%Y-%m-%dT%H:%M:%S")
        response = test_client.get(
            f"/tasks/?due_before={due_before_str}",
            headers=auth_headers
        )
        
        if response.status_code != 200:
            print(f"Response error: {response.json()}")
        assert response.status_code == 200
        tasks = response.json()
        # Should include overdue, due tomorrow, but not due next week or no due date
        assert len(tasks) >= 2


@pytest.mark.integration
class TestTaskStatistics:
    """Test task statistics endpoint"""
    
    def test_get_task_statistics(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test getting task statistics"""
        # Create various tasks
        tasks = [
            Task(
                id=str(uuid.uuid4()),
                title="Overdue task",
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                due_date=datetime.now(timezone.utc) - timedelta(days=1),
                user_id=test_user.id,
                estimated_hours=4.0,
                actual_hours=0.0,
                position=0
            ),
            Task(
                id=str(uuid.uuid4()),
                title="Completed task",
                status=TaskStatus.DONE,
                priority=TaskPriority.MEDIUM,
                completed_at=datetime.now(timezone.utc),
                user_id=test_user.id,
                estimated_hours=2.0,
                actual_hours=2.5,
                position=1
            )
        ]
        
        for task in tasks:
            test_db.add(task)
        test_db.commit()
        
        response = test_client.get("/tasks/statistics/overview", headers=auth_headers)
        
        assert response.status_code == 200
        stats = response.json()
        assert stats["total"] >= 2
        assert stats["overdue"] >= 1
        assert stats["by_priority"]["high"] >= 1
        assert stats["total_estimated_hours"] >= 6.0
        assert stats["total_actual_hours"] >= 2.5


@pytest.mark.integration 
class TestTaskPositioning:
    """Test task positioning functionality"""
    
    def test_update_task_position(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test updating task position"""
        # Create multiple tasks
        tasks = []
        for i in range(4):
            task = Task(
                id=str(uuid.uuid4()),
                title=f"Task {i}",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                user_id=test_user.id,
                position=i,
                actual_hours=0.0
            )
            tasks.append(task)
            test_db.add(task)
        test_db.commit()
        
        # Move task from position 3 to position 1
        response = test_client.put(
            f"/tasks/{tasks[3].id}/position?new_position=1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Task position updated successfully"