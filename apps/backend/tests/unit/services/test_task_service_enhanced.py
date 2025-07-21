"""
Unit tests for enhanced task service functionality.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock

import pytest

from app.db.models import Task, TaskPriority, TaskStatus
from app.services.task_service import TaskService


@pytest.mark.unit
class TestEnhancedTaskStatistics:
    """Test cases for enhanced task statistics"""

    def test_get_task_statistics_with_priorities(self):
        """Test statistics include priority breakdown"""
        mock_db = Mock()
        user_id = "user123"

        # Create mock tasks with different priorities
        mock_tasks = [
            Mock(
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                due_date=None,
                completed_at=None,
                estimated_hours=2.0,
                actual_hours=0.0,
            ),
            Mock(
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.URGENT,
                due_date=None,
                completed_at=None,
                estimated_hours=4.0,
                actual_hours=1.5,
            ),
            Mock(
                status=TaskStatus.DONE,
                priority=TaskPriority.MEDIUM,
                due_date=None,
                completed_at=datetime.now(timezone.utc),
                estimated_hours=3.0,
                actual_hours=3.5,
            ),
        ]

        mock_db.query.return_value.filter.return_value.all.return_value = mock_tasks

        stats = TaskService.get_task_statistics(mock_db, user_id)

        assert stats["total"] == 3
        assert stats["by_priority"][TaskPriority.HIGH] == 1
        assert stats["by_priority"][TaskPriority.URGENT] == 1
        assert stats["by_priority"][TaskPriority.MEDIUM] == 1
        assert stats["by_priority"][TaskPriority.LOW] == 0
        assert stats["total_estimated_hours"] == 9.0
        assert stats["total_actual_hours"] == 5.0

    def test_get_task_statistics_overdue(self):
        """Test statistics correctly identify overdue tasks"""
        mock_db = Mock()
        user_id = "user123"

        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)

        mock_tasks = [
            Mock(
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                due_date=yesterday,  # Overdue
                completed_at=None,
                estimated_hours=None,
                actual_hours=0.0,
            ),
            Mock(
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                due_date=tomorrow,  # Not overdue
                completed_at=None,
                estimated_hours=None,
                actual_hours=0.0,
            ),
            Mock(
                status=TaskStatus.DONE,
                priority=TaskPriority.HIGH,
                due_date=yesterday,  # Past due but completed
                completed_at=datetime.now(timezone.utc),
                estimated_hours=None,
                actual_hours=2.0,
            ),
        ]

        mock_db.query.return_value.filter.return_value.all.return_value = mock_tasks

        stats = TaskService.get_task_statistics(mock_db, user_id)

        assert stats["overdue"] == 1  # Only the TODO task is overdue

    def test_get_task_statistics_due_today(self):
        """Test statistics for tasks due today"""
        mock_db = Mock()
        user_id = "user123"

        today = datetime.now(timezone.utc).replace(
            hour=12, minute=0, second=0, microsecond=0
        )

        mock_tasks = [
            Mock(
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                due_date=today,
                completed_at=None,
                estimated_hours=None,
                actual_hours=0.0,
            )
        ]

        mock_db.query.return_value.filter.return_value.all.return_value = mock_tasks

        stats = TaskService.get_task_statistics(mock_db, user_id)

        assert stats["due_today"] == 1


@pytest.mark.unit
class TestTaskFiltering:
    """Test cases for task filtering methods"""

    def test_get_overdue_tasks(self):
        """Test getting overdue tasks"""
        mock_db = Mock()
        user_id = "user123"

        # Create expected filter conditions
        TaskService.get_overdue_tasks(mock_db, user_id)

        # Verify the query was built correctly
        mock_db.query.assert_called_once_with(Task)
        mock_db.query.return_value.filter.assert_called_once()

    def test_get_upcoming_tasks(self):
        """Test getting upcoming tasks"""
        mock_db = Mock()
        user_id = "user123"
        days = 7

        # Mock the query chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        TaskService.get_upcoming_tasks(mock_db, user_id, days)

        # Verify query was called
        mock_db.query.assert_called_once_with(Task)
        mock_query.filter.assert_called_once()
        mock_query.order_by.assert_called_once()


@pytest.mark.unit
class TestTaskPositioning:
    """Test cases for task positioning"""

    def test_update_task_positions_success(self):
        """Test successful task position update"""
        mock_db = Mock()
        user_id = "user123"
        task_id = "task456"
        new_position = 2

        # Create mock tasks
        mock_tasks = [
            Mock(id="task1", position=0),
            Mock(id="task456", position=1),  # Task to move
            Mock(id="task3", position=2),
            Mock(id="task4", position=3),
        ]

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_tasks
        )

        result = TaskService.update_task_positions(
            mock_db, user_id, task_id, new_position
        )

        assert result is True
        mock_db.commit.assert_called_once()

        # Verify positions were updated
        assert mock_tasks[0].position == 0  # task1 stays at 0
        assert mock_tasks[1].position == 1  # task3 moves to 1
        assert mock_tasks[2].position == 2  # task456 at new position
        assert mock_tasks[3].position == 3  # task4 stays at 3

    def test_update_task_positions_task_not_found(self):
        """Test position update when task doesn't exist"""
        mock_db = Mock()
        user_id = "user123"
        task_id = "nonexistent"
        new_position = 1

        mock_tasks = [Mock(id="task1", position=0), Mock(id="task2", position=1)]

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_tasks
        )

        result = TaskService.update_task_positions(
            mock_db, user_id, task_id, new_position
        )

        assert result is False
        mock_db.commit.assert_not_called()

    def test_update_task_positions_edge_cases(self):
        """Test position update edge cases"""
        mock_db = Mock()
        user_id = "user123"

        # Test moving to position 0
        mock_tasks = [
            Mock(id="task1", position=0),
            Mock(id="task2", position=1),
            Mock(id="task3", position=2),
        ]

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_tasks.copy()
        )

        result = TaskService.update_task_positions(mock_db, user_id, "task3", 0)
        assert result is True
