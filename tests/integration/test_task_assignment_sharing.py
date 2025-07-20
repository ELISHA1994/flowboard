"""
Integration tests for task assignment and sharing functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models import Task, User, Project, ProjectMember, ProjectRole, TaskShare
from datetime import datetime, timedelta, timezone


class TestTaskAssignment:
    """Test task assignment functionality"""
    
    def test_create_task_with_assignment(self, test_client: TestClient, test_user_token: str, second_user_token: str, test_db: Session):
        """Test creating a task and assigning it to another user"""
        # Get second user
        second_user_response = test_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {second_user_token}"}
        )
        second_user_id = second_user_response.json()["id"]
        
        # Create a task assigned to second user
        task_data = {
            "title": "Assigned Task",
            "description": "Task assigned to another user",
            "assigned_to_id": second_user_id
        }
        
        response = test_client.post(
            "/tasks/",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 201
        task = response.json()
        assert task["assigned_to_id"] == second_user_id
        assert task["assigned_to"]["id"] == second_user_id
        assert task["assigned_to"]["username"] == "testuser2"
    
    def test_update_task_assignment(self, test_client: TestClient, test_user_token: str, second_user_token: str, test_task: Task):
        """Test updating task assignment"""
        # Get second user
        second_user_response = test_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {second_user_token}"}
        )
        second_user_id = second_user_response.json()["id"]
        
        # Update task to assign to second user
        update_data = {
            "assigned_to_id": second_user_id
        }
        
        response = test_client.put(
            f"/tasks/{test_task.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        task = response.json()
        assert task["assigned_to_id"] == second_user_id
        assert task["assigned_to"]["id"] == second_user_id
    
    def test_filter_tasks_by_assigned_to(self, test_client: TestClient, test_user_token: str, second_user_token: str, test_db: Session):
        """Test filtering tasks by assigned user"""
        # Get second user
        second_user_response = test_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {second_user_token}"}
        )
        second_user_id = second_user_response.json()["id"]
        
        # Create tasks with different assignments
        tasks_data = [
            {"title": "Task 1", "assigned_to_id": second_user_id},
            {"title": "Task 2"},  # Not assigned
            {"title": "Task 3", "assigned_to_id": second_user_id}
        ]
        
        for task_data in tasks_data:
            test_client.post(
                "/tasks/",
                json=task_data,
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
        
        # Filter by assigned_to_id
        response = test_client.get(
            f"/tasks/?assigned_to_id={second_user_id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2
        assert all(task["assigned_to_id"] == second_user_id for task in tasks)
    
    @pytest.mark.skip(reason="Project member endpoints not implemented yet")
    def test_project_task_assignment_validation(self, test_client: TestClient, test_user_token: str, second_user_token: str, test_db: Session):
        """Test that assigned user must be project member for project tasks"""
        # Create a project
        project_data = {
            "name": "Test Project",
            "description": "Testing task assignment"
        }
        project_response = test_client.post(
            "/projects/",
            json=project_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        project_id = project_response.json()["id"]
        
        # Get second user ID
        second_user_response = test_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {second_user_token}"}
        )
        second_user_id = second_user_response.json()["id"]
        
        # Try to create task assigned to non-member
        task_data = {
            "title": "Project Task",
            "project_id": project_id,
            "assigned_to_id": second_user_id
        }
        
        response = test_client.post(
            "/tasks/",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 400
        error_detail = response.json()
        print(f"Error response: {error_detail}")  # Debug output
        assert "not a member of this project" in str(error_detail)
        
        # Add second user to project
        member_data = {
            "user_id": second_user_id,
            "role": "member"
        }
        test_client.post(
            f"/projects/{project_id}/members",
            json=member_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # Now task creation should succeed
        response = test_client.post(
            "/tasks/",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 201
        assert response.json()["assigned_to_id"] == second_user_id


class TestTaskSharing:
    """Test task sharing functionality"""
    
    def test_share_task_success(self, test_client: TestClient, test_user_token: str, second_user_token: str, test_task: Task):
        """Test sharing a task with another user"""
        # Get second user ID
        second_user_response = test_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {second_user_token}"}
        )
        second_user_id = second_user_response.json()["id"]
        
        # Share task
        share_data = {
            "task_id": test_task.id,
            "shared_with_id": second_user_id,
            "permission": "view"
        }
        
        response = test_client.post(
            f"/tasks/{test_task.id}/share",
            json=share_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        share = response.json()
        assert share["task_id"] == test_task.id
        assert share["shared_with_id"] == second_user_id
        assert share["permission"] == "view"
        assert share["task"]["id"] == test_task.id
        assert share["shared_with"]["id"] == second_user_id
    
    def test_update_existing_share(self, test_client: TestClient, test_user_token: str, second_user_token: str, test_task: Task):
        """Test updating an existing share"""
        # Get second user ID
        second_user_response = test_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {second_user_token}"}
        )
        second_user_id = second_user_response.json()["id"]
        
        # Share task with view permission
        share_data = {
            "task_id": test_task.id,
            "shared_with_id": second_user_id,
            "permission": "view"
        }
        
        response1 = test_client.post(
            f"/tasks/{test_task.id}/share",
            json=share_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        share1 = response1.json()
        
        # Update share to edit permission
        share_data["permission"] = "edit"
        
        response2 = test_client.post(
            f"/tasks/{test_task.id}/share",
            json=share_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        share2 = response2.json()
        
        # Should be same share ID, updated permission
        assert share2["id"] == share1["id"]
        assert share2["permission"] == "edit"
    
    def test_share_with_expiration(self, test_client: TestClient, test_user_token: str, second_user_token: str, test_task: Task):
        """Test sharing a task with expiration date"""
        # Get second user ID
        second_user_response = test_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {second_user_token}"}
        )
        second_user_id = second_user_response.json()["id"]
        
        # Share task with expiration
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        share_data = {
            "task_id": test_task.id,
            "shared_with_id": second_user_id,
            "permission": "view",
            "expires_at": expires_at.isoformat()
        }
        
        response = test_client.post(
            f"/tasks/{test_task.id}/share",
            json=share_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        share = response.json()
        assert share["expires_at"] is not None
    
    def test_get_tasks_shared_with_me(self, test_client: TestClient, test_user_token: str, second_user_token: str, test_db: Session):
        """Test getting tasks shared with current user"""
        # Get users
        first_user_response = test_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        first_user_id = first_user_response.json()["id"]
        
        # Create tasks as second user
        task_data = {"title": "Task to share"}
        task_response = test_client.post(
            "/tasks/",
            json=task_data,
            headers={"Authorization": f"Bearer {second_user_token}"}
        )
        task_id = task_response.json()["id"]
        
        # Share with first user
        share_data = {
            "task_id": task_id,
            "shared_with_id": first_user_id,
            "permission": "edit"
        }
        
        test_client.post(
            f"/tasks/{task_id}/share",
            json=share_data,
            headers={"Authorization": f"Bearer {second_user_token}"}
        )
        
        # Get shared tasks as first user
        response = test_client.get(
            "/tasks/shared/with-me",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        shares = response.json()
        assert len(shares) >= 1
        assert any(share["task_id"] == task_id for share in shares)
    
    def test_remove_task_share(self, test_client: TestClient, test_user_token: str, second_user_token: str, test_task: Task):
        """Test removing a task share"""
        # Get second user ID
        second_user_response = test_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {second_user_token}"}
        )
        second_user_id = second_user_response.json()["id"]
        
        # Share task
        share_data = {
            "task_id": test_task.id,
            "shared_with_id": second_user_id,
            "permission": "view"
        }
        
        share_response = test_client.post(
            f"/tasks/{test_task.id}/share",
            json=share_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        share_id = share_response.json()["id"]
        
        # Remove share
        response = test_client.delete(
            f"/tasks/{test_task.id}/share/{share_id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        assert "removed successfully" in response.json()["message"]
        
        # Verify share is removed
        shares = test_client.get(
            "/tasks/shared/with-me",
            headers={"Authorization": f"Bearer {second_user_token}"}
        )
        assert not any(share["id"] == share_id for share in shares.json())
    
    def test_share_permissions(self, test_client: TestClient, test_user_token: str, second_user_token: str, test_db: Session):
        """Test that only task owner or share creator can remove shares"""
        # Create third user
        third_user_data = {
            "username": "thirduser",
            "email": "third@example.com",
            "password": "testpass123"
        }
        test_client.post("/register", json=third_user_data)
        third_login = test_client.post(
            "/login",
            data={"username": "thirduser", "password": "testpass123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        third_user_token = third_login.json()["access_token"]
        
        # Get user IDs
        second_user_response = test_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {second_user_token}"}
        )
        second_user_id = second_user_response.json()["id"]
        
        # Create and share task
        task_data = {"title": "Shared task"}
        task_response = test_client.post(
            "/tasks/",
            json=task_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        task_id = task_response.json()["id"]
        
        share_data = {
            "task_id": task_id,
            "shared_with_id": second_user_id,
            "permission": "view"
        }
        
        share_response = test_client.post(
            f"/tasks/{task_id}/share",
            json=share_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        share_id = share_response.json()["id"]
        
        # Third user tries to remove share (should fail)
        response = test_client.delete(
            f"/tasks/{task_id}/share/{share_id}",
            headers={"Authorization": f"Bearer {third_user_token}"}
        )
        
        assert response.status_code == 403
        error_resp = response.json()
        assert "don't have permission" in error_resp.get("detail", "") or "don't have permission" in str(error_resp)