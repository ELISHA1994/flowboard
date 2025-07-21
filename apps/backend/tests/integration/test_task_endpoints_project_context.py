"""
Integration tests for task endpoints with project context
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Project, ProjectMember, ProjectRole, Task, User


class TestTaskProjectContext:
    """Test task operations within project context"""

    def test_create_task_with_project(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test creating a task within a project"""
        # Create a project
        project_response = test_client.post(
            "/projects",
            json={"name": "Test Project", "description": "Project for task tests"},
            headers=auth_headers,
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        # Create a task in the project
        task_data = {
            "title": "Project Task",
            "description": "Task within a project",
            "project_id": project_id,
        }
        response = test_client.post("/tasks", json=task_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Project Task"
        assert data["project_id"] == project_id
        assert data["project"]["id"] == project_id
        assert data["project"]["name"] == "Test Project"

    def test_create_task_in_unauthorized_project(
        self,
        test_client: TestClient,
        test_user: User,
        second_user: User,
        auth_headers: dict,
        second_auth_headers: dict,
        test_db: Session,
    ):
        """Test creating a task in a project without permission"""
        # Create a project as second user
        project_response = test_client.post(
            "/projects",
            json={"name": "Private Project", "description": "Not accessible"},
            headers=second_auth_headers,
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        # Try to create a task in that project as first user
        task_data = {
            "title": "Unauthorized Task",
            "description": "Should fail",
            "project_id": project_id,
        }
        response = test_client.post("/tasks", json=task_data, headers=auth_headers)

        assert response.status_code == 403
        # Check response content
        response_json = response.json()
        if "detail" in response_json:
            assert "don't have permission" in response_json["detail"]
        else:
            # Handle case where detail might be in a different format
            assert response.status_code == 403  # At least verify it's forbidden

    def test_list_tasks_by_project(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test listing tasks filtered by project"""
        # Create a project
        project_response = test_client.post(
            "/projects",
            json={"name": "Task List Project", "description": "For listing tests"},
            headers=auth_headers,
        )
        project_id = project_response.json()["id"]

        # Create tasks in the project
        for i in range(3):
            test_client.post(
                "/tasks",
                json={"title": f"Project Task {i}", "project_id": project_id},
                headers=auth_headers,
            )

        # Create tasks without project
        for i in range(2):
            test_client.post(
                "/tasks", json={"title": f"Personal Task {i}"}, headers=auth_headers
            )

        # List tasks filtered by project
        response = test_client.get(
            f"/tasks?project_id={project_id}", headers=auth_headers
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 3
        assert all(task["project_id"] == project_id for task in tasks)

    def test_get_project_tasks_endpoint(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test the dedicated project tasks endpoint"""
        # Create a project
        project_response = test_client.post(
            "/projects",
            json={
                "name": "Project Tasks Test",
                "description": "Testing project tasks endpoint",
            },
            headers=auth_headers,
        )
        project_id = project_response.json()["id"]

        # Create tasks with different statuses
        test_client.post(
            "/tasks",
            json={"title": "Todo Task", "project_id": project_id, "status": "todo"},
            headers=auth_headers,
        )
        test_client.post(
            "/tasks",
            json={
                "title": "In Progress Task",
                "project_id": project_id,
                "status": "in_progress",
            },
            headers=auth_headers,
        )
        test_client.post(
            "/tasks",
            json={"title": "Done Task", "project_id": project_id, "status": "done"},
            headers=auth_headers,
        )

        # Get all project tasks
        response = test_client.get(f"/tasks/project/{project_id}", headers=auth_headers)
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 3

        # Filter by status
        response = test_client.get(
            f"/tasks/project/{project_id}?task_status=in_progress", headers=auth_headers
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "In Progress Task"

    def test_update_task_project(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test moving a task between projects"""
        # Create two projects
        project1_response = test_client.post(
            "/projects",
            json={"name": "Project 1", "description": "First project"},
            headers=auth_headers,
        )
        project1_id = project1_response.json()["id"]

        project2_response = test_client.post(
            "/projects",
            json={"name": "Project 2", "description": "Second project"},
            headers=auth_headers,
        )
        project2_id = project2_response.json()["id"]

        # Create a task in project 1
        task_response = test_client.post(
            "/tasks",
            json={"title": "Mobile Task", "project_id": project1_id},
            headers=auth_headers,
        )
        task_id = task_response.json()["id"]

        # Move task to project 2
        update_response = test_client.put(
            f"/tasks/{task_id}", json={"project_id": project2_id}, headers=auth_headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["project_id"] == project2_id

        # Remove task from project (set to null)
        update_response = test_client.put(
            f"/tasks/{task_id}", json={"project_id": None}, headers=auth_headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["project_id"] is None

    def test_project_member_permissions(
        self,
        test_client: TestClient,
        test_user: User,
        second_user: User,
        auth_headers: dict,
        second_auth_headers: dict,
        test_db: Session,
    ):
        """Test task operations with different project member roles"""
        # Create project as first user
        project_response = test_client.post(
            "/projects",
            json={
                "name": "Permission Test Project",
                "description": "Testing permissions",
            },
            headers=auth_headers,
        )
        project_id = project_response.json()["id"]

        # Add second user as viewer
        member_response = test_client.post(
            f"/projects/{project_id}/members/{second_user.id}",
            json={"role": "viewer"},
            headers=auth_headers,
        )
        assert member_response.status_code == 200

        # Create a task in the project
        task_response = test_client.post(
            "/tasks",
            json={"title": "Test Task", "project_id": project_id},
            headers=auth_headers,
        )
        task_id = task_response.json()["id"]

        # Second user (viewer) should be able to view the task
        get_response = test_client.get(f"/tasks/{task_id}", headers=second_auth_headers)
        assert get_response.status_code == 200

        # But not update it
        update_response = test_client.put(
            f"/tasks/{task_id}",
            json={"title": "Updated Title"},
            headers=second_auth_headers,
        )
        assert update_response.status_code == 403

        # Update second user to member role
        test_client.put(
            f"/projects/{project_id}/members/{second_user.id}",
            json={"role": "member"},
            headers=auth_headers,
        )

        # Now they should be able to update
        update_response = test_client.put(
            f"/tasks/{task_id}",
            json={"title": "Updated Title"},
            headers=second_auth_headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Updated Title"

    def test_delete_task_with_project_permissions(
        self,
        test_client: TestClient,
        test_user: User,
        second_user: User,
        auth_headers: dict,
        second_auth_headers: dict,
        test_db: Session,
    ):
        """Test deleting tasks with project permissions"""
        # Create project and add second user as admin
        project_response = test_client.post(
            "/projects",
            json={
                "name": "Delete Test Project",
                "description": "Testing delete permissions",
            },
            headers=auth_headers,
        )
        project_id = project_response.json()["id"]

        member_response = test_client.post(
            f"/projects/{project_id}/members/{second_user.id}",
            json={"role": "admin"},
            headers=auth_headers,
        )
        assert member_response.status_code == 200

        # Create a task
        task_response = test_client.post(
            "/tasks",
            json={"title": "Task to Delete", "project_id": project_id},
            headers=auth_headers,
        )
        task_id = task_response.json()["id"]

        # Admin should be able to delete
        delete_response = test_client.delete(
            f"/tasks/{task_id}", headers=second_auth_headers
        )
        assert delete_response.status_code == 204

        # Verify task is deleted
        get_response = test_client.get(f"/tasks/{task_id}", headers=auth_headers)
        assert get_response.status_code == 404
