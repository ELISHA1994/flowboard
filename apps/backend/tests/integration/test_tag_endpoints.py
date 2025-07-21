"""
Integration tests for tag endpoints
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Tag, User


@pytest.mark.integration
class TestTagEndpoints:
    """Test tag API endpoints"""

    def test_create_tag(
        self, test_client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test creating a new tag"""
        tag_data = {"name": "urgent", "color": "#FF0000"}

        response = test_client.post("/tags/", json=tag_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "urgent"
        assert data["color"] == "#FF0000"
        assert data["task_count"] == 0
        assert "id" in data
        assert "created_at" in data

    def test_create_tag_normalized_name(
        self, test_client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test tag name normalization"""
        tag_data = {
            "name": "  URGENT  ",  # Should be normalized to "urgent"
            "color": "#FF0000",
        }

        response = test_client.post("/tags/", json=tag_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "urgent"

    def test_create_bulk_tags(
        self, test_client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test creating multiple tags at once"""
        bulk_data = {"tag_names": ["bug", "feature", "todo"]}

        response = test_client.post("/tags/bulk", json=bulk_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        tag_names = [tag["name"] for tag in data]
        assert "bug" in tag_names
        assert "feature" in tag_names
        assert "todo" in tag_names

    def test_list_tags(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test listing user tags"""
        # Create test tags
        tags = [
            Tag(
                id=str(uuid.uuid4()), name="bug", color="#FF0000", user_id=test_user.id
            ),
            Tag(
                id=str(uuid.uuid4()),
                name="feature",
                color="#00FF00",
                user_id=test_user.id,
            ),
            Tag(
                id=str(uuid.uuid4()),
                name="urgent",
                color="#0000FF",
                user_id=test_user.id,
            ),
        ]
        for tag in tags:
            test_db.add(tag)
        test_db.commit()

        response = test_client.get("/tags/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Should be ordered by name
        assert [tag["name"] for tag in data] == ["bug", "feature", "urgent"]

    def test_get_popular_tags(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test getting popular tags"""
        # Create tags (in real scenario, these would have tasks associated)
        tags = [
            Tag(
                id=str(uuid.uuid4()),
                name="popular",
                color="#FF0000",
                user_id=test_user.id,
            ),
            Tag(
                id=str(uuid.uuid4()),
                name="common",
                color="#00FF00",
                user_id=test_user.id,
            ),
        ]
        for tag in tags:
            test_db.add(tag)
        test_db.commit()

        response = test_client.get("/tags/popular?limit=5", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Each item should have tag info and task count
        if data:  # If any tags have tasks
            assert "task_count" in data[0]
            assert "name" in data[0]

    def test_get_tag(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test getting a specific tag"""
        # Create test tag
        tag = Tag(
            id=str(uuid.uuid4()), name="bug", color="#FF0000", user_id=test_user.id
        )
        test_db.add(tag)
        test_db.commit()

        response = test_client.get(f"/tags/{tag.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tag.id
        assert data["name"] == "bug"
        assert data["color"] == "#FF0000"
        assert data["task_count"] == 0

    def test_update_tag(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test updating a tag"""
        # Create test tag
        tag = Tag(
            id=str(uuid.uuid4()), name="bug", color="#FF0000", user_id=test_user.id
        )
        test_db.add(tag)
        test_db.commit()

        update_data = {"name": "critical-bug", "color": "#FF00FF"}

        response = test_client.put(
            f"/tags/{tag.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "critical-bug"
        assert data["color"] == "#FF00FF"

    def test_delete_tag(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test deleting a tag (hard delete)"""
        # Create test tag
        tag = Tag(
            id=str(uuid.uuid4()),
            name="to-delete",
            color="#000000",
            user_id=test_user.id,
        )
        test_db.add(tag)
        test_db.commit()
        tag_id = tag.id

        response = test_client.delete(f"/tags/{tag_id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify tag is deleted
        deleted_tag = test_db.query(Tag).filter(Tag.id == tag_id).first()
        assert deleted_tag is None

    def test_tag_isolation(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test that users can only access their own tags"""
        # Create another user and their tag
        other_user = User(
            id=str(uuid.uuid4()),
            username="otheruser",
            email="other@example.com",
            hashed_password="hash",
        )
        test_db.add(other_user)

        other_tag = Tag(
            id=str(uuid.uuid4()),
            name="other-user-tag",
            color="#000000",
            user_id=other_user.id,
        )
        test_db.add(other_tag)
        test_db.commit()

        # Try to access other user's tag
        response = test_client.get(f"/tags/{other_tag.id}", headers=auth_headers)

        assert response.status_code == 404

    def test_tag_name_validation(
        self, test_client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test tag name validation"""
        # Invalid tag name with special characters
        tag_data = {"name": "invalid@tag!", "color": "#FF0000"}

        response = test_client.post("/tags/", json=tag_data, headers=auth_headers)

        assert response.status_code == 422
        assert "can only contain lowercase letters" in str(response.json())
