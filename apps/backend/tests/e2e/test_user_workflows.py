"""
End-to-end tests for complete user workflows.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models import User, Task
import uuid


@pytest.mark.e2e
class TestCompleteUserJourney:
    """Test complete user journey from registration to task management."""
    
    def test_new_user_complete_workflow(self, test_client: TestClient, test_db: Session):
        """Test complete workflow: register -> login -> create tasks -> manage tasks."""
        # Step 1: Register a new user
        user_data = {
            "username": "workflowuser",
            "email": "workflow@example.com",
            "password": "securepass123"
        }
        
        register_response = test_client.post("/register", json=user_data)
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]
        
        # Step 2: Login with the new user
        login_response = test_client.post(
            "/login",
            data={"username": user_data["username"], "password": user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Create authenticated headers
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Verify user profile
        profile_response = test_client.get("/users/me", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["username"] == user_data["username"]
        
        # Step 4: Create multiple tasks
        tasks_data = [
            {"title": "First task", "description": "Learn FastAPI", "status": "todo"},
            {"title": "Second task", "description": "Build API", "status": "in_progress"},
            {"title": "Third task", "description": "Deploy app", "status": "todo"}
        ]
        
        created_tasks = []
        for task_data in tasks_data:
            create_response = test_client.post("/tasks/", json=task_data, headers=headers)
            assert create_response.status_code == 201
            created_tasks.append(create_response.json())
        
        # Step 5: List all tasks
        list_response = test_client.get("/tasks/", headers=headers)
        assert list_response.status_code == 200
        tasks_list = list_response.json()
        assert len(tasks_list) == 3
        
        # Step 6: Update a task
        task_to_update = created_tasks[0]
        update_data = {"status": "in_progress", "description": "Learning FastAPI basics"}
        update_response = test_client.put(
            f"/tasks/{task_to_update['id']}", 
            json=update_data, 
            headers=headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "in_progress"
        
        # Step 7: Filter tasks by status
        in_progress_response = test_client.get("/tasks/?task_status=in_progress", headers=headers)
        assert in_progress_response.status_code == 200
        in_progress_tasks = in_progress_response.json()
        assert len(in_progress_tasks) == 2
        
        # Step 8: Complete a task
        complete_response = test_client.put(
            f"/tasks/{task_to_update['id']}", 
            json={"status": "done"}, 
            headers=headers
        )
        assert complete_response.status_code == 200
        
        # Step 9: Delete a task
        task_to_delete = created_tasks[2]
        delete_response = test_client.delete(f"/tasks/{task_to_delete['id']}", headers=headers)
        assert delete_response.status_code == 204
        
        # Step 10: Verify final state
        final_list_response = test_client.get("/tasks/", headers=headers)
        assert final_list_response.status_code == 200
        final_tasks = final_list_response.json()
        assert len(final_tasks) == 2
        
        # Verify in database
        db_user = test_db.query(User).filter(User.id == user_id).first()
        assert db_user is not None
        db_tasks = test_db.query(Task).filter(Task.user_id == user_id).all()
        assert len(db_tasks) == 2


@pytest.mark.e2e
class TestMultiUserWorkflow:
    """Test workflows involving multiple users."""
    
    def test_user_isolation_workflow(self, test_client: TestClient, test_db: Session):
        """Test that multiple users' data is properly isolated."""
        # Create two users
        users_data = [
            {"username": "alice", "email": "alice@example.com", "password": "alicepass123"},
            {"username": "bob", "email": "bob@example.com", "password": "bobpass123"}
        ]
        
        user_tokens = []
        for user_data in users_data:
            # Register
            register_response = test_client.post("/register", json=user_data)
            assert register_response.status_code == 201
            
            # Login
            login_response = test_client.post(
                "/login",
                data={"username": user_data["username"], "password": user_data["password"]},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            assert login_response.status_code == 200
            user_tokens.append(login_response.json()["access_token"])
        
        alice_headers = {"Authorization": f"Bearer {user_tokens[0]}"}
        bob_headers = {"Authorization": f"Bearer {user_tokens[1]}"}
        
        # Alice creates tasks
        alice_tasks = []
        for i in range(3):
            task_data = {"title": f"Alice's task {i+1}"}
            response = test_client.post("/tasks/", json=task_data, headers=alice_headers)
            assert response.status_code == 201
            alice_tasks.append(response.json())
        
        # Bob creates tasks
        bob_tasks = []
        for i in range(2):
            task_data = {"title": f"Bob's task {i+1}"}
            response = test_client.post("/tasks/", json=task_data, headers=bob_headers)
            assert response.status_code == 201
            bob_tasks.append(response.json())
        
        # Verify Alice only sees her tasks
        alice_list = test_client.get("/tasks/", headers=alice_headers)
        assert alice_list.status_code == 200
        alice_task_list = alice_list.json()
        assert len(alice_task_list) == 3
        assert all("Alice" in task["title"] for task in alice_task_list)
        
        # Verify Bob only sees his tasks
        bob_list = test_client.get("/tasks/", headers=bob_headers)
        assert bob_list.status_code == 200
        bob_task_list = bob_list.json()
        assert len(bob_task_list) == 2
        assert all("Bob" in task["title"] for task in bob_task_list)
        
        # Alice tries to access Bob's task - should fail
        bob_task_id = bob_tasks[0]["id"]
        response = test_client.get(f"/tasks/{bob_task_id}", headers=alice_headers)
        assert response.status_code == 403
        
        # Alice tries to update Bob's task - should fail
        response = test_client.put(
            f"/tasks/{bob_task_id}", 
            json={"title": "Hacked!"}, 
            headers=alice_headers
        )
        assert response.status_code == 403
        
        # Alice tries to delete Bob's task - should fail
        response = test_client.delete(f"/tasks/{bob_task_id}", headers=alice_headers)
        assert response.status_code == 403


@pytest.mark.e2e
class TestErrorHandlingWorkflow:
    """Test error handling and recovery workflows."""
    
    def test_authentication_expiry_workflow(self, test_client: TestClient):
        """Test handling of expired authentication tokens."""
        # Register and login
        user_data = {
            "username": "expirytest",
            "email": "expiry@example.com",
            "password": "testpass123"
        }
        
        register_response = test_client.post("/register", json=user_data)
        assert register_response.status_code == 201
        
        login_response = test_client.post(
            "/login",
            data={"username": user_data["username"], "password": user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Use valid token
        headers = {"Authorization": f"Bearer {token}"}
        profile_response = test_client.get("/users/me", headers=headers)
        assert profile_response.status_code == 200
        
        # Simulate expired token (use invalid token)
        expired_headers = {"Authorization": "Bearer invalid.expired.token"}
        expired_response = test_client.get("/users/me", headers=expired_headers)
        assert expired_response.status_code == 401
        
        # Re-authenticate
        new_login_response = test_client.post(
            "/login",
            data={"username": user_data["username"], "password": user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert new_login_response.status_code == 200
        new_token = new_login_response.json()["access_token"]
        
        # Use new token successfully
        new_headers = {"Authorization": f"Bearer {new_token}"}
        new_profile_response = test_client.get("/users/me", headers=new_headers)
        assert new_profile_response.status_code == 200
    
    def test_concurrent_updates_workflow(self, test_client: TestClient, test_user: User, test_user_token: str):
        """Test handling of concurrent updates to the same resource."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create a task
        task_data = {"title": "Concurrent test task", "status": "todo"}
        create_response = test_client.post("/tasks/", json=task_data, headers=headers)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]
        
        # Simulate concurrent updates
        update1 = {"title": "Update 1", "status": "in_progress"}
        update2 = {"title": "Update 2", "status": "done"}
        
        # Both updates should succeed (last write wins)
        response1 = test_client.put(f"/tasks/{task_id}", json=update1, headers=headers)
        assert response1.status_code == 200
        
        response2 = test_client.put(f"/tasks/{task_id}", json=update2, headers=headers)
        assert response2.status_code == 200
        
        # Verify final state
        get_response = test_client.get(f"/tasks/{task_id}", headers=headers)
        assert get_response.status_code == 200
        final_task = get_response.json()
        assert final_task["title"] == "Update 2"
        assert final_task["status"] == "done"


@pytest.mark.e2e
class TestPaginationWorkflow:
    """Test pagination workflows with large datasets."""
    
    def test_large_dataset_pagination(self, test_client: TestClient, test_user: User, test_user_token: str, test_db: Session):
        """Test pagination with a large number of tasks."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create 25 tasks
        for i in range(25):
            task_data = {
                "title": f"Task {i+1:02d}",
                "description": f"Description for task {i+1}",
                "status": ["todo", "in_progress", "done"][i % 3]
            }
            response = test_client.post("/tasks/", json=task_data, headers=headers)
            assert response.status_code == 201
        
        # Test default pagination (limit=10)
        page1 = test_client.get("/tasks/", headers=headers)
        assert page1.status_code == 200
        page1_data = page1.json()
        assert len(page1_data) == 10
        
        # Get second page
        page2 = test_client.get("/tasks/?skip=10", headers=headers)
        assert page2.status_code == 200
        page2_data = page2.json()
        assert len(page2_data) == 10
        
        # Get third page (partial)
        page3 = test_client.get("/tasks/?skip=20", headers=headers)
        assert page3.status_code == 200
        page3_data = page3.json()
        assert len(page3_data) == 5
        
        # Verify no duplicate tasks across pages
        all_task_ids = (
            [task["id"] for task in page1_data] +
            [task["id"] for task in page2_data] +
            [task["id"] for task in page3_data]
        )
        assert len(all_task_ids) == len(set(all_task_ids))  # All unique
        
        # Test custom page size
        large_page = test_client.get("/tasks/?limit=20", headers=headers)
        assert large_page.status_code == 200
        assert len(large_page.json()) == 20
        
        # Test filtering with pagination
        todo_tasks = test_client.get("/tasks/?task_status=todo&limit=5", headers=headers)
        assert todo_tasks.status_code == 200
        todo_data = todo_tasks.json()
        assert len(todo_data) <= 5
        assert all(task["status"] == "todo" for task in todo_data)