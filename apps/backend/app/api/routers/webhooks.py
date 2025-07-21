"""
Webhook management API endpoints.
"""

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import List

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.core.middleware.jwt_auth_backend import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.models.webhook import (WebhookDeliveryResponse,
                                WebhookSubscriptionCreate,
                                WebhookSubscriptionResponse,
                                WebhookSubscriptionUpdate, WebhookTestRequest)
from app.services.webhook_service import WebhookEvent, WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/subscriptions", response_model=WebhookSubscriptionResponse)
async def create_webhook_subscription(
    subscription: WebhookSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new webhook subscription."""
    try:
        webhook = WebhookService.create_subscription(
            db,
            current_user.id,
            subscription.name,
            str(subscription.url),
            subscription.events,
            subscription.secret,
            subscription.project_id,
        )

        # Convert events from JSON string to list for response
        webhook.events = json.loads(webhook.events)
        return webhook
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscriptions", response_model=List[WebhookSubscriptionResponse])
async def get_webhook_subscriptions(
    project_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all webhook subscriptions for the current user."""
    subscriptions = WebhookService.get_user_subscriptions(
        db, current_user.id, project_id
    )

    # Convert events from JSON string to list for response
    for sub in subscriptions:
        sub.events = json.loads(sub.events)

    return subscriptions


@router.get(
    "/subscriptions/{subscription_id}", response_model=WebhookSubscriptionResponse
)
async def get_webhook_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific webhook subscription."""
    subscriptions = WebhookService.get_user_subscriptions(db, current_user.id)
    subscription = next((s for s in subscriptions if s.id == subscription_id), None)

    if not subscription:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")

    subscription.events = json.loads(subscription.events)
    return subscription


@router.put(
    "/subscriptions/{subscription_id}", response_model=WebhookSubscriptionResponse
)
async def update_webhook_subscription(
    subscription_id: str,
    update: WebhookSubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a webhook subscription."""
    try:
        subscription = WebhookService.update_subscription(
            db,
            subscription_id,
            current_user.id,
            update.name,
            str(update.url) if update.url else None,
            update.events,
            update.is_active,
        )

        if not subscription:
            raise HTTPException(
                status_code=404, detail="Webhook subscription not found"
            )

        subscription.events = json.loads(subscription.events)
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/subscriptions/{subscription_id}")
async def delete_webhook_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a webhook subscription."""
    success = WebhookService.delete_subscription(db, subscription_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")

    return {"message": "Webhook subscription deleted successfully"}


@router.get(
    "/subscriptions/{subscription_id}/deliveries",
    response_model=List[WebhookDeliveryResponse],
)
async def get_webhook_deliveries(
    subscription_id: str,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get delivery history for a webhook subscription."""
    deliveries = WebhookService.get_delivery_history(
        db, subscription_id, current_user.id, limit
    )

    return deliveries


@router.get("/events")
async def get_webhook_events():
    """Get list of all available webhook events."""
    return {
        "events": [
            {"name": event.value, "description": event.value.replace(".", " ").title()}
            for event in WebhookEvent
        ]
    }


@router.post("/test")
async def test_webhook(
    test_request: WebhookTestRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Test a webhook URL by sending a test event."""

    async def send_test_webhook():
        webhook_payload = {
            "event": test_request.event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "message": "This is a test webhook",
                "user_id": current_user.id,
                "username": current_user.username,
            },
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "TaskManager-Webhook/1.0",
        }

        # Add HMAC signature if secret is provided
        if test_request.secret:
            payload_bytes = json.dumps(webhook_payload).encode("utf-8")
            signature = hmac.new(
                test_request.secret.encode("utf-8"), payload_bytes, hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    str(test_request.url), json=webhook_payload, headers=headers
                )

            logger.info(
                f"Test webhook sent to {test_request.url}: {response.status_code}"
            )

        except Exception as e:
            logger.error(f"Failed to send test webhook: {e}")

    # Send webhook in background
    background_tasks.add_task(send_test_webhook)

    return {
        "message": "Test webhook is being sent",
        "url": str(test_request.url),
        "event_type": test_request.event_type,
    }
