"""
Unit tests for TagService
"""

import uuid
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.db.models import Tag, Task, User
from app.models.tag import TagCreate, TagUpdate
from app.services.tag_service import TagService


@pytest.mark.unit
class TestTagService:
    """Test TagService methods"""

    def test_create_tag_new(self):
        """Test creating a new tag"""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = None  # No existing tag

        # Test data
        user_id = "test-user-123"
        tag_data = TagCreate(name="urgent", color="#FF0000")

        # Call service
        result = TagService.create_tag(mock_db, user_id, tag_data)

        # Verify
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_tag_existing_returns_existing(self):
        """Test creating tag that already exists returns existing"""
        # Mock database session
        mock_db = Mock(spec=Session)
        existing_tag = Tag(id="existing-id", name="urgent", color="#FF0000")
        mock_db.query().filter().first.return_value = existing_tag

        # Test data
        user_id = "test-user-123"
        tag_data = TagCreate(name="urgent", color="#00FF00")

        # Call service
        result = TagService.create_tag(mock_db, user_id, tag_data)

        # Verify - should return existing tag, not create new
        assert result == existing_tag
        mock_db.add.assert_not_called()

    def test_get_or_create_tags(self):
        """Test get_or_create_tags functionality"""
        # Mock database session
        mock_db = Mock(spec=Session)

        # Mock existing tag
        existing_tag = Tag(id="existing-id", name="bug", color="#FF0000")

        # Setup mocks for each tag lookup
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter1.first.return_value = existing_tag  # bug exists
        mock_filter2 = Mock()
        mock_filter2.first.return_value = None  # feature doesn't exist
        mock_filter3 = Mock()
        mock_filter3.first.return_value = None  # todo doesn't exist

        # Configure query chain to return different results
        mock_query.filter.side_effect = [mock_filter1, mock_filter2, mock_filter3]
        mock_db.query.return_value = mock_query

        # Test data
        user_id = "test-user-123"
        tag_names = ["bug", "feature", "todo"]

        # Call service
        with patch("uuid.uuid4", side_effect=["new-uuid-1", "new-uuid-2"]):
            result = TagService.get_or_create_tags(mock_db, user_id, tag_names)

        # Verify
        assert len(result) == 3
        assert result[0].name == "bug"  # Existing tag
        assert result[0] == existing_tag
        assert mock_db.add.call_count == 2  # Two new tags created
        mock_db.commit.assert_called_once()

    def test_get_user_tags(self):
        """Test getting all user tags"""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_tags = [
            Tag(id="1", name="bug"),
            Tag(id="2", name="feature"),
            Tag(id="3", name="urgent"),
        ]

        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_tags
        mock_db.query.return_value = mock_query

        # Call service
        result = TagService.get_user_tags(mock_db, "user-123")

        # Verify
        assert len(result) == 3
        assert result == mock_tags

    def test_update_tag(self):
        """Test updating a tag"""
        # Mock database session
        mock_db = Mock(spec=Session)
        existing_tag = Tag(id="tag-123", name="bug", color="#FF0000")

        # Mock get_tag
        TagService.get_tag = Mock(return_value=existing_tag)
        mock_db.query().filter().first.return_value = None  # No duplicate

        # Test data
        update_data = TagUpdate(name="critical-bug", color="#FF00FF")

        # Call service
        result = TagService.update_tag(mock_db, "tag-123", "user-123", update_data)

        # Verify
        assert existing_tag.name == "critical-bug"
        assert existing_tag.color == "#FF00FF"
        mock_db.commit.assert_called_once()

    def test_delete_tag(self):
        """Test deleting a tag (hard delete)"""
        # Mock database session
        mock_db = Mock(spec=Session)
        existing_tag = Tag(id="tag-123", name="obsolete")

        # Mock get_tag
        TagService.get_tag = Mock(return_value=existing_tag)

        # Call service
        result = TagService.delete_tag(mock_db, "tag-123", "user-123")

        # Verify
        assert result is True
        mock_db.delete.assert_called_once_with(existing_tag)
        mock_db.commit.assert_called_once()

    def test_set_task_tags(self):
        """Test setting tags for a task (replace existing)"""
        # Mock database session
        mock_db = Mock(spec=Session)

        # Mock task with existing tags
        old_tag = Tag(id="old-tag", name="old")
        mock_task = Mock(spec=Task)
        mock_task.tags = [old_tag]

        new_tags = [Tag(id="1", name="new1"), Tag(id="2", name="new2")]

        mock_db.query().filter().first.return_value = mock_task
        TagService.get_or_create_tags = Mock(return_value=new_tags)

        # Call service
        result = TagService.set_task_tags(
            mock_db, "task-123", ["new1", "new2"], "user-123"
        )

        # Verify
        assert mock_task.tags == new_tags
        assert old_tag not in mock_task.tags
        mock_db.commit.assert_called_once()

    def test_add_tags_to_task(self):
        """Test adding tags to a task (keep existing)"""
        # Mock database session
        mock_db = Mock(spec=Session)

        # Mock task with existing tags
        existing_tag = Mock(spec=Tag, id="existing", name="bug")
        new_tag = Mock(spec=Tag, id="new", name="feature")

        # Create a mock list that we can track
        initial_tags = [existing_tag]

        mock_task = Mock(spec=Task)
        mock_task.tags = initial_tags

        mock_db.query().filter().first.return_value = mock_task
        TagService.get_or_create_tags = Mock(return_value=[new_tag, existing_tag])

        # Call service
        result = TagService.add_tags_to_task(
            mock_db, "task-123", ["feature", "bug"], "user-123"
        )

        # Verify - task should have both tags
        assert len(mock_task.tags) == 2
        assert existing_tag in mock_task.tags
        assert new_tag in mock_task.tags
        mock_db.commit.assert_called_once()

    def test_get_popular_tags(self):
        """Test getting popular tags sorted by usage"""
        # Mock database session
        mock_db = Mock(spec=Session)

        # Mock tags with different task counts
        tag1 = Mock(spec=Tag, name="bug", tasks=[1, 2, 3, 4, 5])  # 5 tasks
        tag2 = Mock(spec=Tag, name="feature", tasks=[1, 2])  # 2 tasks
        tag3 = Mock(spec=Tag, name="urgent", tasks=[1, 2, 3])  # 3 tasks
        tag4 = Mock(spec=Tag, name="unused", tasks=[])  # 0 tasks

        mock_tags = [tag1, tag2, tag3, tag4]
        mock_db.query().filter().all.return_value = mock_tags

        # Call service
        result = TagService.get_popular_tags(mock_db, "user-123", limit=3)

        # Verify - should be sorted by task count, unused excluded
        assert len(result) == 3
        assert result[0]["tag"] == tag1  # Most used
        assert result[0]["task_count"] == 5
        assert result[1]["tag"] == tag3
        assert result[2]["tag"] == tag2
