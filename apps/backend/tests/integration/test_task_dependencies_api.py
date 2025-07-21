"""
Integration tests for task dependencies API endpoints
"""

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Task, TaskDependency, TaskPriority, TaskStatus, User
from tests.factories import TaskCreateFactory


@pytest.mark.integration
class TestTaskDependenciesAPI:
    """Test task dependencies API endpoints"""

    # auth_headers fixture is already provided by conftest.py

    @pytest.fixture
    def parent_task(self, test_db: Session, test_user: User):
        """Create a parent task"""
        task = Task(
            id=str(uuid.uuid4()),
            title="Parent Task",
            description="This is a parent task",
            user_id=test_user.id,
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
        )
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        return task

    @pytest.fixture
    def child_tasks(self, test_db: Session, test_user: User, parent_task: Task):
        """Create child tasks"""
        tasks = []
        for i in range(3):
            task = Task(
                id=str(uuid.uuid4()),
                title=f"Child Task {i+1}",
                description=f"This is child task {i+1}",
                user_id=test_user.id,
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                parent_task_id=parent_task.id,
            )
            test_db.add(task)
            tasks.append(task)
        test_db.commit()
        for task in tasks:
            test_db.refresh(task)
        return tasks

    @pytest.fixture
    def independent_tasks(self, test_db: Session, test_user: User):
        """Create independent tasks for dependency testing"""
        tasks = []
        for i in range(4):
            task = Task(
                id=str(uuid.uuid4()),
                title=f"Task {chr(65+i)}",  # Task A, B, C, D
                description=f"This is task {chr(65+i)}",
                user_id=test_user.id,
                status=TaskStatus.TODO if i < 3 else TaskStatus.DONE,
                priority=TaskPriority.MEDIUM,
            )
            test_db.add(task)
            tasks.append(task)
        test_db.commit()
        for task in tasks:
            test_db.refresh(task)
        return tasks

    def test_create_task_with_parent(
        self, test_client: TestClient, auth_headers: dict, parent_task: Task
    ):
        """Test creating a task with a parent"""
        task_data = {
            "title": "New Subtask",
            "description": "This is a subtask",
            "priority": "medium",
            "parent_task_id": parent_task.id,
        }

        response = test_client.post("/tasks", json=task_data, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["parent_task_id"] == parent_task.id

    def test_update_task_parent(
        self,
        test_client: TestClient,
        auth_headers: dict,
        parent_task: Task,
        child_tasks: list,
    ):
        """Test updating a task's parent"""
        child_task = child_tasks[0]
        new_parent = child_tasks[1]

        # Update child to have a different parent
        update_data = {"parent_task_id": new_parent.id}
        response = test_client.put(
            f"/tasks/{child_task.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["parent_task_id"] == new_parent.id

    def test_remove_task_parent(
        self, test_client: TestClient, auth_headers: dict, child_tasks: list
    ):
        """Test removing a task's parent"""
        child_task = child_tasks[0]

        # Remove parent by setting to null
        update_data = {"parent_task_id": None}
        response = test_client.put(
            f"/tasks/{child_task.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["parent_task_id"] is None

    def test_prevent_self_parent(
        self, test_client: TestClient, auth_headers: dict, parent_task: Task
    ):
        """Test that a task cannot be its own parent"""
        update_data = {"parent_task_id": parent_task.id}
        response = test_client.put(
            f"/tasks/{parent_task.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 400
        assert "cannot be its own parent" in response.json()["message"]

    def test_prevent_circular_parent_hierarchy(
        self,
        test_client: TestClient,
        auth_headers: dict,
        parent_task: Task,
        child_tasks: list,
    ):
        """Test that circular parent hierarchies are prevented"""
        # Current hierarchy: parent_task -> child_tasks[0]
        # Try to make parent_task a child of child_tasks[0]
        update_data = {"parent_task_id": child_tasks[0].id}
        response = test_client.put(
            f"/tasks/{parent_task.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 400
        assert "circular task hierarchy" in response.json()["message"]

    def test_create_task_dependency(
        self, test_client: TestClient, auth_headers: dict, independent_tasks: list
    ):
        """Test creating a task dependency"""
        task_a, task_b = independent_tasks[0], independent_tasks[1]

        # Make task_a depend on task_b
        response = test_client.post(
            f"/tasks/{task_a.id}/dependencies",
            params={"depends_on_id": task_b.id},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_a.id
        assert data["depends_on_id"] == task_b.id

    def test_prevent_self_dependency(
        self, test_client: TestClient, auth_headers: dict, independent_tasks: list
    ):
        """Test that a task cannot depend on itself"""
        task_a = independent_tasks[0]

        response = test_client.post(
            f"/tasks/{task_a.id}/dependencies",
            params={"depends_on_id": task_a.id},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "cannot depend on itself" in response.json()["message"]

    def test_prevent_duplicate_dependency(
        self,
        test_client: TestClient,
        auth_headers: dict,
        independent_tasks: list,
        test_db: Session,
    ):
        """Test that duplicate dependencies are prevented"""
        task_a, task_b = independent_tasks[0], independent_tasks[1]

        # Create initial dependency
        dep = TaskDependency(
            id=str(uuid.uuid4()), task_id=task_a.id, depends_on_id=task_b.id
        )
        test_db.add(dep)
        test_db.commit()

        # Try to create duplicate
        response = test_client.post(
            f"/tasks/{task_a.id}/dependencies",
            params={"depends_on_id": task_b.id},
            headers=auth_headers,
        )

        assert (
            response.status_code == 400
        )  # ConflictException is mapped to 400 in our error handler
        assert "already exists" in response.json()["message"]

    def test_prevent_circular_dependency(
        self,
        test_client: TestClient,
        auth_headers: dict,
        independent_tasks: list,
        test_db: Session,
    ):
        """Test that circular dependencies are prevented"""
        task_a, task_b, task_c = (
            independent_tasks[0],
            independent_tasks[1],
            independent_tasks[2],
        )

        # Create chain: A -> B -> C
        dep1 = TaskDependency(
            id=str(uuid.uuid4()), task_id=task_a.id, depends_on_id=task_b.id
        )
        dep2 = TaskDependency(
            id=str(uuid.uuid4()), task_id=task_b.id, depends_on_id=task_c.id
        )
        test_db.add_all([dep1, dep2])
        test_db.commit()

        # Try to create C -> A (would create cycle)
        response = test_client.post(
            f"/tasks/{task_c.id}/dependencies",
            params={"depends_on_id": task_a.id},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "circular reference" in response.json()["message"]

    def test_get_task_dependencies(
        self,
        test_client: TestClient,
        auth_headers: dict,
        independent_tasks: list,
        test_db: Session,
    ):
        """Test getting task dependencies"""
        task_a, task_b, task_c = (
            independent_tasks[0],
            independent_tasks[1],
            independent_tasks[2],
        )

        # Create dependencies: A depends on B and C
        dep1 = TaskDependency(
            id=str(uuid.uuid4()), task_id=task_a.id, depends_on_id=task_b.id
        )
        dep2 = TaskDependency(
            id=str(uuid.uuid4()), task_id=task_a.id, depends_on_id=task_c.id
        )
        test_db.add_all([dep1, dep2])
        test_db.commit()

        response = test_client.get(
            f"/tasks/{task_a.id}/dependencies", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        depends_on_ids = [dep["depends_on_id"] for dep in data]
        assert task_b.id in depends_on_ids
        assert task_c.id in depends_on_ids

    def test_delete_task_dependency(
        self,
        test_client: TestClient,
        auth_headers: dict,
        independent_tasks: list,
        test_db: Session,
    ):
        """Test deleting a task dependency"""
        task_a, task_b = independent_tasks[0], independent_tasks[1]

        # Create dependency
        dep = TaskDependency(
            id=str(uuid.uuid4()), task_id=task_a.id, depends_on_id=task_b.id
        )
        test_db.add(dep)
        test_db.commit()

        # Delete dependency
        response = test_client.delete(
            f"/tasks/{task_a.id}/dependencies/{dep.id}", headers=auth_headers
        )

        assert response.status_code == 204

        # Verify deletion
        deleted_dep = test_db.query(TaskDependency).filter_by(id=dep.id).first()
        assert deleted_dep is None

    def test_check_task_completion_readiness(
        self,
        test_client: TestClient,
        auth_headers: dict,
        independent_tasks: list,
        test_db: Session,
    ):
        """Test checking if a task can be completed based on dependencies"""
        task_a, task_b, task_c, task_d = independent_tasks
        # task_d is already DONE, others are TODO

        # A depends on B (incomplete) and D (complete)
        dep1 = TaskDependency(
            id=str(uuid.uuid4()), task_id=task_a.id, depends_on_id=task_b.id
        )
        dep2 = TaskDependency(
            id=str(uuid.uuid4()), task_id=task_a.id, depends_on_id=task_d.id
        )
        test_db.add_all([dep1, dep2])
        test_db.commit()

        response = test_client.get(
            f"/tasks/{task_a.id}/can-complete", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["can_complete"] is False
        assert len(data["incomplete_dependencies"]) == 1
        assert task_b.id in data["incomplete_dependencies"]

    def test_get_task_subtasks(
        self,
        test_client: TestClient,
        auth_headers: dict,
        parent_task: Task,
        child_tasks: list,
    ):
        """Test getting subtasks of a parent task"""
        response = test_client.get(
            f"/tasks/{parent_task.id}/subtasks", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(child_tasks)

        subtask_ids = [task["id"] for task in data]
        for child in child_tasks:
            assert child.id in subtask_ids

    def test_parent_task_status_update(
        self,
        test_client: TestClient,
        auth_headers: dict,
        parent_task: Task,
        child_tasks: list,
        test_db: Session,
    ):
        """Test that parent task status updates when subtasks change"""
        # Mark all subtasks as done
        for child in child_tasks:
            response = test_client.put(
                f"/tasks/{child.id}", json={"status": "done"}, headers=auth_headers
            )
            assert response.status_code == 200

        # Check parent status
        parent_response = test_client.get(
            f"/tasks/{parent_task.id}", headers=auth_headers
        )
        assert parent_response.status_code == 200
        parent_data = parent_response.json()
        assert parent_data["status"] == "done"

    def test_create_task_with_dependencies(
        self, test_client: TestClient, auth_headers: dict, independent_tasks: list
    ):
        """Test creating a task with initial dependencies"""
        task_b, task_c = independent_tasks[1], independent_tasks[2]

        task_data = {
            "title": "New Task with Dependencies",
            "description": "This task depends on others",
            "priority": "high",
            "depends_on_ids": [task_b.id, task_c.id],
        }

        response = test_client.post("/tasks", json=task_data, headers=auth_headers)
        assert response.status_code == 201

        new_task_id = response.json()["id"]

        # Verify dependencies were created
        deps_response = test_client.get(
            f"/tasks/{new_task_id}/dependencies", headers=auth_headers
        )
        assert deps_response.status_code == 200
        deps = deps_response.json()
        assert len(deps) == 2

        depends_on_ids = [dep["depends_on_id"] for dep in deps]
        assert task_b.id in depends_on_ids
        assert task_c.id in depends_on_ids

    def test_update_task_dependencies(
        self, test_client: TestClient, auth_headers: dict, independent_tasks: list
    ):
        """Test updating task dependencies via task update endpoint"""
        task_a, task_b, task_c, task_d = independent_tasks

        # Update task to set dependencies
        update_data = {"depends_on_ids": [task_c.id, task_d.id]}

        response = test_client.put(
            f"/tasks/{task_a.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200

        # Verify dependencies
        deps_response = test_client.get(
            f"/tasks/{task_a.id}/dependencies", headers=auth_headers
        )
        assert deps_response.status_code == 200
        deps = deps_response.json()
        assert len(deps) == 2

        depends_on_ids = [dep["depends_on_id"] for dep in deps]
        assert task_c.id in depends_on_ids
        assert task_d.id in depends_on_ids

    def test_task_not_found_errors(self, test_client: TestClient, auth_headers: dict):
        """Test proper error handling for non-existent tasks"""
        fake_id = str(uuid.uuid4())
        fake_id2 = str(uuid.uuid4())  # Different ID to avoid self-reference error

        # Try to create dependency for non-existent task
        response = test_client.post(
            f"/tasks/{fake_id}/dependencies",
            params={"depends_on_id": fake_id2},
            headers=auth_headers,
        )
        assert response.status_code == 400  # NotFoundException is mapped to 400
        assert "not found" in response.json()["message"]

        # Try to get dependencies for non-existent task
        response = test_client.get(
            f"/tasks/{fake_id}/dependencies", headers=auth_headers
        )
        assert response.status_code == 404  # GET endpoints return standard 404

        # Try to get subtasks for non-existent task
        response = test_client.get(f"/tasks/{fake_id}/subtasks", headers=auth_headers)
        assert response.status_code == 404  # GET endpoints return standard 404

    def test_unauthorized_access(
        self, test_client: TestClient, independent_tasks: list
    ):
        """Test that unauthenticated requests are rejected"""
        task_a = independent_tasks[0]

        # Try without auth headers
        response = test_client.post(
            f"/tasks/{task_a.id}/dependencies", params={"depends_on_id": task_a.id}
        )
        assert response.status_code == 401

        response = test_client.get(f"/tasks/{task_a.id}/dependencies")
        assert response.status_code == 401

        response = test_client.get(f"/tasks/{task_a.id}/subtasks")
        assert response.status_code == 401
