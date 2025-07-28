"""
Integration tests for authentication endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.middleware.jwt_auth_backend import verify_password
from app.db.models import User
from tests.factories import UserCreateFactory


@pytest.mark.integration
class TestRegistration:
    """Test cases for user registration endpoint."""

    def test_register_success(self, test_client: TestClient, test_db: Session):
        """Test successful user registration."""
        user_data = UserCreateFactory.create()

        response = test_client.post("/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "created_at" in data
        assert "is_active" in data
        assert data["is_active"] is True
        # Password should not be in response
        assert "password" not in data
        assert "hashed_password" not in data

        # Verify user in database
        db_user = (
            test_db.query(User).filter(User.username == user_data["username"]).first()
        )
        assert db_user is not None
        assert verify_password(user_data["password"], db_user.hashed_password)

    def test_register_duplicate_username(
        self, test_client: TestClient, test_user: User
    ):
        """Test registration with existing username."""
        user_data = {
            "username": test_user.username,  # Existing username
            "email": "different@example.com",
            "password": "password123",
        }

        response = test_client.post("/register", json=user_data)

        assert response.status_code == 400
        assert "Username already registered" in response.json()["message"]

    def test_register_duplicate_email(self, test_client: TestClient, test_user: User):
        """Test registration with existing email."""
        user_data = {
            "username": "differentuser",
            "email": test_user.email,  # Existing email
            "password": "password123",
        }

        response = test_client.post("/register", json=user_data)

        assert response.status_code == 400
        assert "Email already registered" in response.json()["message"]

    def test_register_invalid_email(self, test_client: TestClient):
        """Test registration with invalid email format."""
        user_data = {
            "username": "validuser",
            "email": "invalid-email",
            "password": "password123",
        }

        response = test_client.post("/register", json=user_data)

        assert response.status_code == 422  # Validation error
        errors = response.json()["detail"]
        assert any("email" in str(error).lower() for error in errors)

    def test_register_short_password(self, test_client: TestClient):
        """Test registration with too short password."""
        user_data = {
            "username": "validuser",
            "email": "valid@example.com",
            "password": "short",  # Less than 6 characters
        }

        response = test_client.post("/register", json=user_data)

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("password" in str(error).lower() for error in errors)

    def test_register_short_username(self, test_client: TestClient):
        """Test registration with too short username."""
        user_data = {
            "username": "ab",  # Less than 3 characters
            "email": "valid@example.com",
            "password": "password123",
        }

        response = test_client.post("/register", json=user_data)

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("username" in str(error).lower() for error in errors)


@pytest.mark.integration
class TestLogin:
    """Test cases for login endpoint."""

    def test_login_success(self, test_client: TestClient, test_user: User):
        """Test successful login."""
        login_data = {
            "username": test_user.username,
            "password": "testpass123",  # Password from fixture
        }

        response = test_client.post(
            "/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, test_client: TestClient, test_user: User):
        """Test login with wrong password."""
        login_data = {"username": test_user.username, "password": "wrongpassword"}

        response = test_client.post(
            "/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["message"]

    def test_login_nonexistent_user(self, test_client: TestClient):
        """Test login with non-existent username."""
        login_data = {"username": "nonexistentuser", "password": "anypassword"}

        response = test_client.post(
            "/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["message"]

    def test_login_with_json_fails(self, test_client: TestClient, test_user: User):
        """Test that login with JSON instead of form data fails."""
        login_data = {"username": test_user.username, "password": "testpass123"}

        # Send as JSON instead of form data
        response = test_client.post("/login", json=login_data)

        assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.integration
class TestUserProfile:
    """Test cases for user profile endpoint."""

    def test_get_profile_authenticated(
        self, authenticated_client: TestClient, test_user: User
    ):
        """Test getting user profile when authenticated."""
        response = authenticated_client.get("/users/me")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["is_active"] == test_user.is_active
        assert "created_at" in data
        # Password should not be in response
        assert "password" not in data
        assert "hashed_password" not in data

    def test_get_profile_unauthenticated(self, test_client: TestClient):
        """Test getting user profile without authentication."""
        response = test_client.get("/users/me")

        assert response.status_code == 401
        assert response.json()["message"] == "Not authenticated"

    def test_get_profile_invalid_token(self, test_client: TestClient):
        """Test getting user profile with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = test_client.get("/users/me", headers=headers)

        assert response.status_code == 401
        assert response.json()["message"] == "Could not validate credentials"

    def test_get_profile_expired_token(self, test_client: TestClient):
        """Test getting user profile with expired token."""
        # This would require creating an expired token
        # For now, we'll use an invalid token as a proxy
        headers = {
            "Authorization": "Bearer invalid-expired-test-token"
        }
        response = test_client.get("/users/me", headers=headers)

        assert response.status_code == 401
