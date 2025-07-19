"""
Integration tests for authentication edge cases.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.models import User
from app.core.middleware.jwt_auth_backend import create_access_token, get_password_hash
from datetime import timedelta


@pytest.mark.integration
class TestAuthEdgeCases:
    """Test edge cases in authentication flow."""
    
    def test_token_valid_but_user_deleted(self, test_client: TestClient, test_db: Session):
        """Test case where token is valid but user has been deleted from database."""
        # Create a user
        user = User(
            id=9001,  # Set explicit ID to avoid autoincrement issues
            username="deleteduser",
            email="deleted@example.com",
            hashed_password=get_password_hash("password123")
        )
        test_db.add(user)
        test_db.commit()
        
        # Create a valid token
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=30)
        )
        
        # Delete the user from database
        test_db.delete(user)
        test_db.commit()
        
        # Try to access protected endpoint with valid token but deleted user
        response = test_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Should return 401 because user doesn't exist
        assert response.status_code == 401
        assert response.json()["message"] == "Could not validate credentials"
    
    def test_inactive_user_access(self, test_client: TestClient, test_db: Session):
        """Test case where user exists but is inactive."""
        # Create an inactive user
        user = User(
            id=9002,  # Set explicit ID to avoid autoincrement issues
            username="inactiveuser",
            email="inactive@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=False  # User is inactive
        )
        test_db.add(user)
        test_db.commit()
        
        # Create a valid token
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=30)
        )
        
        # Try to access an endpoint that requires active user
        # We need to use an endpoint that uses get_current_active_user
        # Let's check if tasks endpoint uses it
        response = test_client.get(
            "/tasks/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Should return 400 because user is inactive
        assert response.status_code == 400
        assert response.json()["message"] == "Inactive user"
    
    def test_token_with_nonexistent_username(self, test_client: TestClient, test_db: Session):
        """Test case where token contains username that never existed."""
        # Create a token with a username that doesn't exist
        access_token = create_access_token(
            data={"sub": "nonexistentuser"},
            expires_delta=timedelta(minutes=30)
        )
        
        # Try to access protected endpoint
        response = test_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Should return 401 because user doesn't exist
        assert response.status_code == 401
        assert response.json()["message"] == "Could not validate credentials"
    
    def test_user_deleted_between_requests(self, test_client: TestClient, test_db: Session):
        """Test case where user is deleted between login and subsequent request."""
        # Create a user
        user_data = {
            "username": "tempuser",
            "email": "temp@example.com",
            "password": "password123"
        }
        
        # Register the user
        response = test_client.post("/register", json=user_data)
        assert response.status_code == 201
        
        # Login to get token
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        response = test_client.post("/login", data=login_data)
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Verify user can access protected endpoint
        response = test_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Delete the user
        user = test_db.query(User).filter(User.username == user_data["username"]).first()
        test_db.delete(user)
        test_db.commit()
        
        # Try to access protected endpoint again
        response = test_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should now return 401
        assert response.status_code == 401
        assert response.json()["message"] == "Could not validate credentials"
    
    def test_user_deactivated_between_requests(self, test_client: TestClient, test_db: Session):
        """Test case where user is deactivated between login and subsequent request."""
        # Create an active user
        user_data = {
            "username": "activeuser",
            "email": "active@example.com",
            "password": "password123"
        }
        
        # Register the user
        response = test_client.post("/register", json=user_data)
        assert response.status_code == 201
        
        # Login to get token
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        response = test_client.post("/login", data=login_data)
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Verify user can access tasks
        response = test_client.get(
            "/tasks/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Deactivate the user
        user = test_db.query(User).filter(User.username == user_data["username"]).first()
        user.is_active = False
        test_db.commit()
        
        # Try to access tasks endpoint again
        response = test_client.get(
            "/tasks/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should now return 400 for inactive user
        assert response.status_code == 400
        assert response.json()["message"] == "Inactive user"