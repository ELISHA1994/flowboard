"""
Unit tests for User Pydantic models.
"""
import pytest
from pydantic import ValidationError
from app.models.user import UserBase, UserCreate, UserResponse, Token
from datetime import datetime, timezone
import uuid


@pytest.mark.unit
class TestUserBase:
    """Test cases for UserBase model validation."""
    
    def test_valid_user_base(self):
        """Test creating a valid user base."""
        data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        user = UserBase(**data)
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
    
    def test_username_too_short_fails(self):
        """Test that username less than 3 chars fails."""
        with pytest.raises(ValidationError) as exc_info:
            UserBase(username="ab", email="test@example.com")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "at least 3 characters" in str(errors[0])
    
    def test_username_too_long_fails(self):
        """Test that username more than 50 chars fails."""
        long_username = "x" * 51
        
        with pytest.raises(ValidationError) as exc_info:
            UserBase(username=long_username, email="test@example.com")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "at most 50 characters" in str(errors[0])
    
    def test_invalid_email_fails(self):
        """Test that invalid email format fails."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test @example.com"
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                UserBase(username="testuser", email=email)


@pytest.mark.unit
class TestUserCreate:
    """Test cases for UserCreate model validation."""
    
    def test_valid_user_create(self):
        """Test creating a valid user for registration."""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123"
        }
        user = UserCreate(**data)
        
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.password == "password123"
    
    def test_password_too_short_fails(self):
        """Test that password less than 6 chars fails."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="12345"
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "at least 6 characters" in str(errors[0])
    
    def test_user_create_inherits_base_validation(self):
        """Test that UserCreate inherits UserBase validations."""
        # Test username validation from base
        with pytest.raises(ValidationError):
            UserCreate(
                username="ab",  # Too short
                email="test@example.com",
                password="password123"
            )
        
        # Test email validation from base
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="invalid-email",
                password="password123"
            )


@pytest.mark.unit
class TestUserResponse:
    """Test cases for UserResponse model."""
    
    def test_valid_user_response(self):
        """Test creating a valid user response."""
        data = {
            "id": str(uuid.uuid4()),
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
        response = UserResponse(**data)
        
        assert response.id == data["id"]
        assert response.username == "testuser"
        assert response.email == "test@example.com"
        assert response.is_active is True
        assert isinstance(response.created_at, datetime)
    
    def test_user_response_inactive_user(self):
        """Test user response for inactive user."""
        data = {
            "id": str(uuid.uuid4()),
            "username": "inactiveuser",
            "email": "inactive@example.com",
            "is_active": False,
            "created_at": datetime.now(timezone.utc)
        }
        response = UserResponse(**data)
        
        assert response.is_active is False
    
    def test_user_response_from_orm(self):
        """Test that from_attributes config works."""
        assert UserResponse.model_config.get("from_attributes") is True
    
    def test_user_response_no_password(self):
        """Test that UserResponse doesn't include password field."""
        data = {
            "id": str(uuid.uuid4()),
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "password": "this_should_be_ignored"  # Extra field
        }
        response = UserResponse(**data)
        
        # Password field should not exist in response
        assert not hasattr(response, "password")
        assert not hasattr(response, "hashed_password")


@pytest.mark.unit
class TestToken:
    """Test cases for Token model."""
    
    def test_valid_token(self):
        """Test creating a valid token response."""
        data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }
        token = Token(**data)
        
        assert token.access_token == data["access_token"]
        assert token.token_type == "bearer"
    
    def test_token_missing_fields_fails(self):
        """Test that missing required fields fail."""
        # Missing access_token
        with pytest.raises(ValidationError):
            Token(token_type="bearer")
        
        # Missing token_type
        with pytest.raises(ValidationError):
            Token(access_token="some-token")