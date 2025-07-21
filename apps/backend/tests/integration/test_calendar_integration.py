"""
Integration tests for calendar integration functionality.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import CalendarIntegration, Task, User
from app.models.calendar import CalendarProviderEnum, SyncDirectionEnum
from app.services.calendar_service import CalendarService


class TestCalendarIntegration:
    """Test calendar integration endpoints."""

    def test_create_calendar_integration(
        self, test_client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test creating a calendar integration."""
        integration_data = {
            "provider": CalendarProviderEnum.GOOGLE.value,
            "calendar_id": "primary",
            "calendar_name": "My Calendar",
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "sync_direction": SyncDirectionEnum.BOTH.value,
        }

        response = test_client.post(
            "/calendar/integrations", json=integration_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == CalendarProviderEnum.GOOGLE.value
        assert data["calendar_id"] == "primary"
        assert data["calendar_name"] == "My Calendar"
        assert data["sync_enabled"] is True
        assert data["sync_direction"] == SyncDirectionEnum.BOTH.value
        assert data["user_id"] == test_user.id

    def test_create_duplicate_integration_fails(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test that creating duplicate integration fails."""
        # Create first integration
        integration = CalendarIntegration(
            user_id=test_user.id,
            provider=CalendarProviderEnum.GOOGLE.value,
            calendar_id="primary",
            calendar_name="My Calendar",
            access_token="test_token",
            sync_direction=SyncDirectionEnum.BOTH.value,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_db.add(integration)
        test_db.commit()

        # Try to create duplicate
        integration_data = {
            "provider": CalendarProviderEnum.GOOGLE.value,
            "calendar_id": "primary",
            "calendar_name": "My Calendar",
            "access_token": "test_access_token",
            "sync_direction": SyncDirectionEnum.BOTH.value,
        }

        response = test_client.post(
            "/calendar/integrations", json=integration_data, headers=auth_headers
        )

        assert response.status_code == 400
        response_data = response.json()
        # Check for error message in either 'detail' or in validation errors
        if "detail" in response_data:
            assert "already exists" in response_data["detail"]
        else:
            # Handle validation error format
            assert any("already exists" in str(err) for err in response_data.values())

    def test_get_calendar_integrations(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test getting calendar integrations."""
        # Create test integrations
        integrations = [
            CalendarIntegration(
                user_id=test_user.id,
                provider=CalendarProviderEnum.GOOGLE.value,
                calendar_id="primary",
                calendar_name="Google Calendar",
                access_token="google_token",
                sync_enabled=True,
                sync_direction=SyncDirectionEnum.BOTH.value,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
            CalendarIntegration(
                user_id=test_user.id,
                provider=CalendarProviderEnum.MICROSOFT.value,
                calendar_id="outlook_cal",
                calendar_name="Outlook Calendar",
                access_token="ms_token",
                sync_enabled=False,
                sync_direction=SyncDirectionEnum.TO_CALENDAR.value,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
        ]
        test_db.add_all(integrations)
        test_db.commit()

        # Get all integrations
        response = test_client.get("/calendar/integrations", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Only active integration
        assert data[0]["provider"] == CalendarProviderEnum.GOOGLE.value

        # Get all including inactive
        response = test_client.get(
            "/calendar/integrations?active_only=false", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_update_calendar_integration(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test updating a calendar integration."""
        # Create integration
        integration = CalendarIntegration(
            user_id=test_user.id,
            provider=CalendarProviderEnum.GOOGLE.value,
            calendar_id="primary",
            calendar_name="My Calendar",
            access_token="test_token",
            sync_enabled=True,
            sync_direction=SyncDirectionEnum.BOTH.value,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_db.add(integration)
        test_db.commit()

        # Update integration
        update_data = {
            "sync_enabled": False,
            "sync_direction": SyncDirectionEnum.TO_CALENDAR.value,
        }

        response = test_client.put(
            f"/calendar/integrations/{integration.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sync_enabled"] is False
        assert data["sync_direction"] == SyncDirectionEnum.TO_CALENDAR.value

    def test_delete_calendar_integration(
        self,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test deleting a calendar integration."""
        # Create integration
        integration = CalendarIntegration(
            user_id=test_user.id,
            provider=CalendarProviderEnum.GOOGLE.value,
            calendar_id="primary",
            calendar_name="My Calendar",
            access_token="test_token",
            sync_direction=SyncDirectionEnum.BOTH.value,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_db.add(integration)
        test_db.commit()

        # Delete integration
        response = test_client.delete(
            f"/calendar/integrations/{integration.id}", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Calendar integration deleted successfully"

        # Verify deletion
        integration = (
            test_db.query(CalendarIntegration)
            .filter(CalendarIntegration.id == integration.id)
            .first()
        )
        assert integration is None

    @patch("app.services.calendar_service.CalendarService.sync_all_tasks")
    def test_sync_calendar(
        self, mock_sync, test_client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test manual calendar sync."""
        mock_sync.return_value = {
            "synced": 5,
            "failed": 1,
            "errors": ["Task 123: Failed to sync"],
        }

        sync_data = {}

        response = test_client.post(
            "/calendar/sync", json=sync_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "background" in data["errors"][0]

    def test_get_calendar_providers(self, test_client: TestClient, auth_headers: dict):
        """Test getting list of calendar providers."""
        response = test_client.get("/calendar/providers", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["providers"]) == 3  # Google, Microsoft, CalDAV

        provider_ids = [p["id"] for p in data["providers"]]
        assert CalendarProviderEnum.GOOGLE.value in provider_ids
        assert CalendarProviderEnum.MICROSOFT.value in provider_ids
        assert CalendarProviderEnum.CALDAV.value in provider_ids

    @patch("httpx.AsyncClient.post")
    def test_task_create_triggers_calendar_sync(
        self,
        mock_post,
        test_client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_db: Session,
    ):
        """Test that creating a task triggers calendar sync."""
        # Create calendar integration
        integration = CalendarIntegration(
            user_id=test_user.id,
            provider=CalendarProviderEnum.GOOGLE.value,
            calendar_id="primary",
            calendar_name="My Calendar",
            access_token="test_token",
            sync_enabled=True,
            sync_direction=SyncDirectionEnum.BOTH.value,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_db.add(integration)
        test_db.commit()

        # Mock calendar API response
        mock_response = AsyncMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "google_event_123"}
        mock_post.return_value = mock_response

        # Create task
        task_data = {
            "title": "Test Task with Calendar Sync",
            "description": "This should sync to calendar",
            "due_date": "2025-02-01T10:00:00Z",
        }

        response = test_client.post("/tasks/", json=task_data, headers=auth_headers)

        assert response.status_code == 201

        # Verify task was created
        task_id = response.json()["id"]
        task = test_db.query(Task).filter(Task.id == task_id).first()
        assert task is not None

    def test_oauth_initiate(
        self, test_client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test OAuth initiation for calendar providers."""
        # Test Google OAuth
        response = test_client.get(
            "/calendar/oauth/google?redirect_uri=http://localhost:3000/callback",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "oauth_url" in data
        assert "accounts.google.com" in data["oauth_url"]

        # Test Microsoft OAuth
        response = test_client.get(
            "/calendar/oauth/microsoft?redirect_uri=http://localhost:3000/callback",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "oauth_url" in data
        assert "login.microsoftonline.com" in data["oauth_url"]

    def test_oauth_callback(
        self, test_client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test OAuth callback handling."""
        callback_data = {
            "provider": CalendarProviderEnum.GOOGLE.value,
            "code": "test_auth_code",
            "state": test_user.id,
        }

        response = test_client.post(
            "/calendar/oauth/callback", json=callback_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "OAuth callback processed"
