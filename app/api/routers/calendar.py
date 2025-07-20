"""
Calendar integration API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.core.middleware.jwt_auth_backend import get_current_user
from app.models.calendar import (
    CalendarIntegrationCreate, CalendarIntegrationUpdate,
    CalendarIntegrationResponse, CalendarSyncRequest, CalendarSyncResponse,
    TaskCalendarSyncResponse, CalendarEventCreate, CalendarEventUpdate,
    CalendarEventDelete, CalendarOAuthCallback
)
from app.services.calendar_service import CalendarService, CalendarProvider
from app.core.logging import logger

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/integrations", response_model=CalendarIntegrationResponse)
async def create_calendar_integration(
    integration: CalendarIntegrationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new calendar integration."""
    try:
        calendar_integration = CalendarService.create_integration(
            db,
            current_user.id,
            integration.provider.value,
            integration.calendar_id,
            integration.calendar_name,
            integration.access_token,
            integration.refresh_token,
            integration.token_expires_at,
            integration.sync_direction.value
        )
        
        return calendar_integration
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating calendar integration: {e}")
        raise HTTPException(status_code=500, detail="Failed to create calendar integration")


@router.get("/integrations", response_model=List[CalendarIntegrationResponse])
async def get_calendar_integrations(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    active_only: bool = Query(True, description="Only return active integrations"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all calendar integrations for the current user."""
    integrations = CalendarService.get_user_integrations(
        db,
        current_user.id,
        provider,
        active_only
    )
    
    return integrations


@router.get("/integrations/{integration_id}", response_model=CalendarIntegrationResponse)
async def get_calendar_integration(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific calendar integration."""
    integrations = CalendarService.get_user_integrations(db, current_user.id, active_only=False)
    integration = next((i for i in integrations if i.id == integration_id), None)
    
    if not integration:
        raise HTTPException(status_code=404, detail="Calendar integration not found")
    
    return integration


@router.put("/integrations/{integration_id}", response_model=CalendarIntegrationResponse)
async def update_calendar_integration(
    integration_id: str,
    update: CalendarIntegrationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a calendar integration."""
    try:
        integration = CalendarService.update_integration(
            db,
            integration_id,
            current_user.id,
            sync_enabled=update.sync_enabled,
            sync_direction=update.sync_direction.value if update.sync_direction else None
        )
        
        if not integration:
            raise HTTPException(status_code=404, detail="Calendar integration not found")
        
        return integration
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/integrations/{integration_id}")
async def delete_calendar_integration(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a calendar integration."""
    success = CalendarService.delete_integration(
        db,
        integration_id,
        current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Calendar integration not found")
    
    return {"message": "Calendar integration deleted successfully"}


@router.post("/sync", response_model=CalendarSyncResponse)
async def sync_calendar(
    sync_request: CalendarSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger calendar sync."""
    # Run sync in background
    async def run_sync():
        result = await CalendarService.sync_all_tasks(
            db,
            current_user.id,
            sync_request.integration_id
        )
        logger.info(f"Calendar sync completed for user {current_user.id}: {result}")
    
    background_tasks.add_task(run_sync)
    
    return CalendarSyncResponse(
        synced=0,
        failed=0,
        errors=["Sync started in background"]
    )


@router.get("/sync/status/{integration_id}", response_model=TaskCalendarSyncResponse)
async def get_sync_status(
    integration_id: str,
    task_id: str = Query(..., description="Task ID to check sync status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync status for a specific task."""
    # Verify integration belongs to user
    integrations = CalendarService.get_user_integrations(db, current_user.id, active_only=False)
    integration = next((i for i in integrations if i.id == integration_id), None)
    
    if not integration:
        raise HTTPException(status_code=404, detail="Calendar integration not found")
    
    # Get sync status
    syncs = CalendarService.get_task_syncs(db, task_id)
    sync = next((s for s in syncs if s.calendar_integration_id == integration_id), None)
    
    if not sync:
        raise HTTPException(status_code=404, detail="Task not synced with this calendar")
    
    return sync


@router.post("/events", status_code=201)
async def create_calendar_event(
    event: CalendarEventCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a calendar event from a task."""
    # Get task
    from app.db.models import Task
    task = db.query(Task).filter(
        Task.id == event.task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get integration
    integrations = CalendarService.get_user_integrations(db, current_user.id, active_only=False)
    integration = next((i for i in integrations if i.id == event.integration_id), None)
    
    if not integration:
        raise HTTPException(status_code=404, detail="Calendar integration not found")
    
    # Sync in background
    async def sync_task():
        success = await CalendarService.sync_task(db, task, integration, "create")
        if success:
            logger.info(f"Task {task.id} synced to calendar {integration.id}")
        else:
            logger.error(f"Failed to sync task {task.id} to calendar {integration.id}")
    
    background_tasks.add_task(sync_task)
    
    return {"message": "Calendar event creation started"}


@router.put("/events")
async def update_calendar_event(
    event: CalendarEventUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a calendar event from a task."""
    # Get task
    from app.db.models import Task
    task = db.query(Task).filter(
        Task.id == event.task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get integration
    integrations = CalendarService.get_user_integrations(db, current_user.id, active_only=False)
    integration = next((i for i in integrations if i.id == event.integration_id), None)
    
    if not integration:
        raise HTTPException(status_code=404, detail="Calendar integration not found")
    
    # Sync in background
    async def sync_task():
        success = await CalendarService.sync_task(db, task, integration, "update")
        if success:
            logger.info(f"Task {task.id} updated in calendar {integration.id}")
        else:
            logger.error(f"Failed to update task {task.id} in calendar {integration.id}")
    
    background_tasks.add_task(sync_task)
    
    return {"message": "Calendar event update started"}


@router.delete("/events")
async def delete_calendar_event(
    event: CalendarEventDelete,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a calendar event."""
    # Get task
    from app.db.models import Task
    task = db.query(Task).filter(
        Task.id == event.task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get integration
    integrations = CalendarService.get_user_integrations(db, current_user.id, active_only=False)
    integration = next((i for i in integrations if i.id == event.integration_id), None)
    
    if not integration:
        raise HTTPException(status_code=404, detail="Calendar integration not found")
    
    # Sync in background
    async def sync_task():
        success = await CalendarService.sync_task(db, task, integration, "delete")
        if success:
            logger.info(f"Task {task.id} deleted from calendar {integration.id}")
        else:
            logger.error(f"Failed to delete task {task.id} from calendar {integration.id}")
    
    background_tasks.add_task(sync_task)
    
    return {"message": "Calendar event deletion started"}


@router.get("/providers")
async def get_calendar_providers():
    """Get list of supported calendar providers."""
    return {
        "providers": [
            {
                "id": provider.value,
                "name": provider.value.title(),
                "oauth_url": f"/api/calendar/oauth/{provider.value}"
            }
            for provider in CalendarProvider
        ]
    }


@router.get("/oauth/{provider}")
async def initiate_oauth(
    provider: str,
    redirect_uri: str = Query(..., description="Redirect URI after OAuth"),
    current_user: User = Depends(get_current_user)
):
    """Initiate OAuth flow for calendar provider."""
    # This is a placeholder - in production, you would implement actual OAuth flows
    
    if provider == CalendarProvider.GOOGLE:
        # Google OAuth URL construction
        client_id = "YOUR_GOOGLE_CLIENT_ID"  # From environment
        oauth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope=https://www.googleapis.com/auth/calendar&"
            f"state={current_user.id}"
        )
    elif provider == CalendarProvider.MICROSOFT:
        # Microsoft OAuth URL construction
        client_id = "YOUR_MICROSOFT_CLIENT_ID"  # From environment
        oauth_url = (
            f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope=https://graph.microsoft.com/calendars.readwrite&"
            f"state={current_user.id}"
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    
    return {"oauth_url": oauth_url}


@router.post("/oauth/callback")
async def oauth_callback(
    callback: CalendarOAuthCallback,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from calendar provider."""
    # This is a placeholder - in production, you would exchange the code for tokens
    
    # Mock response for development
    return {
        "message": "OAuth callback processed",
        "integration_id": "mock-integration-id"
    }