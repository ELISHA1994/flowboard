"""
Service layer for webhook functionality.
"""
import json
import hmac
import hashlib
import httpx
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from enum import Enum

from app.db.models import (
    WebhookSubscription, WebhookDelivery, Project
)
from app.core.logging import logger


class WebhookEvent(str, Enum):
    """Supported webhook event types"""
    # Task events
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_DELETED = "task.deleted"
    TASK_COMPLETED = "task.completed"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMMENTED = "task.commented"
    
    # Project events
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"
    PROJECT_MEMBER_ADDED = "project.member_added"
    PROJECT_MEMBER_REMOVED = "project.member_removed"
    
    # Time tracking events
    TIME_LOGGED = "time.logged"
    
    # File events
    FILE_UPLOADED = "file.uploaded"
    FILE_DELETED = "file.deleted"


class WebhookService:
    """Service for managing webhooks"""
    
    @staticmethod
    def create_subscription(
        db: Session,
        user_id: str,
        name: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> WebhookSubscription:
        """Create a new webhook subscription."""
        # Validate events
        valid_events = [e.value for e in WebhookEvent]
        invalid_events = [e for e in events if e not in valid_events]
        if invalid_events:
            raise ValueError(f"Invalid events: {invalid_events}")
        
        # Verify project access if project_id provided
        if project_id:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project or not project.has_permission(user_id):
                raise ValueError("Invalid project or no access")
        
        subscription = WebhookSubscription(
            user_id=user_id,
            name=name,
            url=url,
            events=json.dumps(events),
            secret=secret,
            project_id=project_id
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        logger.info(f"Created webhook subscription {subscription.id} for user {user_id}")
        return subscription
    
    @staticmethod
    def get_user_subscriptions(
        db: Session,
        user_id: str,
        project_id: Optional[str] = None
    ) -> List[WebhookSubscription]:
        """Get all webhook subscriptions for a user."""
        query = db.query(WebhookSubscription).filter(
            WebhookSubscription.user_id == user_id
        )
        
        if project_id:
            query = query.filter(WebhookSubscription.project_id == project_id)
        
        return query.all()
    
    @staticmethod
    def update_subscription(
        db: Session,
        subscription_id: str,
        user_id: str,
        name: Optional[str] = None,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[WebhookSubscription]:
        """Update a webhook subscription."""
        subscription = db.query(WebhookSubscription).filter(
            WebhookSubscription.id == subscription_id,
            WebhookSubscription.user_id == user_id
        ).first()
        
        if not subscription:
            return None
        
        if name is not None:
            subscription.name = name
        if url is not None:
            subscription.url = url
        if events is not None:
            # Validate events
            valid_events = [e.value for e in WebhookEvent]
            invalid_events = [e for e in events if e not in valid_events]
            if invalid_events:
                raise ValueError(f"Invalid events: {invalid_events}")
            subscription.events = json.dumps(events)
        if is_active is not None:
            subscription.is_active = is_active
        
        db.commit()
        db.refresh(subscription)
        return subscription
    
    @staticmethod
    def delete_subscription(
        db: Session,
        subscription_id: str,
        user_id: str
    ) -> bool:
        """Delete a webhook subscription."""
        subscription = db.query(WebhookSubscription).filter(
            WebhookSubscription.id == subscription_id,
            WebhookSubscription.user_id == user_id
        ).first()
        
        if not subscription:
            return False
        
        db.delete(subscription)
        db.commit()
        
        logger.info(f"Deleted webhook subscription {subscription_id}")
        return True
    
    @staticmethod
    def trigger_webhook(
        db: Session,
        event_type: WebhookEvent,
        payload: Dict[str, Any],
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        """Trigger webhooks for an event."""
        # Find relevant subscriptions
        query = db.query(WebhookSubscription).filter(
            WebhookSubscription.is_active == True
        )
        
        if user_id:
            query = query.filter(WebhookSubscription.user_id == user_id)
        
        if project_id:
            # Include both project-specific and user-wide subscriptions
            query = query.filter(
                or_(
                    WebhookSubscription.project_id == project_id,
                    WebhookSubscription.project_id.is_(None)
                )
            )
        
        subscriptions = query.all()
        
        # Filter subscriptions that include this event
        relevant_subscriptions = []
        for sub in subscriptions:
            sub_events = json.loads(sub.events)
            if event_type.value in sub_events or "*" in sub_events:
                relevant_subscriptions.append(sub)
        
        # Send webhooks asynchronously
        for subscription in relevant_subscriptions:
            WebhookService._deliver_webhook(
                db,
                subscription,
                event_type.value,
                payload
            )
    
    @staticmethod
    def _deliver_webhook(
        db: Session,
        subscription: WebhookSubscription,
        event_type: str,
        payload: Dict[str, Any]
    ):
        """Deliver a webhook to a subscription."""
        # Prepare webhook payload
        webhook_payload = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload
        }
        
        # Create delivery record
        delivery = WebhookDelivery(
            subscription_id=subscription.id,
            event_type=event_type,
            payload=json.dumps(webhook_payload)
        )
        
        try:
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "TaskManager-Webhook/1.0"
            }
            
            # Add HMAC signature if secret is configured
            if subscription.secret:
                payload_bytes = json.dumps(webhook_payload).encode('utf-8')
                signature = hmac.new(
                    subscription.secret.encode('utf-8'),
                    payload_bytes,
                    hashlib.sha256
                ).hexdigest()
                headers["X-Webhook-Signature"] = f"sha256={signature}"
            
            # Send webhook
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    subscription.url,
                    json=webhook_payload,
                    headers=headers
                )
            
            delivery.status_code = response.status_code
            delivery.response = response.text[:1000]  # Store first 1000 chars
            
            if response.status_code >= 400:
                delivery.error = f"HTTP {response.status_code}"
                if delivery.retry_count < 3:
                    # Schedule retry
                    delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(
                        minutes=5 * (delivery.retry_count + 1)
                    )
            
            logger.info(f"Delivered webhook to {subscription.url}: {response.status_code}")
            
        except Exception as e:
            delivery.error = str(e)
            delivery.retry_count += 1
            
            if delivery.retry_count < 3:
                # Schedule retry with exponential backoff
                delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(
                    minutes=5 * delivery.retry_count
                )
            
            logger.error(f"Failed to deliver webhook to {subscription.url}: {e}")
        
        db.add(delivery)
        db.commit()
    
    @staticmethod
    def get_delivery_history(
        db: Session,
        subscription_id: str,
        user_id: str,
        limit: int = 100
    ) -> List[WebhookDelivery]:
        """Get webhook delivery history for a subscription."""
        # Verify ownership
        subscription = db.query(WebhookSubscription).filter(
            WebhookSubscription.id == subscription_id,
            WebhookSubscription.user_id == user_id
        ).first()
        
        if not subscription:
            return []
        
        return db.query(WebhookDelivery).filter(
            WebhookDelivery.subscription_id == subscription_id
        ).order_by(
            WebhookDelivery.delivered_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def retry_failed_deliveries(db: Session):
        """Retry failed webhook deliveries (called by background job)."""
        now = datetime.now(timezone.utc)
        
        # Find deliveries that need retry
        deliveries = db.query(WebhookDelivery).filter(
            WebhookDelivery.next_retry_at <= now,
            WebhookDelivery.retry_count < 3
        ).all()
        
        for delivery in deliveries:
            subscription = delivery.subscription
            if not subscription.is_active:
                continue
            
            # Re-deliver the webhook
            payload = json.loads(delivery.payload)
            WebhookService._deliver_webhook(
                db,
                subscription,
                delivery.event_type,
                payload["data"]
            )
            
            # Mark old delivery as retried
            delivery.next_retry_at = None
            db.commit()
    
    @staticmethod
    def cleanup_old_deliveries(db: Session, days: int = 30):
        """Clean up old webhook deliveries."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        deleted = db.query(WebhookDelivery).filter(
            WebhookDelivery.delivered_at < cutoff_date
        ).delete()
        
        db.commit()
        logger.info(f"Cleaned up {deleted} old webhook deliveries")