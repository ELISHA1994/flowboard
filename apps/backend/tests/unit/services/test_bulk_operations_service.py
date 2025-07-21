"""
Unit tests for BulkOperationsService.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from sqlalchemy.orm import Session

from app.db.models import (Category, Project, ProjectRole, Tag, Task,
                           TaskPriority, TaskStatus, User)
from app.services.bulk_operations_service import BulkOperationsService
from app.services.tag_service import TagService


class TestBulkOperationsService:
    """Test BulkOperationsService functionality."""

    @patch("app.services.bulk_operations_service.Session")
    def test_validate_task_access_owned_tasks(self, mock_session):
        """Test validating access to owned tasks."""
        mock_db = Mock(spec=Session)

        # Mock owned tasks
        task1 = Mock(spec=Task, id="task1", user_id="user123")
        task2 = Mock(spec=Task, id="task2", user_id="user123")

        # Set up mock query chains
        mock_query = Mock()
        mock_db.query.return_value = mock_query

        # First query returns owned tasks
        mock_filter1 = Mock()
        mock_query.filter.return_value = mock_filter1
        mock_filter1.all.return_value = [task1, task2]

        # Second query for project tasks returns empty (since all are owned)
        mock_filter2 = Mock()
        mock_query.filter.side_effect = [mock_filter1, mock_filter2]
        mock_filter2.all.return_value = []

        # Execute
        accessible_tasks = BulkOperationsService.validate_task_access(
            mock_db, "user123", ["task1", "task2", "task3"]
        )

        # Verify
        assert len(accessible_tasks) == 2
        assert task1 in accessible_tasks
        assert task2 in accessible_tasks

    @patch("app.services.bulk_operations_service.Session")
    def test_validate_task_access_with_project_permission(self, mock_session):
        """Test validating access to project tasks."""
        mock_db = Mock(spec=Session)

        # Mock owned tasks (empty)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.all.side_effect = [
            [],  # No owned tasks
            [  # Project tasks
                Mock(
                    spec=Task,
                    id="task3",
                    project_id="proj1",
                    project=Mock(has_permission=Mock(return_value=True)),
                ),
                Mock(
                    spec=Task,
                    id="task4",
                    project_id="proj2",
                    project=Mock(has_permission=Mock(return_value=False)),
                ),
            ],
        ]

        # Execute
        accessible_tasks = BulkOperationsService.validate_task_access(
            mock_db, "user123", ["task3", "task4"]
        )

        # Verify only task with permission is returned
        assert len(accessible_tasks) == 1
        assert accessible_tasks[0].id == "task3"

    @patch("app.services.bulk_operations_service.Session")
    def test_update_status(self, mock_session):
        """Test bulk status update."""
        mock_db = Mock(spec=Session)

        # Mock accessible tasks
        task1 = Mock(spec=Task, status=TaskStatus.TODO, completed_at=None)
        task2 = Mock(spec=Task, status=TaskStatus.TODO, completed_at=None)

        with patch.object(
            BulkOperationsService, "validate_task_access", return_value=[task1, task2]
        ):
            # Execute status update to DONE
            result = BulkOperationsService.update_status(
                mock_db, "user123", ["task1", "task2"], TaskStatus.DONE
            )

        # Verify
        assert result["success"] is True
        assert result["updated_count"] == 2
        assert task1.status == TaskStatus.DONE
        assert task2.status == TaskStatus.DONE
        assert task1.completed_at is not None
        assert task2.completed_at is not None
        mock_db.commit.assert_called_once()

    @patch("app.services.bulk_operations_service.Session")
    def test_update_status_no_accessible_tasks(self, mock_session):
        """Test status update with no accessible tasks."""
        mock_db = Mock(spec=Session)

        with patch.object(
            BulkOperationsService, "validate_task_access", return_value=[]
        ):
            result = BulkOperationsService.update_status(
                mock_db, "user123", ["task1"], TaskStatus.DONE
            )

        # Verify
        assert result["success"] is False
        assert result["message"] == "No accessible tasks found"
        assert result["updated_count"] == 0
        mock_db.commit.assert_not_called()

    @patch("app.services.bulk_operations_service.Session")
    def test_update_priority(self, mock_session):
        """Test bulk priority update."""
        mock_db = Mock(spec=Session)

        # Mock accessible tasks
        task1 = Mock(spec=Task, priority=TaskPriority.LOW)
        task2 = Mock(spec=Task, priority=TaskPriority.MEDIUM)

        with patch.object(
            BulkOperationsService, "validate_task_access", return_value=[task1, task2]
        ):
            result = BulkOperationsService.update_priority(
                mock_db, "user123", ["task1", "task2"], TaskPriority.HIGH
            )

        # Verify
        assert result["success"] is True
        assert result["updated_count"] == 2
        assert task1.priority == TaskPriority.HIGH
        assert task2.priority == TaskPriority.HIGH
        mock_db.commit.assert_called_once()

    @patch("app.services.bulk_operations_service.Session")
    def test_update_assigned_to(self, mock_session):
        """Test bulk assignment update."""
        mock_db = Mock(spec=Session)

        # Mock assigned user exists
        mock_user = Mock(spec=User, id="user456")
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_user

        # Mock accessible tasks
        task1 = Mock(spec=Task, project_id=None)
        task2 = Mock(
            spec=Task,
            project_id="proj1",
            project=Mock(has_permission=Mock(return_value=True)),
        )

        with patch.object(
            BulkOperationsService, "validate_task_access", return_value=[task1, task2]
        ):
            result = BulkOperationsService.update_assigned_to(
                mock_db, "user123", ["task1", "task2"], "user456"
            )

        # Verify
        assert result["success"] is True
        assert result["updated_count"] == 2
        assert task1.assigned_to_id == "user456"
        assert task2.assigned_to_id == "user456"
        mock_db.commit.assert_called_once()

    @patch("app.services.bulk_operations_service.Session")
    def test_update_assigned_to_user_not_found(self, mock_session):
        """Test assignment update with non-existent user."""
        mock_db = Mock(spec=Session)

        # Mock user not found
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        result = BulkOperationsService.update_assigned_to(
            mock_db, "user123", ["task1"], "nonexistent"
        )

        # Verify
        assert result["success"] is False
        assert result["message"] == "Assigned user not found"
        mock_db.commit.assert_not_called()

    @patch("app.services.bulk_operations_service.TagService.add_tags_to_task")
    @patch("app.services.bulk_operations_service.Session")
    def test_add_tags(self, mock_session, mock_add_tags):
        """Test bulk tag addition."""
        mock_db = Mock(spec=Session)

        # Mock accessible tasks with existing tags
        task1 = Mock(spec=Task, id="task1", tags=[Mock(name="existing")])
        task2 = Mock(spec=Task, id="task2", tags=[])

        with patch.object(
            BulkOperationsService, "validate_task_access", return_value=[task1, task2]
        ):
            result = BulkOperationsService.add_tags(
                mock_db, "user123", ["task1", "task2"], ["urgent", "bug"]
            )

        # Verify
        assert result["success"] is True
        assert result["updated_count"] == 2
        # Should be called for both tasks
        assert mock_add_tags.call_count == 2
        mock_db.commit.assert_called_once()

    @patch("app.services.bulk_operations_service.Session")
    def test_remove_tags(self, mock_session):
        """Test bulk tag removal."""
        mock_db = Mock(spec=Session)

        # Mock accessible tasks with tags
        tag1 = Mock()
        tag1.name = "urgent"
        tag2 = Mock()
        tag2.name = "bug"
        tag3 = Mock()
        tag3.name = "feature"

        task1 = Mock(spec=Task, tags=[tag1, tag2, tag3])
        task2 = Mock(spec=Task, tags=[tag1, tag3])

        with patch.object(
            BulkOperationsService, "validate_task_access", return_value=[task1, task2]
        ):
            result = BulkOperationsService.remove_tags(
                mock_db, "user123", ["task1", "task2"], ["urgent", "bug"]
            )

        # Verify
        assert result["success"] is True
        assert result["updated_count"] == 2
        # task1 should only have 'feature' tag
        assert len(task1.tags) == 1
        assert task1.tags[0].name == "feature"
        # task2 should only have 'feature' tag
        assert len(task2.tags) == 1
        assert task2.tags[0].name == "feature"
        mock_db.commit.assert_called_once()

    @patch("app.services.bulk_operations_service.Session")
    def test_add_categories(self, mock_session):
        """Test bulk category addition."""
        mock_db = Mock(spec=Session)

        # Mock categories exist and belong to user
        cat1 = Mock(spec=Category, id="cat1")
        cat2 = Mock(spec=Category, id="cat2")

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.all.return_value = [cat1, cat2]

        # Mock accessible tasks
        task1 = Mock(spec=Task, categories=[])
        task2 = Mock(spec=Task, categories=[cat1])  # Already has cat1

        with patch.object(
            BulkOperationsService, "validate_task_access", return_value=[task1, task2]
        ):
            result = BulkOperationsService.add_categories(
                mock_db, "user123", ["task1", "task2"], ["cat1", "cat2"]
            )

        # Verify
        assert result["success"] is True
        assert result["updated_count"] == 2
        mock_db.commit.assert_called_once()

    @patch("app.services.bulk_operations_service.Session")
    def test_delete_tasks(self, mock_session):
        """Test bulk task deletion."""
        mock_db = Mock(spec=Session)

        # Mock owned tasks
        task1 = Mock(spec=Task, id="task1", user_id="user123")

        # Mock project task where user is admin
        task2 = Mock(
            spec=Task,
            id="task2",
            project_id="proj1",
            project=Mock(has_permission=Mock(return_value=True)),
        )

        # Mock project task where user is not admin
        task3 = Mock(
            spec=Task,
            id="task3",
            project_id="proj2",
            project=Mock(has_permission=Mock(return_value=False)),
        )

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.all.side_effect = [
            [task1],  # Owned tasks
            [task2, task3],  # Project tasks
        ]

        result = BulkOperationsService.delete_tasks(
            mock_db, "user123", ["task1", "task2", "task3"]
        )

        # Verify
        assert result["success"] is True
        assert result["deleted_count"] == 2  # Only task1 and task2
        assert result["inaccessible_count"] == 1
        assert mock_db.delete.call_count == 2
        mock_db.commit.assert_called_once()

    @patch("app.services.bulk_operations_service.Session")
    def test_move_to_project(self, mock_session):
        """Test bulk move to project."""
        mock_db = Mock(spec=Session)

        # Mock project exists and user has permission
        mock_project = Mock(spec=Project, id="proj1")
        mock_project.has_permission.return_value = True

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_project

        # Mock accessible tasks
        task1 = Mock(spec=Task, project_id=None)
        task2 = Mock(spec=Task, project_id="old_proj")

        with patch.object(
            BulkOperationsService, "validate_task_access", return_value=[task1, task2]
        ):
            result = BulkOperationsService.move_to_project(
                mock_db, "user123", ["task1", "task2"], "proj1"
            )

        # Verify
        assert result["success"] is True
        assert result["updated_count"] == 2
        assert task1.project_id == "proj1"
        assert task2.project_id == "proj1"
        mock_project.has_permission.assert_called_with("user123", ProjectRole.MEMBER)
        mock_db.commit.assert_called_once()

    @patch("app.services.bulk_operations_service.Session")
    def test_move_to_project_no_permission(self, mock_session):
        """Test move to project without permission."""
        mock_db = Mock(spec=Session)

        # Mock project exists but user has no permission
        mock_project = Mock(spec=Project)
        mock_project.has_permission.return_value = False

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_project

        result = BulkOperationsService.move_to_project(
            mock_db, "user123", ["task1"], "proj1"
        )

        # Verify
        assert result["success"] is False
        assert (
            result["message"]
            == "You don't have permission to add tasks to this project"
        )
        mock_db.commit.assert_not_called()
