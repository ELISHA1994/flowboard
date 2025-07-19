"""
Unit tests for application constants.
"""
import pytest
from app.utils import constants


@pytest.mark.unit
class TestTaskConstants:
    """Test cases for task-related constants."""
    
    def test_max_tasks_per_user(self):
        """Test MAX_TASKS_PER_USER constant."""
        assert constants.MAX_TASKS_PER_USER == 100
        assert isinstance(constants.MAX_TASKS_PER_USER, int)
        assert constants.MAX_TASKS_PER_USER > 0
    
    def test_task_title_length_constants(self):
        """Test task title length constants."""
        assert constants.MAX_TASK_TITLE_LENGTH == 200
        assert isinstance(constants.MAX_TASK_TITLE_LENGTH, int)
        assert constants.MAX_TASK_TITLE_LENGTH > 0
    
    def test_task_description_length_constants(self):
        """Test task description length constants."""
        assert constants.MAX_TASK_DESCRIPTION_LENGTH == 1000
        assert isinstance(constants.MAX_TASK_DESCRIPTION_LENGTH, int)
        assert constants.MAX_TASK_DESCRIPTION_LENGTH > constants.MAX_TASK_TITLE_LENGTH


@pytest.mark.unit
class TestUserConstants:
    """Test cases for user-related constants."""
    
    def test_username_length_constants(self):
        """Test username length constants."""
        assert constants.MIN_USERNAME_LENGTH == 3
        assert constants.MAX_USERNAME_LENGTH == 50
        assert isinstance(constants.MIN_USERNAME_LENGTH, int)
        assert isinstance(constants.MAX_USERNAME_LENGTH, int)
        assert constants.MIN_USERNAME_LENGTH < constants.MAX_USERNAME_LENGTH
        assert constants.MIN_USERNAME_LENGTH > 0
    
    def test_password_length_constants(self):
        """Test password length constants."""
        assert constants.MIN_PASSWORD_LENGTH == 6
        assert isinstance(constants.MIN_PASSWORD_LENGTH, int)
        assert constants.MIN_PASSWORD_LENGTH > 0


@pytest.mark.unit
class TestPaginationConstants:
    """Test cases for pagination constants."""
    
    def test_pagination_defaults(self):
        """Test pagination default values."""
        assert constants.DEFAULT_PAGE_SIZE == 10
        assert constants.MAX_PAGE_SIZE == 100
        assert isinstance(constants.DEFAULT_PAGE_SIZE, int)
        assert isinstance(constants.MAX_PAGE_SIZE, int)
        assert 0 < constants.DEFAULT_PAGE_SIZE <= constants.MAX_PAGE_SIZE


@pytest.mark.unit
class TestAPIMessages:
    """Test cases for API response message constants."""
    
    def test_success_messages(self):
        """Test success message constants."""
        assert constants.MSG_SUCCESS == "Operation completed successfully"
        assert constants.MSG_CREATED == "Resource created successfully"
        assert constants.MSG_UPDATED == "Resource updated successfully"
        assert constants.MSG_DELETED == "Resource deleted successfully"
        
        # Ensure all success messages are non-empty strings
        success_messages = [
            constants.MSG_SUCCESS,
            constants.MSG_CREATED,
            constants.MSG_UPDATED,
            constants.MSG_DELETED
        ]
        for msg in success_messages:
            assert isinstance(msg, str)
            assert len(msg) > 0
            assert "successfully" in msg.lower()
    
    def test_error_messages(self):
        """Test error message constants."""
        assert constants.MSG_NOT_FOUND == "Resource not found"
        assert constants.MSG_UNAUTHORIZED == "Unauthorized access"
        assert constants.MSG_FORBIDDEN == "Forbidden action"
        
        # Ensure all error messages are non-empty strings
        error_messages = [
            constants.MSG_NOT_FOUND,
            constants.MSG_UNAUTHORIZED,
            constants.MSG_FORBIDDEN
        ]
        for msg in error_messages:
            assert isinstance(msg, str)
            assert len(msg) > 0


@pytest.mark.unit
class TestConstantsConsistency:
    """Test cases for constants consistency and relationships."""
    
    def test_constants_naming_convention(self):
        """Test that all constants follow UPPER_CASE naming convention."""
        # Get all attributes from constants module
        all_attrs = dir(constants)
        
        # Filter to actual constants (exclude dunder methods and imports)
        const_attrs = [attr for attr in all_attrs 
                      if not attr.startswith('_') 
                      and attr.isupper()]
        
        # Ensure we have constants
        assert len(const_attrs) > 0
        
        # All constant names should be uppercase
        for attr in const_attrs:
            assert attr.isupper(), f"Constant {attr} should be in UPPER_CASE"
    
    def test_length_constants_relationship(self):
        """Test relationships between length constants."""
        # Task description should be longer than title
        assert constants.MAX_TASK_DESCRIPTION_LENGTH > constants.MAX_TASK_TITLE_LENGTH
        
        # Username should be shorter than task title
        assert constants.MAX_USERNAME_LENGTH < constants.MAX_TASK_TITLE_LENGTH
        
        # Password minimum should be reasonable
        assert constants.MIN_PASSWORD_LENGTH >= 6  # Security best practice
        assert constants.MIN_PASSWORD_LENGTH < constants.MAX_USERNAME_LENGTH
    
    def test_pagination_constants_relationship(self):
        """Test pagination constants are sensible."""
        # Default should be reasonable
        assert constants.DEFAULT_PAGE_SIZE >= 10
        assert constants.DEFAULT_PAGE_SIZE <= 50
        
        # Max should prevent abuse
        assert constants.MAX_PAGE_SIZE >= 50
        assert constants.MAX_PAGE_SIZE <= 1000
    
    def test_all_constants_defined(self):
        """Test that all expected constants are defined."""
        expected_constants = [
            'MAX_TASKS_PER_USER',
            'MAX_TASK_TITLE_LENGTH',
            'MAX_TASK_DESCRIPTION_LENGTH',
            'MIN_USERNAME_LENGTH',
            'MAX_USERNAME_LENGTH',
            'MIN_PASSWORD_LENGTH',
            'DEFAULT_PAGE_SIZE',
            'MAX_PAGE_SIZE',
            'MSG_SUCCESS',
            'MSG_CREATED',
            'MSG_UPDATED',
            'MSG_DELETED',
            'MSG_NOT_FOUND',
            'MSG_UNAUTHORIZED',
            'MSG_FORBIDDEN'
        ]
        
        for const_name in expected_constants:
            assert hasattr(constants, const_name), f"Missing constant: {const_name}"
            assert getattr(constants, const_name) is not None