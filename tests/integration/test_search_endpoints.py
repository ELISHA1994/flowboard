"""
Integration tests for search and filtering endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json

from app.db.models import Task, TaskStatus, TaskPriority, Category, Tag, SavedSearch, User


class TestSearchEndpoints:
    """Test search and filtering endpoints."""
    
    def test_search_tasks_basic(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User
    ):
        """Test basic task search functionality."""
        # Create test tasks
        task1 = Task(
            id="task1",
            title="Fix login bug",
            description="Users can't login with email",
            user_id=test_user.id,
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH
        )
        task2 = Task(
            id="task2", 
            title="Add search feature",
            description="Implement full-text search",
            user_id=test_user.id,
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM
        )
        task3 = Task(
            id="task3",
            title="Update documentation",
            description="Update API docs",
            user_id=test_user.id,
            status=TaskStatus.DONE,
            priority=TaskPriority.LOW
        )
        test_db.add_all([task1, task2, task3])
        test_db.commit()
        
        # Test text search
        response = test_client.post(
            "/search/tasks",
            headers=auth_headers,
            json={"text": "search"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["title"] == "Add search feature"
        
        # Test with filters
        response = test_client.post(
            "/search/tasks",
            headers=auth_headers,
            json={
                "filters": [
                    {"field": "status", "operator": "eq", "value": "todo"}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["status"] == "todo"
    
    def test_search_with_multiple_filters(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User
    ):
        """Test search with multiple filters."""
        # Create test tasks
        task1 = Task(
            id="task1",
            title="High priority task",
            user_id=test_user.id,
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH
        )
        task2 = Task(
            id="task2",
            title="Another high priority",
            user_id=test_user.id,
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH
        )
        test_db.add_all([task1, task2])
        test_db.commit()
        
        # Search for high priority TODO tasks
        response = test_client.post(
            "/search/tasks",
            headers=auth_headers,
            json={
                "filters": [
                    {"field": "status", "operator": "eq", "value": "todo"},
                    {"field": "priority", "operator": "eq", "value": "high"}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["id"] == "task1"
    
    def test_search_suggestions(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User
    ):
        """Test search suggestions endpoint."""
        # Create test data
        category = Category(
            id="cat1",
            name="Work",
            color="#0000FF",
            user_id=test_user.id
        )
        tag = Tag(
            id="tag1",
            name="urgent",
            color="#FF0000",
            user_id=test_user.id
        )
        test_db.add_all([category, tag])
        test_db.commit()
        
        response = test_client.get(
            "/search/suggestions",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "statuses" in data
        assert "priorities" in data
        assert "categories" in data
        assert "tags" in data
        assert "assigned_users" in data
        assert "projects" in data
        
        # Check values
        assert len(data["statuses"]) == 3  # TODO, IN_PROGRESS, DONE
        assert len(data["priorities"]) == 4  # LOW, MEDIUM, HIGH, URGENT
        assert len(data["categories"]) == 1
        assert data["categories"][0]["name"] == "Work"
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == "urgent"
    
    def test_saved_search_crud(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User
    ):
        """Test saved search CRUD operations."""
        # Create saved search
        search_data = {
            "name": "My High Priority Tasks",
            "description": "All my high priority tasks",
            "search_query": {
                "filters": [
                    {"field": "priority", "operator": "eq", "value": "high"}
                ],
                "sort_by": "created_at",
                "sort_order": "desc"
            },
            "is_default": True
        }
        
        response = test_client.post(
            "/search/saved",
            headers=auth_headers,
            json=search_data
        )
        assert response.status_code == 200
        saved_search = response.json()
        assert saved_search["name"] == search_data["name"]
        assert saved_search["is_default"] is True
        search_id = saved_search["id"]
        
        # Get saved searches
        response = test_client.get(
            "/search/saved",
            headers=auth_headers
        )
        assert response.status_code == 200
        searches = response.json()
        assert len(searches) == 1
        assert searches[0]["id"] == search_id
        
        # Get specific saved search
        response = test_client.get(
            f"/search/saved/{search_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == search_id
        
        # Update saved search
        update_data = {
            "name": "Updated Search Name",
            "is_default": False
        }
        response = test_client.put(
            f"/search/saved/{search_id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["name"] == "Updated Search Name"
        assert updated["is_default"] is False
        
        # Delete saved search
        response = test_client.delete(
            f"/search/saved/{search_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify deletion
        response = test_client.get(
            f"/search/saved/{search_id}",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_bulk_operations(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User
    ):
        """Test bulk operations on tasks."""
        # Create test tasks
        task_ids = []
        for i in range(3):
            task = Task(
                id=f"task{i}",
                title=f"Task {i}",
                user_id=test_user.id,
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM
            )
            test_db.add(task)
            task_ids.append(task.id)
        test_db.commit()
        
        # Bulk update status
        response = test_client.post(
            "/search/bulk",
            headers=auth_headers,
            json={
                "task_ids": task_ids,
                "operation": "update_status",
                "value": "in_progress"
            }
        )
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["updated_count"] == 3
        
        # Verify update
        tasks = test_db.query(Task).filter(Task.id.in_(task_ids)).all()
        for task in tasks:
            assert task.status == TaskStatus.IN_PROGRESS
        
        # Bulk update priority
        response = test_client.post(
            "/search/bulk",
            headers=auth_headers,
            json={
                "task_ids": task_ids[:2],  # Update only first 2
                "operation": "update_priority",
                "value": "high"
            }
        )
        assert response.status_code == 200
        result = response.json()
        assert result["updated_count"] == 2
        
        # Test bulk delete
        response = test_client.post(
            "/search/bulk",
            headers=auth_headers,
            json={
                "task_ids": [task_ids[0]],
                "operation": "delete"
            }
        )
        assert response.status_code == 200
        result = response.json()
        assert result["deleted_count"] == 1
        
        # Verify deletion
        remaining_tasks = test_db.query(Task).filter(Task.id.in_(task_ids)).all()
        assert len(remaining_tasks) == 2
    
    def test_bulk_operations_with_tags(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User
    ):
        """Test bulk operations with tags."""
        # Create tasks
        task1 = Task(id="t1", title="Task 1", user_id=test_user.id)
        task2 = Task(id="t2", title="Task 2", user_id=test_user.id)
        test_db.add_all([task1, task2])
        test_db.commit()
        
        # Add tags
        response = test_client.post(
            "/search/bulk",
            headers=auth_headers,
            json={
                "task_ids": ["t1", "t2"],
                "operation": "add_tags",
                "value": ["important", "review"]
            }
        )
        assert response.status_code == 200
        
        # Verify tags added
        task1 = test_db.query(Task).filter_by(id="t1").first()
        tag_names = [tag.name for tag in task1.tags]
        assert "important" in tag_names
        assert "review" in tag_names
        
        # Remove tags
        response = test_client.post(
            "/search/bulk",
            headers=auth_headers,
            json={
                "task_ids": ["t1"],
                "operation": "remove_tags",
                "value": ["review"]
            }
        )
        assert response.status_code == 200
        
        # Verify tag removed
        task1 = test_db.query(Task).filter_by(id="t1").first()
        tag_names = [tag.name for tag in task1.tags]
        assert "important" in tag_names
        assert "review" not in tag_names
    
    def test_search_pagination(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_user: User
    ):
        """Test search result pagination."""
        # Create 25 tasks
        for i in range(25):
            task = Task(
                id=f"task{i}",
                title=f"Task {i}",
                user_id=test_user.id,
                priority=TaskPriority.MEDIUM
            )
            test_db.add(task)
        test_db.commit()
        
        # Test first page
        response = test_client.post(
            "/search/tasks",
            headers=auth_headers,
            json={
                "skip": 0,
                "limit": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["tasks"]) == 10
        assert data["skip"] == 0
        assert data["limit"] == 10
        
        # Test second page
        response = test_client.post(
            "/search/tasks",
            headers=auth_headers,
            json={
                "skip": 10,
                "limit": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["tasks"]) == 10
        assert data["skip"] == 10
        
        # Test last page
        response = test_client.post(
            "/search/tasks",
            headers=auth_headers,
            json={
                "skip": 20,
                "limit": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["tasks"]) == 5
        assert data["skip"] == 20
    
    def test_invalid_search_operations(
        self,
        test_client: TestClient,
        auth_headers: dict
    ):
        """Test error handling for invalid search operations."""
        # Invalid filter field
        response = test_client.post(
            "/search/tasks",
            headers=auth_headers,
            json={
                "filters": [
                    {"field": "invalid_field", "operator": "eq", "value": "test"}
                ]
            }
        )
        assert response.status_code == 422
        
        # Invalid bulk operation
        response = test_client.post(
            "/search/bulk",
            headers=auth_headers,
            json={
                "task_ids": ["task1"],
                "operation": "invalid_operation"
            }
        )
        assert response.status_code == 422
        
        # Bulk operation with invalid value
        response = test_client.post(
            "/search/bulk",
            headers=auth_headers,
            json={
                "task_ids": ["task1"],
                "operation": "update_status",
                "value": "invalid_status"
            }
        )
        assert response.status_code == 400