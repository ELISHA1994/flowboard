"""
Calendar integration service for syncing tasks with external calendars.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.models import CalendarIntegration, Task, TaskCalendarSync


class CalendarProvider(str, Enum):
    """Supported calendar providers."""

    GOOGLE = "google"
    MICROSOFT = "microsoft"
    CALDAV = "caldav"


class SyncDirection(str, Enum):
    """Calendar sync direction options."""

    TO_CALENDAR = "to_calendar"
    FROM_CALENDAR = "from_calendar"
    BOTH = "both"


class CalendarService:
    """Service for managing calendar integrations."""

    @staticmethod
    def create_integration(
        db: Session,
        user_id: str,
        provider: str,
        calendar_id: str,
        calendar_name: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None,
        sync_direction: str = "both",
    ) -> CalendarIntegration:
        """Create a new calendar integration."""
        if provider not in [p.value for p in CalendarProvider]:
            raise ValueError(f"Invalid provider: {provider}")

        if sync_direction not in [d.value for d in SyncDirection]:
            raise ValueError(f"Invalid sync direction: {sync_direction}")

        # Check if integration already exists
        existing = (
            db.query(CalendarIntegration)
            .filter(
                CalendarIntegration.user_id == user_id,
                CalendarIntegration.provider == provider,
                CalendarIntegration.calendar_id == calendar_id,
            )
            .first()
        )

        if existing:
            raise ValueError("Calendar integration already exists")

        integration = CalendarIntegration(
            user_id=user_id,
            provider=provider,
            calendar_id=calendar_id,
            calendar_name=calendar_name,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            sync_direction=sync_direction,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.add(integration)
        db.commit()
        db.refresh(integration)

        logger.info(f"Created calendar integration {integration.id} for user {user_id}")
        return integration

    @staticmethod
    def get_user_integrations(
        db: Session,
        user_id: str,
        provider: Optional[str] = None,
        active_only: bool = True,
    ) -> List[CalendarIntegration]:
        """Get all calendar integrations for a user."""
        query = db.query(CalendarIntegration).filter(
            CalendarIntegration.user_id == user_id
        )

        if provider:
            query = query.filter(CalendarIntegration.provider == provider)

        if active_only:
            query = query.filter(CalendarIntegration.sync_enabled == True)

        return query.all()

    @staticmethod
    def update_integration(
        db: Session,
        integration_id: str,
        user_id: str,
        sync_enabled: Optional[bool] = None,
        sync_direction: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None,
    ) -> Optional[CalendarIntegration]:
        """Update a calendar integration."""
        integration = (
            db.query(CalendarIntegration)
            .filter(
                CalendarIntegration.id == integration_id,
                CalendarIntegration.user_id == user_id,
            )
            .first()
        )

        if not integration:
            return None

        if sync_enabled is not None:
            integration.sync_enabled = sync_enabled

        if sync_direction is not None:
            if sync_direction not in [d.value for d in SyncDirection]:
                raise ValueError(f"Invalid sync direction: {sync_direction}")
            integration.sync_direction = sync_direction

        if access_token is not None:
            integration.access_token = access_token

        if refresh_token is not None:
            integration.refresh_token = refresh_token

        if token_expires_at is not None:
            integration.token_expires_at = token_expires_at

        integration.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(integration)

        return integration

    @staticmethod
    def delete_integration(db: Session, integration_id: str, user_id: str) -> bool:
        """Delete a calendar integration."""
        integration = (
            db.query(CalendarIntegration)
            .filter(
                CalendarIntegration.id == integration_id,
                CalendarIntegration.user_id == user_id,
            )
            .first()
        )

        if not integration:
            return False

        # Delete all sync mappings
        db.query(TaskCalendarSync).filter(
            TaskCalendarSync.calendar_integration_id == integration_id
        ).delete()

        db.delete(integration)
        db.commit()

        logger.info(f"Deleted calendar integration {integration_id}")
        return True

    @staticmethod
    def sync_task_to_calendar(
        db: Session,
        task: Task,
        integration: CalendarIntegration,
        event_id: Optional[str] = None,
    ) -> TaskCalendarSync:
        """Sync a task to a calendar."""
        # Check if sync already exists
        existing_sync = (
            db.query(TaskCalendarSync)
            .filter(
                TaskCalendarSync.task_id == task.id,
                TaskCalendarSync.calendar_integration_id == integration.id,
            )
            .first()
        )

        if existing_sync:
            # Update existing sync
            existing_sync.last_synced_at = datetime.now(timezone.utc)
            if event_id:
                existing_sync.calendar_event_id = event_id
            db.commit()
            return existing_sync

        # Create new sync
        sync = TaskCalendarSync(
            task_id=task.id,
            calendar_integration_id=integration.id,
            calendar_event_id=event_id or f"task-{task.id}",
            last_synced_at=datetime.now(timezone.utc),
        )

        db.add(sync)
        db.commit()
        db.refresh(sync)

        return sync

    @staticmethod
    def get_task_syncs(db: Session, task_id: str) -> List[TaskCalendarSync]:
        """Get all calendar syncs for a task."""
        return (
            db.query(TaskCalendarSync).filter(TaskCalendarSync.task_id == task_id).all()
        )

    @staticmethod
    def remove_task_sync(db: Session, task_id: str, integration_id: str) -> bool:
        """Remove a task calendar sync."""
        sync = (
            db.query(TaskCalendarSync)
            .filter(
                TaskCalendarSync.task_id == task_id,
                TaskCalendarSync.calendar_integration_id == integration_id,
            )
            .first()
        )

        if not sync:
            return False

        db.delete(sync)
        db.commit()

        return True

    @staticmethod
    async def sync_with_google_calendar(
        integration: CalendarIntegration, task: Task, action: str = "create"
    ) -> Optional[str]:
        """Sync a task with Google Calendar."""
        # This is a placeholder for actual Google Calendar API integration
        # In production, you would use the Google Calendar API client

        headers = {
            "Authorization": f"Bearer {integration.access_token}",
            "Content-Type": "application/json",
        }

        # Convert task to Google Calendar event format
        event_data = {
            "summary": task.title,
            "description": task.description or "",
            "start": {
                "dateTime": (
                    task.due_date.isoformat()
                    if task.due_date
                    else datetime.now(timezone.utc).isoformat()
                ),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": (
                    (task.due_date + timedelta(hours=1)).isoformat()
                    if task.due_date
                    else (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
                ),
                "timeZone": "UTC",
            },
            "reminders": {"useDefault": False, "overrides": []},
        }

        # Add reminder if task has reminder_date
        if hasattr(task, "reminder_date") and task.reminder_date:
            minutes_before = (
                int((task.due_date - task.reminder_date).total_seconds() / 60)
                if task.due_date
                else 60
            )
            event_data["reminders"]["overrides"].append(
                {"method": "popup", "minutes": max(0, minutes_before)}
            )

        try:
            async with httpx.AsyncClient() as client:
                if action == "create":
                    response = await client.post(
                        f"https://www.googleapis.com/calendar/v3/calendars/{integration.calendar_id}/events",
                        headers=headers,
                        json=event_data,
                    )
                elif action == "update":
                    # Get existing event ID from sync record
                    # This would be retrieved from TaskCalendarSync
                    event_id = f"task-{task.id}"  # Placeholder
                    response = await client.put(
                        f"https://www.googleapis.com/calendar/v3/calendars/{integration.calendar_id}/events/{event_id}",
                        headers=headers,
                        json=event_data,
                    )
                elif action == "delete":
                    event_id = f"task-{task.id}"  # Placeholder
                    response = await client.delete(
                        f"https://www.googleapis.com/calendar/v3/calendars/{integration.calendar_id}/events/{event_id}",
                        headers=headers,
                    )
                    return None

                if response.status_code in [200, 201]:
                    event = response.json()
                    return event.get("id")
                else:
                    logger.error(
                        f"Google Calendar sync failed: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Error syncing with Google Calendar: {e}")
            return None

    @staticmethod
    async def sync_with_microsoft_calendar(
        integration: CalendarIntegration, task: Task, action: str = "create"
    ) -> Optional[str]:
        """Sync a task with Microsoft Calendar (Outlook)."""
        # This is a placeholder for actual Microsoft Graph API integration

        headers = {
            "Authorization": f"Bearer {integration.access_token}",
            "Content-Type": "application/json",
        }

        # Convert task to Microsoft Calendar event format
        event_data = {
            "subject": task.title,
            "body": {"contentType": "text", "content": task.description or ""},
            "start": {
                "dateTime": (
                    task.due_date.isoformat()
                    if task.due_date
                    else datetime.now(timezone.utc).isoformat()
                ),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": (
                    (task.due_date + timedelta(hours=1)).isoformat()
                    if task.due_date
                    else (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
                ),
                "timeZone": "UTC",
            },
            "isReminderOn": bool(hasattr(task, "reminder_date") and task.reminder_date),
            "reminderMinutesBeforeStart": 15,  # Default reminder
        }

        try:
            async with httpx.AsyncClient() as client:
                if action == "create":
                    response = await client.post(
                        f"https://graph.microsoft.com/v1.0/me/calendars/{integration.calendar_id}/events",
                        headers=headers,
                        json=event_data,
                    )
                elif action == "update":
                    event_id = f"task-{task.id}"  # Placeholder
                    response = await client.patch(
                        f"https://graph.microsoft.com/v1.0/me/events/{event_id}",
                        headers=headers,
                        json=event_data,
                    )
                elif action == "delete":
                    event_id = f"task-{task.id}"  # Placeholder
                    response = await client.delete(
                        f"https://graph.microsoft.com/v1.0/me/events/{event_id}",
                        headers=headers,
                    )
                    return None

                if response.status_code in [200, 201]:
                    event = response.json()
                    return event.get("id")
                else:
                    logger.error(
                        f"Microsoft Calendar sync failed: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Error syncing with Microsoft Calendar: {e}")
            return None

    @staticmethod
    async def sync_task(
        db: Session,
        task: Task,
        integration: CalendarIntegration,
        action: str = "create",
    ) -> bool:
        """Sync a task with the appropriate calendar provider."""
        if not integration.sync_enabled:
            return False

        # Check sync direction
        if (
            action in ["create", "update"]
            and integration.sync_direction == SyncDirection.FROM_CALENDAR
        ):
            return False
        elif (
            action == "delete"
            and integration.sync_direction == SyncDirection.FROM_CALENDAR
        ):
            return False

        event_id = None

        try:
            if integration.provider == CalendarProvider.GOOGLE:
                event_id = await CalendarService.sync_with_google_calendar(
                    integration, task, action
                )
            elif integration.provider == CalendarProvider.MICROSOFT:
                event_id = await CalendarService.sync_with_microsoft_calendar(
                    integration, task, action
                )
            else:
                logger.warning(f"Unsupported calendar provider: {integration.provider}")
                return False

            if action != "delete" and event_id:
                # Create or update sync record
                CalendarService.sync_task_to_calendar(db, task, integration, event_id)

                # Update last sync time
                integration.last_sync_at = datetime.now(timezone.utc)
                db.commit()
            elif action == "delete":
                # Remove sync record
                CalendarService.remove_task_sync(db, task.id, integration.id)

            return True

        except Exception as e:
            logger.error(f"Error syncing task {task.id} with calendar: {e}")
            return False

    @staticmethod
    async def sync_all_tasks(
        db: Session, user_id: str, integration_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sync all tasks for a user with their calendar integrations."""
        # Get integrations
        if integration_id:
            integrations = [
                db.query(CalendarIntegration)
                .filter(
                    CalendarIntegration.id == integration_id,
                    CalendarIntegration.user_id == user_id,
                )
                .first()
            ]
            integrations = [i for i in integrations if i]  # Filter None
        else:
            integrations = CalendarService.get_user_integrations(db, user_id)

        if not integrations:
            return {
                "synced": 0,
                "failed": 0,
                "errors": ["No active calendar integrations found"],
            }

        # Get user's tasks
        tasks = db.query(Task).filter(Task.user_id == user_id).all()

        synced = 0
        failed = 0
        errors = []

        for integration in integrations:
            for task in tasks:
                try:
                    success = await CalendarService.sync_task(
                        db, task, integration, "create"
                    )
                    if success:
                        synced += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    errors.append(f"Task {task.id}: {str(e)}")

        return {
            "synced": synced,
            "failed": failed,
            "errors": errors[:10],  # Limit error messages
        }
