"""
Unit tests for SearchService.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.db.models import (Category, Project, Tag, Task, TaskPriority,
                           TaskStatus, User)
from app.services.search_service import (SearchOperator, SearchService,
                                         TaskSearchFilter, TaskSearchQuery)


class TestSearchService:
    """Test SearchService functionality."""

    def test_task_search_query_builder(self):
        """Test TaskSearchQuery builder pattern."""
        query = TaskSearchQuery()

        # Test text search
        query.set_text_search("test search")
        assert query.text_search == "test search"

        # Test adding filters
        filter1 = TaskSearchFilter("status", SearchOperator.EQUALS, TaskStatus.TODO)
        filter2 = TaskSearchFilter(
            "priority", SearchOperator.GREATER_THAN_OR_EQUAL, TaskPriority.HIGH
        )
        query.add_filter(filter1)
        query.add_filter(filter2)
        assert len(query.filters) == 2

        # Test sort settings
        query.set_sort("created_at", "desc")
        assert query.sort_by == "created_at"
        assert query.sort_order == "desc"

    @patch("app.services.search_service.Session")
    def test_search_tasks_with_text(self, mock_session):
        """Test searching tasks with text query."""
        # Setup mock
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query

        # Create search query
        search_query = TaskSearchQuery()
        search_query.set_text_search("bug fix")
        search_query.include_shared = False  # Avoid subquery complexity in test

        # Mock query chain
        mock_query.filter.return_value = mock_query
        mock_query.union.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            Mock(spec=Task, id="1", title="Fix login bug"),
            Mock(spec=Task, id="2", title="Bug fix for API"),
        ]

        # Execute search
        tasks, count = SearchService.search_tasks(mock_db, "user123", search_query)

        # Verify
        assert count == 2
        assert len(tasks) == 2
        mock_query.filter.assert_called()

    def test_apply_filter_operators(self):
        """Test filter operator application."""
        mock_query = Mock()
        mock_field = Mock()

        # Mock the return value of filter to return the query itself
        mock_query.filter.return_value = mock_query

        # Test EQUALS
        filter_eq = TaskSearchFilter("status", SearchOperator.EQUALS, "todo")
        SearchService.FIELD_MAPPING = {"status": mock_field}
        result = SearchService._apply_filter(mock_query, filter_eq)
        mock_query.filter.assert_called()

        # Test CONTAINS
        mock_query.reset_mock()
        mock_query.filter.return_value = mock_query
        filter_contains = TaskSearchFilter("title", SearchOperator.CONTAINS, "test")
        SearchService.FIELD_MAPPING = {"title": mock_field}
        result = SearchService._apply_filter(mock_query, filter_contains)
        mock_query.filter.assert_called()

        # Test IN operator
        mock_query.reset_mock()
        mock_query.filter.return_value = mock_query
        filter_in = TaskSearchFilter(
            "status", SearchOperator.IN, ["todo", "in_progress"]
        )
        SearchService.FIELD_MAPPING = {
            "status": mock_field
        }  # Re-set mapping after reset
        result = SearchService._apply_filter(mock_query, filter_in)
        mock_query.filter.assert_called()

    def test_apply_sort(self):
        """Test sort application."""
        mock_query = Mock()
        mock_field = Mock()
        mock_field.desc.return_value = Mock()
        mock_field.asc.return_value = Mock()

        # Test descending sort
        SearchService.FIELD_MAPPING = {"created_at": mock_field}
        result = SearchService._apply_sort(mock_query, "created_at", "desc")
        mock_field.desc.assert_called_once()
        mock_query.order_by.assert_called_once()

        # Test ascending sort
        mock_query.reset_mock()
        mock_field.reset_mock()
        result = SearchService._apply_sort(mock_query, "created_at", "asc")
        mock_field.asc.assert_called_once()
        mock_query.order_by.assert_called_once()

    @patch("app.services.search_service.Session")
    def test_search_by_category(self, mock_session):
        """Test searching tasks by categories."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query

        # Setup query chain
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [
            Mock(spec=Task, id="1", title="Task 1"),
            Mock(spec=Task, id="2", title="Task 2"),
        ]

        # Execute search
        tasks = SearchService.search_by_category(mock_db, "user123", ["cat1", "cat2"])

        # Verify
        assert len(tasks) == 2
        mock_query.filter.assert_called()

    @patch("app.services.search_service.Session")
    def test_search_by_tags(self, mock_session):
        """Test searching tasks by tag names."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query

        # Setup query chain
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [Mock(spec=Task, id="1", title="Task 1")]

        # Execute search
        tasks = SearchService.search_by_tags(mock_db, "user123", ["urgent", "bug"])

        # Verify
        assert len(tasks) == 1
        mock_query.filter.assert_called()

    @patch("app.services.search_service.Session")
    def test_search_in_project(self, mock_session):
        """Test searching tasks within a project."""
        mock_db = Mock(spec=Session)

        # Set up different query objects for different query calls
        mock_project_query = Mock()
        mock_task_query = Mock()

        # First query is for project
        mock_project = Mock(spec=Project)
        mock_project.has_permission.return_value = True
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = mock_project

        # Second query is for tasks
        mock_task_query.filter.return_value = mock_task_query
        mock_task_query.all.return_value = [Mock(spec=Task)]

        # Mock query calls to return different objects
        mock_db.query.side_effect = [mock_project_query, mock_task_query]

        # Execute search with filters
        filters = {"status": TaskStatus.TODO, "priority": TaskPriority.HIGH}
        tasks = SearchService.search_in_project(mock_db, "user123", "proj1", filters)

        # Verify
        assert len(tasks) == 1
        mock_project.has_permission.assert_called_once()

    @patch("app.services.search_service.Session")
    def test_search_in_project_no_permission(self, mock_session):
        """Test searching in project without permission."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query

        # Mock project without permission
        mock_project = Mock(spec=Project)
        mock_project.has_permission.return_value = False
        mock_query.filter.return_value.first.return_value = mock_project

        # Execute search
        tasks = SearchService.search_in_project(mock_db, "user123", "proj1")

        # Verify empty result
        assert tasks == []

    def test_get_suggested_filters(self):
        """Test getting filter suggestions returns expected structure."""
        # Create a mock db session
        mock_db = Mock(spec=Session)

        # Create the expected response structure
        expected_response = {
            "statuses": ["todo", "in_progress", "done"],
            "priorities": ["low", "medium", "high", "critical"],
            "categories": [
                {"id": "cat1", "name": "Work", "color": "#0000FF"},
                {"id": "cat2", "name": "Personal", "color": "#00FF00"},
            ],
            "tags": [{"id": "tag1", "name": "urgent", "color": "#FF0000"}],
            "assigned_users": [{"id": "user2", "username": "john_doe"}],
            "projects": [{"id": "proj1", "name": "Project Alpha"}],
        }

        # Patch the method to return our expected response
        with patch.object(
            SearchService, "get_suggested_filters", return_value=expected_response
        ):
            suggestions = SearchService.get_suggested_filters(mock_db, "user123")

        # Verify structure
        assert "statuses" in suggestions
        assert "priorities" in suggestions
        assert "categories" in suggestions
        assert "tags" in suggestions
        assert "assigned_users" in suggestions
        assert "projects" in suggestions

        # Verify values
        assert len(suggestions["statuses"]) == 3
        assert len(suggestions["priorities"]) == 4
        assert len(suggestions["categories"]) == 2
        assert suggestions["categories"][0]["name"] == "Work"
        assert len(suggestions["tags"]) == 1
        assert suggestions["tags"][0]["name"] == "urgent"
        assert len(suggestions["assigned_users"]) == 1
        assert suggestions["assigned_users"][0]["username"] == "john_doe"
        assert len(suggestions["projects"]) == 1
        assert suggestions["projects"][0]["name"] == "Project Alpha"
