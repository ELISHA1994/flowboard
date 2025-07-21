"""
Integration tests for comment endpoints with @mention support.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Comment, CommentMention, Task, User


class TestCommentCreate:
    """Test comment creation functionality"""

    def test_create_comment_success(
        self, test_client: TestClient, test_user_token: str, test_task: Task
    ):
        """Test creating a comment on a task"""
        comment_data = {"content": "This is a test comment on the task"}

        response = test_client.post(
            f"/tasks/{test_task.id}/comments",
            json=comment_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 201
        comment = response.json()
        assert comment["content"] == comment_data["content"]
        assert comment["task_id"] == test_task.id
        assert comment["parent_comment_id"] is None
        assert comment["is_edited"] is False
        assert comment["user"]["username"] == "testuser"
        assert comment["mentions"] == []
        assert comment["replies"] == []

    def test_create_comment_with_mention(
        self,
        test_client: TestClient,
        test_user_token: str,
        second_user_token: str,
        test_task: Task,
        test_db: Session,
    ):
        """Test creating a comment with @mentions"""
        # Get second user info
        second_user_response = test_client.get(
            "/users/me", headers={"Authorization": f"Bearer {second_user_token}"}
        )
        second_username = second_user_response.json()["username"]

        comment_data = {
            "content": f"Hey @{second_username}, check this out! Also @nonexistent"
        }

        response = test_client.post(
            f"/tasks/{test_task.id}/comments",
            json=comment_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 201
        comment = response.json()
        assert len(comment["mentions"]) == 1
        assert comment["mentions"][0]["username"] == second_username

    def test_create_reply_comment(
        self, test_client: TestClient, test_user_token: str, test_task: Task
    ):
        """Test creating a reply to a comment"""
        # Create parent comment
        parent_data = {"content": "Parent comment"}
        parent_response = test_client.post(
            f"/tasks/{test_task.id}/comments",
            json=parent_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        parent_id = parent_response.json()["id"]

        # Create reply
        reply_data = {"content": "This is a reply", "parent_comment_id": parent_id}

        response = test_client.post(
            f"/tasks/{test_task.id}/comments",
            json=reply_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 201
        reply = response.json()
        assert reply["parent_comment_id"] == parent_id
        assert reply["content"] == reply_data["content"]

    def test_create_comment_unauthorized(
        self, test_client: TestClient, test_task: Task
    ):
        """Test creating a comment without authentication"""
        comment_data = {"content": "Unauthorized comment"}

        response = test_client.post(
            f"/tasks/{test_task.id}/comments", json=comment_data
        )

        assert response.status_code == 401

    def test_create_comment_on_nonexistent_task(
        self, test_client: TestClient, test_user_token: str
    ):
        """Test creating a comment on a non-existent task"""
        comment_data = {"content": "Comment on nonexistent task"}

        response = test_client.post(
            "/tasks/nonexistent-task-id/comments",
            json=comment_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 404

    def test_create_comment_permission_denied(
        self, test_client: TestClient, second_user_token: str, test_task: Task
    ):
        """Test creating a comment on another user's task"""
        comment_data = {"content": "Comment on someone else's task"}

        response = test_client.post(
            f"/tasks/{test_task.id}/comments",
            json=comment_data,
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        assert response.status_code == 403


class TestCommentRead:
    """Test comment reading functionality"""

    def test_get_task_comments(
        self, test_client: TestClient, test_user_token: str, test_task: Task
    ):
        """Test getting all comments for a task"""
        # Create some comments
        comments_data = [
            {"content": "First comment"},
            {"content": "Second comment"},
            {"content": "Third comment"},
        ]

        for data in comments_data:
            test_client.post(
                f"/tasks/{test_task.id}/comments",
                json=data,
                headers={"Authorization": f"Bearer {test_user_token}"},
            )

        # Get comments
        response = test_client.get(
            f"/tasks/{test_task.id}/comments",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        comments = response.json()
        assert len(comments) == 3
        assert all(
            c["content"] in [d["content"] for d in comments_data] for c in comments
        )

    def test_get_comments_with_replies(
        self, test_client: TestClient, test_user_token: str, test_task: Task
    ):
        """Test getting comments with nested replies"""
        # Create parent comment
        parent_response = test_client.post(
            f"/tasks/{test_task.id}/comments",
            json={"content": "Parent comment"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        parent_id = parent_response.json()["id"]

        # Create replies
        for i in range(2):
            test_client.post(
                f"/tasks/{test_task.id}/comments",
                json={"content": f"Reply {i+1}", "parent_comment_id": parent_id},
                headers={"Authorization": f"Bearer {test_user_token}"},
            )

        # Get comments with replies
        response = test_client.get(
            f"/tasks/{test_task.id}/comments?include_replies=true",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        comments = response.json()
        assert len(comments) == 1  # Only top-level comment
        assert len(comments[0]["replies"]) == 2


class TestCommentUpdate:
    """Test comment update functionality"""

    def test_update_comment_success(
        self, test_client: TestClient, test_user_token: str, test_task: Task
    ):
        """Test updating a comment"""
        # Create comment
        create_response = test_client.post(
            f"/tasks/{test_task.id}/comments",
            json={"content": "Original content"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        comment_id = create_response.json()["id"]

        # Update comment
        update_data = {"content": "Updated content"}
        response = test_client.put(
            f"/comments/{comment_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        updated = response.json()
        assert updated["content"] == update_data["content"]
        assert updated["is_edited"] is True

    def test_update_comment_with_new_mentions(
        self,
        test_client: TestClient,
        test_user_token: str,
        second_user_token: str,
        test_task: Task,
    ):
        """Test updating a comment to add @mentions"""
        # Get second user info
        second_user_response = test_client.get(
            "/users/me", headers={"Authorization": f"Bearer {second_user_token}"}
        )
        second_username = second_user_response.json()["username"]

        # Create comment without mentions
        create_response = test_client.post(
            f"/tasks/{test_task.id}/comments",
            json={"content": "Original content"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        comment_id = create_response.json()["id"]

        # Update with mentions
        update_data = {"content": f"Updated content @{second_username}"}
        response = test_client.put(
            f"/comments/{comment_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        updated = response.json()
        assert len(updated["mentions"]) == 1
        assert updated["mentions"][0]["username"] == second_username

    def test_update_comment_permission_denied(
        self,
        test_client: TestClient,
        test_user_token: str,
        second_user_token: str,
        test_task: Task,
    ):
        """Test updating another user's comment"""
        # Create comment as first user
        create_response = test_client.post(
            f"/tasks/{test_task.id}/comments",
            json={"content": "Original content"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        comment_id = create_response.json()["id"]

        # Try to update as second user
        response = test_client.put(
            f"/comments/{comment_id}",
            json={"content": "Hacked content"},
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        assert response.status_code == 403


class TestCommentDelete:
    """Test comment deletion functionality"""

    def test_delete_comment_success(
        self, test_client: TestClient, test_user_token: str, test_task: Task
    ):
        """Test deleting a comment"""
        # Create comment
        create_response = test_client.post(
            f"/tasks/{test_task.id}/comments",
            json={"content": "Comment to delete"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        comment_id = create_response.json()["id"]

        # Delete comment
        response = test_client.delete(
            f"/comments/{comment_id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 204

    def test_delete_comment_permission_denied(
        self,
        test_client: TestClient,
        test_user_token: str,
        second_user_token: str,
        test_task: Task,
    ):
        """Test deleting another user's comment"""
        # Create comment as first user
        create_response = test_client.post(
            f"/tasks/{test_task.id}/comments",
            json={"content": "Comment to delete"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        comment_id = create_response.json()["id"]

        # Try to delete as second user
        response = test_client.delete(
            f"/comments/{comment_id}",
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        assert response.status_code == 403


class TestMentions:
    """Test @mention functionality"""

    def test_get_my_mentions(
        self,
        test_client: TestClient,
        test_user_token: str,
        second_user_token: str,
        test_db: Session,
    ):
        """Test getting mentions for current user"""
        # Get users info
        first_user_response = test_client.get(
            "/users/me", headers={"Authorization": f"Bearer {test_user_token}"}
        )
        first_username = first_user_response.json()["username"]
        first_user_id = first_user_response.json()["id"]

        # Create task as second user
        task_response = test_client.post(
            "/tasks/",
            json={"title": "Task for mentions"},
            headers={"Authorization": f"Bearer {second_user_token}"},
        )
        task_id = task_response.json()["id"]

        # Share task with first user so they can see the mentions
        test_client.post(
            f"/tasks/{task_id}/share",
            json={
                "task_id": task_id,
                "shared_with_id": first_user_id,
                "permission": "view",
            },
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        # Create comment mentioning first user
        test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": f"Hey @{first_username}, check this!"},
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        # Get mentions as first user
        response = test_client.get(
            "/users/me/mentions", headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        mentions = response.json()
        assert len(mentions) >= 1
        assert any(f"@{first_username}" in m["comment_content"] for m in mentions)

    def test_mentions_pagination(
        self,
        test_client: TestClient,
        test_user_token: str,
        second_user_token: str,
        test_db: Session,
    ):
        """Test pagination of mentions"""
        # Get first user info
        first_user_response = test_client.get(
            "/users/me", headers={"Authorization": f"Bearer {test_user_token}"}
        )
        first_username = first_user_response.json()["username"]
        first_user_id = first_user_response.json()["id"]

        # Create task as second user
        task_response = test_client.post(
            "/tasks/",
            json={"title": "Task for many mentions"},
            headers={"Authorization": f"Bearer {second_user_token}"},
        )
        task_id = task_response.json()["id"]

        # Share task with first user so they can see the mentions
        test_client.post(
            f"/tasks/{task_id}/share",
            json={
                "task_id": task_id,
                "shared_with_id": first_user_id,
                "permission": "view",
            },
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        # Create multiple comments with mentions
        for i in range(5):
            test_client.post(
                f"/tasks/{task_id}/comments",
                json={"content": f"Comment {i} @{first_username}"},
                headers={"Authorization": f"Bearer {second_user_token}"},
            )

        # Get mentions with pagination
        response = test_client.get(
            "/users/me/mentions?limit=3&offset=0",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        mentions = response.json()
        assert len(mentions) <= 3
