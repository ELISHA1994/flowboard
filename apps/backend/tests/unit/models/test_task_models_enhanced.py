"""
Unit tests for enhanced task models with priority, dates, and time tracking.
"""
import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from app.models.task import TaskCreate, TaskUpdate, TaskResponse, TaskTimeUpdate
from app.db.models import TaskStatus, TaskPriority


@pytest.mark.unit
class TestEnhancedTaskCreate:
    """Test cases for enhanced TaskCreate model"""
    
    def test_task_create_with_priority(self):
        """Test creating task with priority"""
        task_data = {
            "title": "High Priority Task",
            "description": "This is urgent",
            "priority": TaskPriority.HIGH
        }
        task = TaskCreate(**task_data)
        assert task.priority == TaskPriority.HIGH
    
    def test_task_create_default_priority(self):
        """Test task creation uses default priority"""
        task_data = {
            "title": "Normal Task"
        }
        task = TaskCreate(**task_data)
        assert task.priority == TaskPriority.MEDIUM
    
    def test_task_create_with_dates(self):
        """Test creating task with due date and start date"""
        start_date = datetime.now(timezone.utc)
        due_date = start_date + timedelta(days=7)
        
        task_data = {
            "title": "Scheduled Task",
            "start_date": start_date,
            "due_date": due_date
        }
        task = TaskCreate(**task_data)
        assert task.start_date == start_date
        assert task.due_date == due_date
    
    def test_task_create_invalid_date_order(self):
        """Test validation when due date is before start date"""
        start_date = datetime.now(timezone.utc)
        due_date = start_date - timedelta(days=1)
        
        task_data = {
            "title": "Invalid Date Task",
            "start_date": start_date,
            "due_date": due_date
        }
        
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(**task_data)
        assert "Due date must be after start date" in str(exc_info.value)
    
    def test_task_create_with_estimated_hours(self):
        """Test creating task with estimated hours"""
        task_data = {
            "title": "Time Estimated Task",
            "estimated_hours": 4.5
        }
        task = TaskCreate(**task_data)
        assert task.estimated_hours == 4.5
    
    def test_task_create_invalid_estimated_hours(self):
        """Test validation for invalid estimated hours"""
        # Negative hours
        with pytest.raises(ValidationError):
            TaskCreate(title="Task", estimated_hours=-1)
        
        # Too many hours
        with pytest.raises(ValidationError):
            TaskCreate(title="Task", estimated_hours=1001)
    
    def test_task_create_with_position(self):
        """Test creating task with specific position"""
        task_data = {
            "title": "Positioned Task",
            "position": 5
        }
        task = TaskCreate(**task_data)
        assert task.position == 5
    
    def test_task_create_default_position(self):
        """Test task creation uses default position"""
        task = TaskCreate(title="Task")
        assert task.position == 0


@pytest.mark.unit
class TestEnhancedTaskUpdate:
    """Test cases for enhanced TaskUpdate model"""
    
    def test_update_priority(self):
        """Test updating task priority"""
        update_data = {"priority": TaskPriority.URGENT}
        update = TaskUpdate(**update_data)
        assert update.priority == TaskPriority.URGENT
    
    def test_update_dates(self):
        """Test updating task dates"""
        new_due_date = datetime.now(timezone.utc) + timedelta(days=3)
        update_data = {
            "due_date": new_due_date,
            "start_date": datetime.now(timezone.utc)
        }
        update = TaskUpdate(**update_data)
        assert update.due_date == new_due_date
    
    def test_update_actual_hours(self):
        """Test updating actual hours"""
        update_data = {"actual_hours": 3.5}
        update = TaskUpdate(**update_data)
        assert update.actual_hours == 3.5
    
    def test_update_invalid_actual_hours(self):
        """Test validation for invalid actual hours"""
        with pytest.raises(ValidationError):
            TaskUpdate(actual_hours=-1)
        
        with pytest.raises(ValidationError):
            TaskUpdate(actual_hours=1001)
    
    def test_update_position(self):
        """Test updating task position"""
        update_data = {"position": 10}
        update = TaskUpdate(**update_data)
        assert update.position == 10
    
    def test_update_all_fields_optional(self):
        """Test that all fields in update are optional"""
        update = TaskUpdate()
        assert update.title is None
        assert update.priority is None
        assert update.due_date is None
        assert update.estimated_hours is None


@pytest.mark.unit
class TestTaskTimeUpdate:
    """Test cases for TaskTimeUpdate model"""
    
    def test_valid_time_update(self):
        """Test valid time update"""
        time_update = TaskTimeUpdate(hours_to_add=2.5)
        assert time_update.hours_to_add == 2.5
    
    def test_time_update_validation(self):
        """Test time update validation"""
        # Must be positive
        with pytest.raises(ValidationError):
            TaskTimeUpdate(hours_to_add=0)
        
        with pytest.raises(ValidationError):
            TaskTimeUpdate(hours_to_add=-1)
        
        # Cannot exceed 24 hours
        with pytest.raises(ValidationError):
            TaskTimeUpdate(hours_to_add=25)
    
    def test_time_update_edge_cases(self):
        """Test edge cases for time update"""
        # Minimum valid
        time_update = TaskTimeUpdate(hours_to_add=0.1)
        assert time_update.hours_to_add == 0.1
        
        # Maximum valid
        time_update = TaskTimeUpdate(hours_to_add=24)
        assert time_update.hours_to_add == 24


@pytest.mark.unit
class TestEnhancedTaskResponse:
    """Test cases for enhanced TaskResponse model"""
    
    def test_response_with_all_fields(self):
        """Test response with all enhanced fields"""
        now = datetime.now(timezone.utc)
        response_data = {
            "id": "123",
            "title": "Complete Task",
            "description": "Full details",
            "status": TaskStatus.DONE,
            "priority": TaskPriority.HIGH,
            "user_id": "user123",
            "due_date": now + timedelta(days=1),
            "start_date": now,
            "completed_at": now,
            "estimated_hours": 5.0,
            "actual_hours": 4.5,
            "position": 3,
            "created_at": now,
            "updated_at": now
        }
        
        response = TaskResponse(**response_data)
        assert response.priority == TaskPriority.HIGH
        assert response.completed_at == now
        assert response.actual_hours == 4.5
        assert response.position == 3
    
    def test_response_with_minimal_fields(self):
        """Test response with only required fields"""
        now = datetime.now(timezone.utc)
        response_data = {
            "id": "123",
            "title": "Simple Task",
            "status": TaskStatus.TODO,
            "priority": TaskPriority.MEDIUM,
            "user_id": "user123",
            "created_at": now
        }
        
        response = TaskResponse(**response_data)
        assert response.description is None
        assert response.due_date is None
        assert response.completed_at is None
        assert response.actual_hours == 0.0
        assert response.position == 0