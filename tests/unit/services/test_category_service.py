"""
Unit tests for CategoryService
"""
import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
from app.services.category_service import CategoryService
from app.models.category import CategoryCreate, CategoryUpdate
from app.db.models import Category, Task, User
import uuid


@pytest.mark.unit
class TestCategoryService:
    """Test CategoryService methods"""
    
    def test_create_category_success(self):
        """Test successful category creation"""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = None  # No existing category
        
        # Test data
        user_id = "test-user-123"
        category_data = CategoryCreate(
            name="Work",
            description="Work related tasks",
            color="#FF5733",
            icon="💼"
        )
        
        # Call service
        result = CategoryService.create_category(mock_db, user_id, category_data)
        
        # Verify
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_create_category_duplicate_name(self):
        """Test creating category with duplicate name"""
        # Mock database session
        mock_db = Mock(spec=Session)
        existing_category = Category(id="existing-id", name="Work")
        mock_db.query().filter().first.return_value = existing_category
        
        # Test data
        user_id = "test-user-123"
        category_data = CategoryCreate(name="Work")
        
        # Call service and expect ValueError
        with pytest.raises(ValueError) as exc_info:
            CategoryService.create_category(mock_db, user_id, category_data)
        
        assert "already exists" in str(exc_info.value)
        mock_db.add.assert_not_called()
    
    def test_get_user_categories(self):
        """Test getting user categories"""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_categories = [
            Category(id="1", name="Work", is_active=True),
            Category(id="2", name="Personal", is_active=True),
            Category(id="3", name="Archive", is_active=False)
        ]
        
        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_categories[:2]  # Only active
        mock_db.query.return_value = mock_query
        
        # Test getting only active categories
        result = CategoryService.get_user_categories(mock_db, "user-123", include_inactive=False)
        
        assert len(result) == 2
        assert mock_query.filter.call_count == 2  # user_id and is_active filters
    
    def test_update_category(self):
        """Test updating a category"""
        # Mock database session
        mock_db = Mock(spec=Session)
        existing_category = Category(
            id="cat-123",
            name="Work",
            description="Old description",
            color="#000000"
        )
        
        # Mock get_category
        CategoryService.get_category = Mock(return_value=existing_category)
        mock_db.query().filter().first.return_value = None  # No duplicate name
        
        # Test data
        update_data = CategoryUpdate(
            name="Work Projects",
            description="Updated description",
            color="#FF5733"
        )
        
        # Call service
        result = CategoryService.update_category(mock_db, "cat-123", "user-123", update_data)
        
        # Verify
        assert existing_category.name == "Work Projects"
        assert existing_category.description == "Updated description"
        assert existing_category.color == "#FF5733"
        mock_db.commit.assert_called_once()
    
    def test_delete_category_soft_delete(self):
        """Test soft deleting a category"""
        # Mock database session
        mock_db = Mock(spec=Session)
        existing_category = Category(id="cat-123", is_active=True)
        
        # Mock get_category
        CategoryService.get_category = Mock(return_value=existing_category)
        
        # Call service
        result = CategoryService.delete_category(mock_db, "cat-123", "user-123")
        
        # Verify
        assert result is True
        assert existing_category.is_active is False
        mock_db.commit.assert_called_once()
    
    def test_add_category_to_task(self):
        """Test adding a category to a task"""
        # Mock database session
        mock_db = Mock(spec=Session)
        
        # Mock task and category
        mock_task = Mock(spec=Task)
        mock_task.categories = []
        mock_category = Mock(spec=Category)
        
        mock_db.query().filter().first.return_value = mock_task
        CategoryService.get_category = Mock(return_value=mock_category)
        
        # Call service
        result = CategoryService.add_category_to_task(mock_db, "task-123", "cat-123", "user-123")
        
        # Verify
        assert result is True
        assert mock_category in mock_task.categories
        mock_db.commit.assert_called_once()
    
    def test_remove_category_from_task(self):
        """Test removing a category from a task"""
        # Mock database session
        mock_db = Mock(spec=Session)
        
        # Mock task and category
        mock_category = Mock(spec=Category)
        mock_task = Mock(spec=Task)
        mock_categories_list = Mock()
        mock_categories_list.__contains__ = Mock(return_value=True)
        mock_task.categories = mock_categories_list
        
        mock_db.query().filter().first.return_value = mock_task
        CategoryService.get_category = Mock(return_value=mock_category)
        
        # Call service
        result = CategoryService.remove_category_from_task(mock_db, "task-123", "cat-123", "user-123")
        
        # Verify
        assert result is True
        mock_categories_list.remove.assert_called_with(mock_category)
        mock_db.commit.assert_called_once()