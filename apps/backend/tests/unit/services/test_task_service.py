"""
Unit tests for TaskService.
"""

import uuid
from unittest.mock import MagicMock, Mock

import pytest
from sqlalchemy.orm import Session

from app.db.models import Task, TaskStatus
from app.services.task_service import TaskService
from tests.factories import TaskFactory


@pytest.mark.unit
class TestTaskService:
    """Test cases for TaskService methods."""

    def test_get_user_task_count(self):
        """Test counting tasks for a user."""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()

        # Set up the chain of mocks
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 5

        # Test
        user_id = str(uuid.uuid4())
        count = TaskService.get_user_task_count(mock_db, user_id)

        # Assertions
        assert count == 5
        mock_db.query.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_filter.count.assert_called_once()

    def test_get_tasks_by_status(self):
        """Test getting tasks filtered by status."""
        # Create test tasks
        user_id = str(uuid.uuid4())
        tasks = [
            TaskFactory.create(user_id=user_id, status=TaskStatus.TODO),
            TaskFactory.create(user_id=user_id, status=TaskStatus.TODO),
        ]

        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = tasks

        # Test
        result = TaskService.get_tasks_by_status(mock_db, user_id, TaskStatus.TODO)

        # Assertions
        assert len(result) == 2
        assert all(task.status == TaskStatus.TODO for task in result)
        mock_filter.all.assert_called_once()

    def test_validate_task_limit_under_limit(self):
        """Test task limit validation when under limit."""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 50  # Under limit of 100

        # Test
        user_id = str(uuid.uuid4())
        result = TaskService.validate_task_limit(mock_db, user_id)

        # Assertions
        assert result is True

    def test_validate_task_limit_at_limit(self):
        """Test task limit validation when at limit."""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 100  # At limit

        # Test
        user_id = str(uuid.uuid4())
        result = TaskService.validate_task_limit(mock_db, user_id)

        # Assertions
        assert result is False

    def test_validate_task_limit_custom_limit(self):
        """Test task limit validation with custom limit."""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 10

        # Test with custom limit
        user_id = str(uuid.uuid4())
        result = TaskService.validate_task_limit(mock_db, user_id, limit=10)

        # Assertions
        assert result is False  # 10 >= 10

    def test_get_task_statistics_empty(self):
        """Test getting statistics for user with no tasks."""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = []

        # Test
        user_id = str(uuid.uuid4())
        stats = TaskService.get_task_statistics(mock_db, user_id)

        # Assertions
        assert stats["total"] == 0
        assert stats["by_status"][TaskStatus.TODO] == 0
        assert stats["by_status"][TaskStatus.IN_PROGRESS] == 0
        assert stats["by_status"][TaskStatus.DONE] == 0

    def test_get_task_statistics_with_tasks(self):
        """Test getting statistics for user with tasks."""
        # Create test tasks
        user_id = str(uuid.uuid4())
        tasks = [
            TaskFactory.create(user_id=user_id, status=TaskStatus.TODO),
            TaskFactory.create(user_id=user_id, status=TaskStatus.TODO),
            TaskFactory.create(user_id=user_id, status=TaskStatus.IN_PROGRESS),
            TaskFactory.create(user_id=user_id, status=TaskStatus.DONE),
            TaskFactory.create(user_id=user_id, status=TaskStatus.DONE),
            TaskFactory.create(user_id=user_id, status=TaskStatus.DONE),
        ]

        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = tasks

        # Test
        stats = TaskService.get_task_statistics(mock_db, user_id)

        # Assertions
        assert stats["total"] == 6
        assert stats["by_status"][TaskStatus.TODO] == 2
        assert stats["by_status"][TaskStatus.IN_PROGRESS] == 1
        assert stats["by_status"][TaskStatus.DONE] == 3
