"""
Unit tests for TaskDependencyService
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid

from app.services.task_dependency_service import TaskDependencyService
from app.db.models import Task, TaskDependency, TaskStatus, TaskPriority
from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    ConflictException
)


class TestTaskDependencyService:
    """Test cases for TaskDependencyService"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for tests"""
        return str(uuid.uuid4())
    
    @pytest.fixture
    def sample_tasks(self, sample_user_id):
        """Create sample tasks for testing"""
        task1 = Task(
            id=str(uuid.uuid4()),
            title="Task 1",
            user_id=sample_user_id,
            status=TaskStatus.TODO
        )
        task2 = Task(
            id=str(uuid.uuid4()),
            title="Task 2",
            user_id=sample_user_id,
            status=TaskStatus.TODO
        )
        task3 = Task(
            id=str(uuid.uuid4()),
            title="Task 3",
            user_id=sample_user_id,
            status=TaskStatus.DONE
        )
        return task1, task2, task3
    
    def test_create_dependency_success(self, mock_db, sample_tasks, sample_user_id):
        """Test successful dependency creation"""
        task1, task2, _ = sample_tasks
        
        # Mock the query results
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            task1,  # First call returns task1
            task2,  # Second call returns task2
            None    # Third call (checking existing dependency) returns None
        ]
        
        # Mock for cycle detection
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Call the service
        result = TaskDependencyService.create_dependency(
            mock_db, task1.id, task2.id, sample_user_id
        )
        
        # Verify the dependency was created
        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called
        
        # Verify the dependency object
        created_dependency = mock_db.add.call_args[0][0]
        assert isinstance(created_dependency, TaskDependency)
        assert created_dependency.task_id == task1.id
        assert created_dependency.depends_on_id == task2.id
    
    def test_create_dependency_task_not_found(self, mock_db, sample_tasks, sample_user_id):
        """Test dependency creation when task is not found"""
        task1, _, _ = sample_tasks
        
        # Mock task not found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Should raise NotFoundException
        with pytest.raises(NotFoundException) as exc_info:
            TaskDependencyService.create_dependency(
                mock_db, task1.id, "non-existent-id", sample_user_id
            )
        
        assert "not found" in str(exc_info.value)
    
    def test_create_dependency_already_exists(self, mock_db, sample_tasks, sample_user_id):
        """Test dependency creation when it already exists"""
        task1, task2, _ = sample_tasks
        existing_dependency = TaskDependency(
            id=str(uuid.uuid4()),
            task_id=task1.id,
            depends_on_id=task2.id
        )
        
        # Mock the query results
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            task1,  # First call returns task1
            task2,  # Second call returns task2
            existing_dependency  # Third call returns existing dependency
        ]
        
        # Should raise ConflictException
        with pytest.raises(ConflictException) as exc_info:
            TaskDependencyService.create_dependency(
                mock_db, task1.id, task2.id, sample_user_id
            )
        
        assert "already exists" in str(exc_info.value)
    
    def test_create_dependency_self_reference(self, mock_db, sample_tasks, sample_user_id):
        """Test that a task cannot depend on itself"""
        task1, _, _ = sample_tasks
        
        # Mock the query results
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            task1,  # First call returns task1 (validate task exists)
            task1,  # Second call returns task1 (validate depends_on exists)
            None    # Third call returns None (no existing dependency)
        ]
        
        # Should raise BadRequestException
        with pytest.raises(BadRequestException) as exc_info:
            TaskDependencyService.create_dependency(
                mock_db, task1.id, task1.id, sample_user_id
            )
        
        assert "cannot depend on itself" in str(exc_info.value)
    
    @patch.object(TaskDependencyService, '_would_create_cycle')
    def test_create_dependency_circular_reference(self, mock_cycle_check, mock_db, sample_tasks, sample_user_id):
        """Test that circular dependencies are prevented"""
        task1, task2, _ = sample_tasks
        
        # Mock the query results
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            task1,  # First call returns task1
            task2,  # Second call returns task2
            None    # Third call (checking existing dependency) returns None
        ]
        
        # Mock cycle detection
        mock_cycle_check.return_value = True
        
        # Should raise BadRequestException
        with pytest.raises(BadRequestException) as exc_info:
            TaskDependencyService.create_dependency(
                mock_db, task1.id, task2.id, sample_user_id
            )
        
        assert "circular reference" in str(exc_info.value)
    
    def test_would_create_cycle_simple(self, mock_db):
        """Test cycle detection with simple cycle"""
        # Create a dependency chain: A -> B -> C
        dep1 = TaskDependency(task_id="A", depends_on_id="B")
        dep2 = TaskDependency(task_id="B", depends_on_id="C")
        
        # Mock the query results
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [dep2],  # B depends on C
            [],      # C has no dependencies
            [dep1]   # Check if C -> A would create cycle
        ]
        
        # Adding C -> A would create a cycle
        result = TaskDependencyService._would_create_cycle(mock_db, "C", "A")
        assert result is True
    
    def test_would_create_cycle_no_cycle(self, mock_db):
        """Test cycle detection when no cycle exists"""
        # Create a dependency chain: A -> B
        dep1 = TaskDependency(task_id="A", depends_on_id="B")
        
        # Mock the query results
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [],      # C has no dependencies
            []       # No path from C to A
        ]
        
        # Adding C -> A would not create a cycle
        result = TaskDependencyService._would_create_cycle(mock_db, "C", "A")
        assert result is False
    
    def test_delete_dependency_success(self, mock_db, sample_user_id):
        """Test successful dependency deletion"""
        dependency = TaskDependency(
            id=str(uuid.uuid4()),
            task_id="task1",
            depends_on_id="task2"
        )
        task = Task(id="task1", user_id=sample_user_id)
        
        # Mock the query
        mock_db.query.return_value.join.return_value.filter.return_value.first.return_value = dependency
        dependency.task = task
        
        # Call the service
        result = TaskDependencyService.delete_dependency(
            mock_db, dependency.id, sample_user_id
        )
        
        # Verify deletion
        assert result is True
        mock_db.delete.assert_called_with(dependency)
        assert mock_db.commit.called
    
    def test_delete_dependency_not_found(self, mock_db, sample_user_id):
        """Test dependency deletion when not found"""
        # Mock dependency not found
        mock_db.query.return_value.join.return_value.filter.return_value.first.return_value = None
        
        # Should raise NotFoundException
        with pytest.raises(NotFoundException):
            TaskDependencyService.delete_dependency(
                mock_db, "non-existent-id", sample_user_id
            )
    
    def test_get_task_dependencies(self, mock_db, sample_tasks, sample_user_id):
        """Test getting all dependencies for a task"""
        task1, task2, task3 = sample_tasks
        
        # Create mock dependencies
        dep1 = TaskDependency(
            id=str(uuid.uuid4()),
            task_id=task1.id,
            depends_on_id=task2.id
        )
        dep2 = TaskDependency(
            id=str(uuid.uuid4()),
            task_id=task1.id,
            depends_on_id=task3.id
        )
        
        # Mock the queries
        mock_db.query.return_value.filter.return_value.first.return_value = task1
        mock_db.query.return_value.filter.return_value.all.return_value = [dep1, dep2]
        
        # Call the service
        result = TaskDependencyService.get_task_dependencies(
            mock_db, task1.id, sample_user_id
        )
        
        # Verify results
        assert len(result) == 2
        assert dep1 in result
        assert dep2 in result
    
    def test_can_complete_task_with_incomplete_dependencies(self, mock_db, sample_tasks, sample_user_id):
        """Test checking if task can be completed when dependencies are incomplete"""
        task1, task2, _ = sample_tasks
        
        # Create dependency where task1 depends on incomplete task2
        dep = TaskDependency(
            id=str(uuid.uuid4()),
            task_id=task1.id,
            depends_on_id=task2.id
        )
        dep.depends_on = task2  # task2 is TODO
        
        # Mock the query
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [dep]
        
        # Call the service
        can_complete, incomplete_deps = TaskDependencyService.can_complete_task(
            mock_db, task1.id, sample_user_id
        )
        
        # Verify results
        assert can_complete is False
        assert task2.id in incomplete_deps
    
    def test_can_complete_task_with_completed_dependencies(self, mock_db, sample_tasks, sample_user_id):
        """Test checking if task can be completed when all dependencies are done"""
        task1, _, task3 = sample_tasks
        
        # Create dependency where task1 depends on completed task3
        dep = TaskDependency(
            id=str(uuid.uuid4()),
            task_id=task1.id,
            depends_on_id=task3.id
        )
        dep.depends_on = task3  # task3 is DONE
        
        # Mock the query
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [dep]
        
        # Call the service
        can_complete, incomplete_deps = TaskDependencyService.can_complete_task(
            mock_db, task1.id, sample_user_id
        )
        
        # Verify results
        assert can_complete is True
        assert len(incomplete_deps) == 0
    
    def test_update_task_parent_success(self, mock_db, sample_tasks, sample_user_id):
        """Test successful parent task update"""
        task1, task2, _ = sample_tasks
        
        # Mock the queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            task1,  # First call returns task to update
            task2,  # Second call returns parent task
            None,   # Third call for circular hierarchy check (task2 has no parent)
        ]
        
        # Call the service
        result = TaskDependencyService.update_task_parent(
            mock_db, task1.id, task2.id, sample_user_id
        )
        
        # Verify parent was set
        assert task1.parent_task_id == task2.id
        assert mock_db.commit.called
        assert result == task1
    
    def test_update_task_parent_remove_parent(self, mock_db, sample_tasks, sample_user_id):
        """Test removing parent from a task"""
        task1, _, _ = sample_tasks
        task1.parent_task_id = "some-parent-id"
        
        # Mock the query
        mock_db.query.return_value.filter.return_value.first.return_value = task1
        
        # Call the service with None
        result = TaskDependencyService.update_task_parent(
            mock_db, task1.id, None, sample_user_id
        )
        
        # Verify parent was removed
        assert task1.parent_task_id is None
        assert mock_db.commit.called
        assert result == task1
    
    def test_update_task_parent_self_parent(self, mock_db, sample_tasks, sample_user_id):
        """Test that a task cannot be its own parent"""
        task1, _, _ = sample_tasks
        
        # Mock the query
        mock_db.query.return_value.filter.return_value.first.return_value = task1
        
        # Should raise BadRequestException
        with pytest.raises(BadRequestException) as exc_info:
            TaskDependencyService.update_task_parent(
                mock_db, task1.id, task1.id, sample_user_id
            )
        
        assert "cannot be its own parent" in str(exc_info.value)
    
    @patch.object(TaskDependencyService, '_would_create_circular_hierarchy')
    def test_update_task_parent_circular_hierarchy(self, mock_circular_check, mock_db, sample_tasks, sample_user_id):
        """Test that circular hierarchies are prevented"""
        task1, task2, _ = sample_tasks
        
        # Mock the queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            task1,  # First call returns task to update
            task2   # Second call returns parent task
        ]
        
        # Mock circular hierarchy detection
        mock_circular_check.return_value = True
        
        # Should raise BadRequestException
        with pytest.raises(BadRequestException) as exc_info:
            TaskDependencyService.update_task_parent(
                mock_db, task1.id, task2.id, sample_user_id
            )
        
        assert "circular task hierarchy" in str(exc_info.value)
    
    def test_would_create_circular_hierarchy(self, mock_db):
        """Test circular hierarchy detection"""
        # Create tasks with hierarchy: A -> B -> C
        taskA = Task(id="A", parent_task_id=None)
        taskB = Task(id="B", parent_task_id="A")
        taskC = Task(id="C", parent_task_id="B")
        
        # Mock the queries to trace up from A
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            taskB,  # First call: C's parent is B
            taskA,  # Second call: B's parent is A
            None    # Third call: A has no parent
        ]
        
        # Setting A's parent to C would create a cycle (C -> B -> A -> C)
        result = TaskDependencyService._would_create_circular_hierarchy(
            mock_db, "A", "C"
        )
        assert result is True
    
    def test_get_subtasks(self, mock_db, sample_tasks, sample_user_id):
        """Test getting subtasks of a task"""
        parent_task, task1, task2 = sample_tasks
        task1.parent_task_id = parent_task.id
        task2.parent_task_id = parent_task.id
        
        # Mock the queries
        mock_db.query.return_value.filter.return_value.first.return_value = parent_task
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [task1, task2]
        
        # Call the service
        result = TaskDependencyService.get_subtasks(
            mock_db, parent_task.id, sample_user_id
        )
        
        # Verify results
        assert len(result) == 2
        assert task1 in result
        assert task2 in result
    
    def test_update_parent_task_status_all_done(self, mock_db):
        """Test parent task status update when all subtasks are done"""
        parent_task = Task(
            id="parent",
            status=TaskStatus.IN_PROGRESS
        )
        subtask1 = Task(id="sub1", parent_task_id="parent", status=TaskStatus.DONE)
        subtask2 = Task(id="sub2", parent_task_id="parent", status=TaskStatus.DONE)
        
        # Mock the query
        mock_db.query.return_value.filter.return_value.all.return_value = [subtask1, subtask2]
        
        # Call the service
        TaskDependencyService.update_parent_task_status(mock_db, parent_task)
        
        # Verify parent status was updated to DONE
        assert parent_task.status == TaskStatus.DONE
        assert parent_task.completed_at is not None
        assert mock_db.commit.called
    
    def test_update_parent_task_status_any_in_progress(self, mock_db):
        """Test parent task status update when any subtask is in progress"""
        parent_task = Task(
            id="parent",
            status=TaskStatus.TODO
        )
        subtask1 = Task(id="sub1", parent_task_id="parent", status=TaskStatus.DONE)
        subtask2 = Task(id="sub2", parent_task_id="parent", status=TaskStatus.IN_PROGRESS)
        
        # Mock the query
        mock_db.query.return_value.filter.return_value.all.return_value = [subtask1, subtask2]
        
        # Call the service
        TaskDependencyService.update_parent_task_status(mock_db, parent_task)
        
        # Verify parent status was updated to IN_PROGRESS
        assert parent_task.status == TaskStatus.IN_PROGRESS
        assert mock_db.commit.called
    
    def test_update_parent_task_status_all_todo(self, mock_db):
        """Test parent task status update when all subtasks are todo"""
        parent_task = Task(
            id="parent",
            status=TaskStatus.DONE,
            completed_at="2023-01-01"
        )
        subtask1 = Task(id="sub1", parent_task_id="parent", status=TaskStatus.TODO)
        subtask2 = Task(id="sub2", parent_task_id="parent", status=TaskStatus.TODO)
        
        # Mock the query
        mock_db.query.return_value.filter.return_value.all.return_value = [subtask1, subtask2]
        
        # Call the service
        TaskDependencyService.update_parent_task_status(mock_db, parent_task)
        
        # Verify parent status was updated to TODO
        assert parent_task.status == TaskStatus.TODO
        assert parent_task.completed_at is None
        assert mock_db.commit.called