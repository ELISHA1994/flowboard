"""
Pydantic models for calendar integration functionality.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CalendarProviderEnum(str, Enum):
    """Calendar provider options."""

    GOOGLE = "google"
    MICROSOFT = "microsoft"
    CALDAV = "caldav"


class SyncDirectionEnum(str, Enum):
    """Sync direction options."""

    TO_CALENDAR = "to_calendar"
    FROM_CALENDAR = "from_calendar"
    BOTH = "both"


class CalendarIntegrationCreate(BaseModel):
    """Model for creating a calendar integration."""

    provider: CalendarProviderEnum = Field(..., description="Calendar provider type")
    calendar_id: str = Field(
        ..., max_length=255, description="Calendar ID from provider"
    )
    calendar_name: str = Field(
        ..., max_length=255, description="Human-readable calendar name"
    )
    access_token: str = Field(..., description="OAuth access token")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token")
    token_expires_at: Optional[datetime] = Field(
        None, description="Token expiration time"
    )
    sync_direction: SyncDirectionEnum = Field(
        default=SyncDirectionEnum.BOTH, description="Sync direction"
    )


class CalendarIntegrationUpdate(BaseModel):
    """Model for updating a calendar integration."""

    sync_enabled: Optional[bool] = Field(None, description="Enable/disable sync")
    sync_direction: Optional[SyncDirectionEnum] = Field(
        None, description="Sync direction"
    )


class CalendarIntegrationResponse(BaseModel):
    """Model for calendar integration response."""

    id: str
    user_id: str
    provider: str
    calendar_id: str
    calendar_name: str
    sync_enabled: bool
    sync_direction: str
    last_sync_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalendarOAuthCallback(BaseModel):
    """Model for OAuth callback data."""

    provider: CalendarProviderEnum
    code: str = Field(..., description="OAuth authorization code")
    state: Optional[str] = Field(None, description="OAuth state parameter")


class CalendarOAuthTokenResponse(BaseModel):
    """Model for OAuth token response."""

    access_token: str
    refresh_token: Optional[str]
    expires_in: Optional[int]
    token_type: str = "Bearer"


class CalendarSyncRequest(BaseModel):
    """Model for manual sync request."""

    integration_id: Optional[str] = Field(
        None, description="Specific integration to sync"
    )
    task_ids: Optional[List[str]] = Field(None, description="Specific tasks to sync")


class CalendarSyncResponse(BaseModel):
    """Model for sync operation response."""

    synced: int = Field(..., description="Number of successfully synced items")
    failed: int = Field(..., description="Number of failed sync attempts")
    errors: List[str] = Field(default_factory=list, description="Error messages")


class TaskCalendarSyncResponse(BaseModel):
    """Model for task calendar sync mapping response."""

    id: str
    task_id: str
    calendar_integration_id: str
    calendar_event_id: str
    last_synced_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalendarEventCreate(BaseModel):
    """Model for creating a calendar event from a task."""

    task_id: str = Field(..., description="Task ID to sync")
    integration_id: str = Field(..., description="Calendar integration ID")


class CalendarEventUpdate(BaseModel):
    """Model for updating a calendar event."""

    task_id: str = Field(..., description="Task ID to update")
    integration_id: str = Field(..., description="Calendar integration ID")


class CalendarEventDelete(BaseModel):
    """Model for deleting a calendar event."""

    task_id: str = Field(..., description="Task ID to remove")
    integration_id: str = Field(..., description="Calendar integration ID")
