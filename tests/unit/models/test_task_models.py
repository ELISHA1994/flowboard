"""
Unit tests for Task Pydantic models.
"""
import pytest
from pydantic import ValidationError
from app.models.task import TaskCreate, TaskUpdate, TaskResponse
from app.db.models import TaskStatus
from datetime import datetime, timezone
import uuid


@pytest.mark.unit
class TestTaskCreate:
    """Test cases for TaskCreate model validation."""
    
    def test_valid_task_create(self):
        """Test creating a valid task."""
        data = {
            "title": "Test Task",
            "description": "This is a test task",
            "status": "todo"
        }
        task = TaskCreate(**data)
        
        assert task.title == "Test Task"
        assert task.description == "This is a test task"
        assert task.status == TaskStatus.TODO
    
    def test_task_create_minimal(self):
        """Test creating a task with minimal data."""
        data = {"title": "Minimal Task"}
        task = TaskCreate(**data)
        
        assert task.title == "Minimal Task"
        assert task.description is None
        assert task.status == TaskStatus.TODO  # Default value
    
    def test_task_create_title_strip_whitespace(self):
        """Test that title whitespace is stripped."""
        data = {"title": "  Spaced Title  "}
        task = TaskCreate(**data)
        
        assert task.title == "Spaced Title"
    
    def test_task_create_empty_title_fails(self):
        """Test that empty title fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title="")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "at least 1 character" in str(errors[0])
    
    def test_task_create_whitespace_only_title_fails(self):
        """Test that whitespace-only title fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title="   ")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "empty or just whitespace" in str(errors[0])
    
    def test_task_create_title_too_long_fails(self):
        """Test that title exceeding max length fails."""
        long_title = "x" * 201  # Max is 200
        
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title=long_title)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "at most 200 characters" in str(errors[0])
    
    def test_task_create_description_too_long_fails(self):
        """Test that description exceeding max length fails."""
        long_description = "x" * 1001  # Max is 1000
        
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title="Valid Title", description=long_description)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "at most 1000 characters" in str(errors[0])
    
    def test_task_create_invalid_status_fails(self):
        """Test that invalid status fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title="Test", status="invalid_status")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1


@pytest.mark.unit
class TestTaskUpdate:
    """Test cases for TaskUpdate model validation."""
    
    def test_valid_task_update_all_fields(self):
        """Test updating all fields."""
        data = {
            "title": "Updated Title",
            "description": "Updated description",
            "status": "in_progress"
        }
        task_update = TaskUpdate(**data)
        
        assert task_update.title == "Updated Title"
        assert task_update.description == "Updated description"
        assert task_update.status == TaskStatus.IN_PROGRESS
    
    def test_task_update_partial(self):
        """Test partial update with only some fields."""
        data = {"title": "Only Title Updated"}
        task_update = TaskUpdate(**data)
        
        assert task_update.title == "Only Title Updated"
        assert task_update.description is None
        assert task_update.status is None
    
    def test_task_update_empty_valid(self):
        """Test that empty update is valid (no fields to update)."""
        task_update = TaskUpdate()
        
        assert task_update.title is None
        assert task_update.description is None
        assert task_update.status is None
    
    def test_task_update_title_validation(self):
        """Test that title validation works in update."""
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdate(title="")  # Empty title not allowed if provided
        
        errors = exc_info.value.errors()
        assert len(errors) == 1


@pytest.mark.unit
class TestTaskResponse:
    """Test cases for TaskResponse model."""
    
    def test_valid_task_response(self):
        """Test creating a valid task response."""
        data = {
            "id": str(uuid.uuid4()),
            "title": "Response Task",
            "description": "Task description",
            "status": "todo",
            "user_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc),
            "updated_at": None
        }
        response = TaskResponse(**data)
        
        assert response.id == data["id"]
        assert response.title == "Response Task"
        assert response.status == TaskStatus.TODO
        assert response.updated_at is None
    
    def test_task_response_with_updated_at(self):
        """Test task response with updated_at timestamp."""
        now = datetime.now(timezone.utc)
        data = {
            "id": str(uuid.uuid4()),
            "title": "Updated Task",
            "status": "done",
            "user_id": str(uuid.uuid4()),
            "created_at": now,
            "updated_at": now
        }
        response = TaskResponse(**data)
        
        assert response.updated_at == now
    
    def test_task_response_from_orm(self):
        """Test that from_attributes config works."""
        # This is tested implicitly when using the response models
        # with SQLAlchemy models in the actual application
        assert TaskResponse.model_config.get("from_attributes") is True