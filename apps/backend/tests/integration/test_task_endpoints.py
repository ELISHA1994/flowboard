"""
Integration tests for task endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models import Task, User, TaskStatus
from tests.factories import TaskCreateFactory, TaskUpdateFactory, TaskFactory
import uuid


@pytest.mark.integration
class TestTaskCreate:
    """Test cases for task creation endpoint."""
    
    def test_create_task_success(self, authenticated_client: TestClient, test_user: User, test_db: Session):
        """Test successful task creation."""
        task_data = TaskCreateFactory.create()
        
        response = authenticated_client.post("/tasks/", json=task_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["status"] == task_data["status"]
        assert data["user_id"] == test_user.id
        assert "id" in data
        assert "created_at" in data
        
        # Verify in database
        db_task = test_db.query(Task).filter(Task.id == data["id"]).first()
        assert db_task is not None
        assert db_task.user_id == test_user.id
    
    def test_create_task_minimal(self, authenticated_client: TestClient, test_user: User):
        """Test creating task with minimal data."""
        task_data = {"title": "Minimal Task"}
        
        response = authenticated_client.post("/tasks/", json=task_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Task"
        assert data["description"] is None
        assert data["status"] == "todo"  # Default
    
    def test_create_task_unauthenticated(self, test_client: TestClient):
        """Test creating task without authentication."""
        task_data = TaskCreateFactory.create()
        
        response = test_client.post("/tasks/", json=task_data)
        
        assert response.status_code == 401
    
    def test_create_task_invalid_title(self, authenticated_client: TestClient):
        """Test creating task with invalid title."""
        task_data = {"title": "", "description": "Test"}
        
        response = authenticated_client.post("/tasks/", json=task_data)
        
        assert response.status_code == 422
    
    def test_create_task_invalid_status(self, authenticated_client: TestClient):
        """Test creating task with invalid status."""
        task_data = {
            "title": "Test Task",
            "status": "invalid_status"
        }
        
        response = authenticated_client.post("/tasks/", json=task_data)
        
        assert response.status_code == 422


@pytest.mark.integration
class TestTaskList:
    """Test cases for task listing endpoint."""
    
    def test_list_tasks_empty(self, authenticated_client: TestClient):
        """Test listing tasks when user has none."""
        response = authenticated_client.get("/tasks/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_list_tasks_with_data(self, authenticated_client: TestClient, test_user: User, test_db: Session):
        """Test listing user's tasks."""
        # Create some tasks for the user
        tasks = []
        for i in range(3):
            task = TaskFactory.create(user_id=test_user.id)
            test_db.add(task)
            tasks.append(task)
        test_db.commit()
        
        response = authenticated_client.get("/tasks/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Verify all tasks belong to the user
        for task in data:
            assert task["user_id"] == test_user.id
    
    def test_list_tasks_user_isolation(self, authenticated_client: TestClient, test_user: User, test_db: Session):
        """Test that users only see their own tasks."""
        # Create tasks for test user
        user_task = TaskFactory.create(user_id=test_user.id)
        test_db.add(user_task)
        
        # Create tasks for another user
        other_user_id = str(uuid.uuid4())
        other_task = TaskFactory.create(user_id=other_user_id)
        test_db.add(other_task)
        test_db.commit()
        
        response = authenticated_client.get("/tasks/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == user_task.id
        assert data[0]["user_id"] == test_user.id
    
    def test_list_tasks_filter_by_status(self, authenticated_client: TestClient, test_user: User, test_db: Session):
        """Test filtering tasks by status."""
        # Create tasks with different statuses
        todo_task = TaskFactory.create(user_id=test_user.id, status=TaskStatus.TODO)
        in_progress_task = TaskFactory.create(user_id=test_user.id, status=TaskStatus.IN_PROGRESS)
        done_task = TaskFactory.create(user_id=test_user.id, status=TaskStatus.DONE)
        
        test_db.add_all([todo_task, in_progress_task, done_task])
        test_db.commit()
        
        # Filter by TODO status
        response = authenticated_client.get("/tasks/?task_status=todo")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "todo"
        
        # Filter by DONE status
        response = authenticated_client.get("/tasks/?task_status=done")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "done"
    
    def test_list_tasks_pagination(self, authenticated_client: TestClient, test_user: User, test_db: Session):
        """Test task list pagination."""
        # Create multiple tasks
        for i in range(15):
            task = TaskFactory.create(user_id=test_user.id)
            test_db.add(task)
        test_db.commit()
        
        # Test default limit (10)
        response = authenticated_client.get("/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        
        # Test custom limit
        response = authenticated_client.get("/tasks/?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        
        # Test skip
        response = authenticated_client.get("/tasks/?skip=10&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # Only 5 remaining
    
    def test_list_tasks_unauthenticated(self, test_client: TestClient):
        """Test listing tasks without authentication."""
        response = test_client.get("/tasks/")
        assert response.status_code == 401


@pytest.mark.integration
class TestTaskGet:
    """Test cases for getting a specific task."""
    
    def test_get_task_success(self, authenticated_client: TestClient, test_task: Task):
        """Test getting a specific task."""
        response = authenticated_client.get(f"/tasks/{test_task.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_task.id
        assert data["title"] == test_task.title
        assert data["description"] == test_task.description
        assert data["status"] == test_task.status
    
    def test_get_task_not_found(self, authenticated_client: TestClient):
        """Test getting non-existent task."""
        fake_id = str(uuid.uuid4())
        response = authenticated_client.get(f"/tasks/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()
    
    def test_get_task_other_user(self, authenticated_client: TestClient, test_db: Session):
        """Test that users can't access other users' tasks."""
        # Create task for another user
        other_user_id = str(uuid.uuid4())
        other_task = TaskFactory.create(user_id=other_user_id)
        test_db.add(other_task)
        test_db.commit()
        
        response = authenticated_client.get(f"/tasks/{other_task.id}")
        
        assert response.status_code == 403


@pytest.mark.integration
class TestTaskUpdate:
    """Test cases for task update endpoint."""
    
    def test_update_task_all_fields(self, authenticated_client: TestClient, test_task: Task, test_db: Session):
        """Test updating all task fields."""
        update_data = TaskUpdateFactory.create()
        
        response = authenticated_client.put(f"/tasks/{test_task.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
        assert data["status"] == update_data["status"]
        assert data["updated_at"] is not None
        
        # Verify in database
        db_task = test_db.query(Task).filter(Task.id == test_task.id).first()
        assert db_task is not None
        assert db_task.title == update_data["title"]
    
    def test_update_task_partial(self, authenticated_client: TestClient, test_task: Task):
        """Test partial task update."""
        update_data = {"status": "done"}
        
        response = authenticated_client.put(f"/tasks/{test_task.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        # Other fields unchanged
        assert data["title"] == test_task.title
        assert data["description"] == test_task.description
    
    def test_update_task_not_found(self, authenticated_client: TestClient):
        """Test updating non-existent task."""
        fake_id = str(uuid.uuid4())
        update_data = {"title": "Updated"}
        
        response = authenticated_client.put(f"/tasks/{fake_id}", json=update_data)
        
        assert response.status_code == 404
    
    def test_update_task_other_user(self, authenticated_client: TestClient, test_db: Session):
        """Test that users can't update other users' tasks."""
        # Create task for another user
        other_user_id = str(uuid.uuid4())
        other_task = TaskFactory.create(user_id=other_user_id)
        test_db.add(other_task)
        test_db.commit()
        
        update_data = {"title": "Hacked!"}
        response = authenticated_client.put(f"/tasks/{other_task.id}", json=update_data)
        
        assert response.status_code == 403


@pytest.mark.integration
class TestTaskDelete:
    """Test cases for task deletion endpoint."""
    
    def test_delete_task_success(self, authenticated_client: TestClient, test_task: Task, test_db: Session):
        """Test successful task deletion."""
        task_id = test_task.id
        
        response = authenticated_client.delete(f"/tasks/{task_id}")
        
        assert response.status_code == 204
        
        # Verify task is deleted from database
        deleted_task = test_db.query(Task).filter(Task.id == task_id).first()
        assert deleted_task is None
    
    def test_delete_task_not_found(self, authenticated_client: TestClient):
        """Test deleting non-existent task."""
        fake_id = str(uuid.uuid4())
        
        response = authenticated_client.delete(f"/tasks/{fake_id}")
        
        assert response.status_code == 404
    
    def test_delete_task_other_user(self, authenticated_client: TestClient, test_db: Session):
        """Test that users can't delete other users' tasks."""
        # Create task for another user
        other_user_id = str(uuid.uuid4())
        other_task = TaskFactory.create(user_id=other_user_id)
        test_db.add(other_task)
        test_db.commit()
        
        response = authenticated_client.delete(f"/tasks/{other_task.id}")
        
        assert response.status_code == 403
        
        # Verify task still exists
        task_exists = test_db.query(Task).filter(Task.id == other_task.id).first()
        assert task_exists is not None