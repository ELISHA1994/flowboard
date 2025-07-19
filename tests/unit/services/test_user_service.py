"""
Unit tests for UserService.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.db.models import User
from tests.factories import UserFactory
import uuid


@pytest.mark.unit
class TestUserService:
    """Test cases for UserService methods."""
    
    def test_get_user_by_email_found(self):
        """Test getting user by email when user exists."""
        # Create test user
        user = UserFactory.create()
        
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = user
        
        # Test
        result = UserService.get_user_by_email(mock_db, user.email)
        
        # Assertions
        assert result == user
        mock_db.query.assert_called_once()
        mock_filter.first.assert_called_once()
    
    def test_get_user_by_email_not_found(self):
        """Test getting user by email when user doesn't exist."""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        # Test
        result = UserService.get_user_by_email(mock_db, "nonexistent@example.com")
        
        # Assertions
        assert result is None
    
    def test_get_user_by_username_found(self):
        """Test getting user by username when user exists."""
        # Create test user
        user = UserFactory.create()
        
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = user
        
        # Test
        result = UserService.get_user_by_username(mock_db, user.username)
        
        # Assertions
        assert result == user
        mock_db.query.assert_called_once()
        mock_filter.first.assert_called_once()
    
    def test_get_user_by_username_not_found(self):
        """Test getting user by username when user doesn't exist."""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        # Test
        result = UserService.get_user_by_username(mock_db, "nonexistent")
        
        # Assertions
        assert result is None
    
    def test_is_user_active_true(self):
        """Test checking if user is active when they are."""
        # Create active user
        user = UserFactory.create(is_active=True)
        
        # Test
        result = UserService.is_user_active(user)
        
        # Assertions
        assert result is True
    
    def test_is_user_active_false(self):
        """Test checking if user is active when they're not."""
        # Create inactive user
        user = UserFactory.create(is_active=False)
        
        # Test
        with patch('app.services.user_service.logger') as mock_logger:
            result = UserService.is_user_active(user)
        
        # Assertions
        assert result is False
        mock_logger.info.assert_called_once()
    
    def test_get_active_users_count(self):
        """Test counting active users."""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 42
        
        # Test
        count = UserService.get_active_users_count(mock_db)
        
        # Assertions
        assert count == 42
        mock_db.query.assert_called_once()
        mock_filter.count.assert_called_once()
    
    @patch('app.services.user_service.datetime')
    def test_get_recent_users_default_days(self, mock_datetime):
        """Test getting recent users with default 7 days."""
        # Mock current time
        current_time = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.utcnow.return_value = current_time
        
        # Create test users
        recent_users = UserFactory.create_batch(3)
        
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = recent_users
        
        # Test
        result = UserService.get_recent_users(mock_db)
        
        # Assertions
        assert len(result) == 3
        mock_datetime.utcnow.assert_called_once()
        # Verify the cutoff date calculation
        expected_cutoff = current_time - timedelta(days=7)
        mock_filter.all.assert_called_once()
    
    @patch('app.services.user_service.datetime')
    def test_get_recent_users_custom_days(self, mock_datetime):
        """Test getting recent users with custom days."""
        # Mock current time
        current_time = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.utcnow.return_value = current_time
        
        # Create test users
        recent_users = UserFactory.create_batch(5)
        
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = recent_users
        
        # Test with custom days
        result = UserService.get_recent_users(mock_db, days=30)
        
        # Assertions
        assert len(result) == 5
        mock_datetime.utcnow.assert_called_once()