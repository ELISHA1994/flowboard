"""
Integration tests for task endpoints with categories and tags
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Category, Tag, Task, TaskPriority, TaskStatus, User


@pytest.mark.integration
class TestTaskCategoriesAndTags:
    """Test task endpoints with categories and tags functionality"""

    def test_create_task_with_categories_and_tags(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test creating a task with categories and tags"""
        # Create test category
        category = Category(id=str(uuid.uuid4()), name="Work", user_id=test_user.id)
        test_db.add(category)
        test_db.commit()

        task_data = {
            "title": "Task with categories and tags",
            "description": "Test task",
            "priority": "high",
            "category_ids": [category.id],
            "tag_names": ["urgent", "backend"],
        }

        response = test_client.post("/tasks/", json=task_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Task with categories and tags"
        assert len(data["categories"]) == 1
        assert data["categories"][0]["name"] == "Work"
        assert len(data["tags"]) == 2
        tag_names = [tag["name"] for tag in data["tags"]]
        assert "urgent" in tag_names
        assert "backend" in tag_names

    def test_update_task_categories(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test updating task categories"""
        # Create categories
        cat1 = Category(id=str(uuid.uuid4()), name="Work", user_id=test_user.id)
        cat2 = Category(id=str(uuid.uuid4()), name="Personal", user_id=test_user.id)
        test_db.add_all([cat1, cat2])

        # Create task with initial category
        task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            user_id=test_user.id,
            actual_hours=0.0,
            position=0,
        )
        task.categories.append(cat1)
        test_db.add(task)
        test_db.commit()

        # Update categories
        update_data = {"category_ids": [cat2.id]}  # Replace with Personal category

        response = test_client.put(
            f"/tasks/{task.id}/categories", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["categories"]) == 1
        assert data["categories"][0]["name"] == "Personal"

    def test_update_task_tags(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test updating task tags"""
        # Create task with initial tags
        task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            user_id=test_user.id,
            actual_hours=0.0,
            position=0,
        )

        initial_tag = Tag(
            id=str(uuid.uuid4()), name="old-tag", color="#000000", user_id=test_user.id
        )
        task.tags.append(initial_tag)
        test_db.add_all([task, initial_tag])
        test_db.commit()

        # Update tags
        update_data = {"tag_names": ["new-tag", "urgent"]}

        response = test_client.put(
            f"/tasks/{task.id}/tags", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 2
        tag_names = [tag["name"] for tag in data["tags"]]
        assert "new-tag" in tag_names
        assert "urgent" in tag_names
        assert "old-tag" not in tag_names

    def test_add_tags_to_task(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test adding tags to existing task tags"""
        # Create task with initial tag
        task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            user_id=test_user.id,
            actual_hours=0.0,
            position=0,
        )

        existing_tag = Tag(
            id=str(uuid.uuid4()), name="existing", color="#000000", user_id=test_user.id
        )
        task.tags.append(existing_tag)
        test_db.add_all([task, existing_tag])
        test_db.commit()

        # Add more tags
        add_data = {"tag_names": ["new-tag", "urgent"]}

        response = test_client.post(
            f"/tasks/{task.id}/tags", json=add_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 3  # Original + 2 new
        tag_names = [tag["name"] for tag in data["tags"]]
        assert "existing" in tag_names
        assert "new-tag" in tag_names
        assert "urgent" in tag_names

    def test_remove_tags_from_task(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test removing specific tags from a task"""
        # Create task with multiple tags
        task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            user_id=test_user.id,
            actual_hours=0.0,
            position=0,
        )

        tags = [
            Tag(
                id=str(uuid.uuid4()), name="keep", color="#000000", user_id=test_user.id
            ),
            Tag(
                id=str(uuid.uuid4()),
                name="remove1",
                color="#FF0000",
                user_id=test_user.id,
            ),
            Tag(
                id=str(uuid.uuid4()),
                name="remove2",
                color="#00FF00",
                user_id=test_user.id,
            ),
        ]
        task.tags.extend(tags)
        test_db.add(task)
        test_db.add_all(tags)
        test_db.commit()

        # Remove specific tags
        remove_data = {"tag_names": ["remove1", "remove2"]}

        response = test_client.request(
            "DELETE", f"/tasks/{task.id}/tags", json=remove_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == "keep"

    def test_filter_tasks_by_category(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test filtering tasks by category"""
        # Create categories
        work_cat = Category(id=str(uuid.uuid4()), name="Work", user_id=test_user.id)
        personal_cat = Category(
            id=str(uuid.uuid4()), name="Personal", user_id=test_user.id
        )
        test_db.add_all([work_cat, personal_cat])

        # Create tasks with different categories
        work_task = Task(
            id=str(uuid.uuid4()),
            title="Work Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            user_id=test_user.id,
            actual_hours=0.0,
            position=0,
        )
        work_task.categories.append(work_cat)

        personal_task = Task(
            id=str(uuid.uuid4()),
            title="Personal Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            user_id=test_user.id,
            actual_hours=0.0,
            position=1,
        )
        personal_task.categories.append(personal_cat)

        test_db.add_all([work_task, personal_task])
        test_db.commit()

        # Filter by work category
        response = test_client.get(
            f"/tasks/?category_id={work_cat.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Work Task"

    def test_filter_tasks_by_tag(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test filtering tasks by tag"""
        # Create tags
        urgent_tag = Tag(
            id=str(uuid.uuid4()), name="urgent", color="#FF0000", user_id=test_user.id
        )
        backend_tag = Tag(
            id=str(uuid.uuid4()), name="backend", color="#00FF00", user_id=test_user.id
        )
        test_db.add_all([urgent_tag, backend_tag])

        # Create tasks with different tags
        urgent_task = Task(
            id=str(uuid.uuid4()),
            title="Urgent Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            user_id=test_user.id,
            actual_hours=0.0,
            position=0,
        )
        urgent_task.tags.append(urgent_tag)

        backend_task = Task(
            id=str(uuid.uuid4()),
            title="Backend Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            user_id=test_user.id,
            actual_hours=0.0,
            position=1,
        )
        backend_task.tags.append(backend_tag)

        test_db.add_all([urgent_task, backend_task])
        test_db.commit()

        # Filter by urgent tag
        response = test_client.get("/tasks/?tag_name=urgent", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Urgent Task"

    def test_task_response_includes_categories_and_tags(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test that task responses always include categories and tags"""
        # Create task with category and tag
        category = Category(
            id=str(uuid.uuid4()), name="Work", color="#FF5733", user_id=test_user.id
        )
        tag = Tag(
            id=str(uuid.uuid4()), name="urgent", color="#FF0000", user_id=test_user.id
        )
        test_db.add_all([category, tag])

        task = Task(
            id=str(uuid.uuid4()),
            title="Complete Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            user_id=test_user.id,
            actual_hours=0.0,
            position=0,
        )
        task.categories.append(category)
        task.tags.append(tag)
        test_db.add(task)
        test_db.commit()

        # Get single task
        response = test_client.get(f"/tasks/{task.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "tags" in data
        assert data["categories"][0]["color"] == "#FF5733"
        assert data["tags"][0]["color"] == "#FF0000"

        # Get task list
        response = test_client.get("/tasks/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all("categories" in task for task in data)
        assert all("tags" in task for task in data)
