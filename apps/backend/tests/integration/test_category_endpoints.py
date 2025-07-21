"""
Integration tests for category endpoints
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Category, User


@pytest.mark.integration
class TestCategoryEndpoints:
    """Test category API endpoints"""

    def test_create_category(
        self, test_client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test creating a new category"""
        category_data = {
            "name": "Work",
            "description": "Work related tasks",
            "color": "#FF5733",
            "icon": "💼",
        }

        response = test_client.post(
            "/categories/", json=category_data, headers=auth_headers
        )

        if response.status_code != 201:
            print(f"Error response: {response.json()}")
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Work"
        assert data["description"] == "Work related tasks"
        assert data["color"] == "#FF5733"
        assert data["icon"] == "💼"
        assert data["is_active"] is True
        assert data["task_count"] == 0
        assert "id" in data
        assert "created_at" in data

    def test_create_category_duplicate_name(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test creating category with duplicate name"""
        # Create first category
        category = Category(id=str(uuid.uuid4()), name="Work", user_id=test_user.id)
        test_db.add(category)
        test_db.commit()

        # Try to create duplicate
        category_data = {"name": "Work"}
        response = test_client.post(
            "/categories/", json=category_data, headers=auth_headers
        )

        assert response.status_code == 400
        response_data = response.json()
        assert "already exists" in response_data.get(
            "detail", response_data.get("message", "")
        )

    def test_list_categories(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test listing user categories"""
        # Create test categories
        categories = [
            Category(
                id=str(uuid.uuid4()), name="Work", user_id=test_user.id, is_active=True
            ),
            Category(
                id=str(uuid.uuid4()),
                name="Personal",
                user_id=test_user.id,
                is_active=True,
            ),
            Category(
                id=str(uuid.uuid4()),
                name="Archive",
                user_id=test_user.id,
                is_active=False,
            ),
        ]
        for cat in categories:
            test_db.add(cat)
        test_db.commit()

        # Get active categories only
        response = test_client.get("/categories/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Only active categories
        assert all(cat["is_active"] for cat in data)

        # Get all categories including inactive
        response = test_client.get(
            "/categories/?include_inactive=true", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # All categories

    def test_get_category(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test getting a specific category"""
        # Create test category
        category = Category(
            id=str(uuid.uuid4()),
            name="Work",
            description="Work tasks",
            color="#FF5733",
            user_id=test_user.id,
        )
        test_db.add(category)
        test_db.commit()

        response = test_client.get(f"/categories/{category.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == category.id
        assert data["name"] == "Work"
        assert data["task_count"] == 0

    def test_update_category(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test updating a category"""
        # Create test category
        category = Category(
            id=str(uuid.uuid4()), name="Work", color="#000000", user_id=test_user.id
        )
        test_db.add(category)
        test_db.commit()

        update_data = {
            "name": "Work Projects",
            "description": "Updated description",
            "color": "#FF5733",
        }

        response = test_client.put(
            f"/categories/{category.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Work Projects"
        assert data["description"] == "Updated description"
        assert data["color"] == "#FF5733"

    def test_delete_category(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test deleting a category (soft delete)"""
        # Create test category
        category = Category(
            id=str(uuid.uuid4()), name="To Delete", user_id=test_user.id, is_active=True
        )
        test_db.add(category)
        test_db.commit()

        category_id = category.id
        response = test_client.delete(
            f"/categories/{category_id}", headers=auth_headers
        )

        assert response.status_code == 204

        # Verify category is soft deleted by querying it
        updated_category = test_db.query(Category).filter_by(id=category_id).first()
        assert updated_category is not None
        assert updated_category.is_active is False

    def test_category_isolation(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test that users can only access their own categories"""
        # Create another user and their category
        other_user = User(
            id=str(uuid.uuid4()),
            username="otheruser",
            email="other@example.com",
            hashed_password="hash",
        )
        test_db.add(other_user)

        other_category = Category(
            id=str(uuid.uuid4()), name="Other User Category", user_id=other_user.id
        )
        test_db.add(other_category)
        test_db.commit()

        # Try to access other user's category
        response = test_client.get(
            f"/categories/{other_category.id}", headers=auth_headers
        )

        assert response.status_code == 404
