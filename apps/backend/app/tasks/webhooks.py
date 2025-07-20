"""
Background tasks for webhook delivery and processing.
"""
import logging
import json
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

import httpx
from sqlalchemy.orm import Session
from celery import Task

from app.core.celery_app import celery_app
from app.db.database import get_db
from app.db.models import WebhookSubscription, WebhookDelivery, WebhookDeliveryStatus
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task class that provides database session."""
    
    def __call__(self, *args, **kwargs):
        with get_db() as db:
            return self.run_with_db(db, *args, **kwargs)
    
    def run_with_db(self, db: Session, *args, **kwargs):
        """Override this method instead of run()"""
        raise NotImplementedError


def generate_webhook_signature(payload: str, secret: str) -> str:
    """Generate HMAC signature for webhook payload."""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


@celery_app.task(bind=True, base=DatabaseTask, queue="webhooks")
def deliver_webhook(self, db: Session, subscription_id: str, event_type: str, payload: Dict[str, Any]):
    """Deliver a webhook to a subscribed endpoint."""
    try:
        subscription = db.query(WebhookSubscription).filter(
            WebhookSubscription.id == subscription_id
        ).first()
        
        if not subscription:
            logger.warning(f"Webhook subscription {subscription_id} not found")
            return {"success": False, "reason": "Subscription not found"}
        
        if not subscription.is_active:
            logger.info(f"Webhook subscription {subscription_id} is inactive")
            return {"success": False, "reason": "Subscription inactive"}
        
        # Check if this event type is subscribed to
        if event_type not in subscription.events:
            logger.debug(f"Event type {event_type} not subscribed for {subscription_id}")
            return {"success": False, "reason": "Event not subscribed"}
        
        # Create delivery record
        delivery = WebhookDelivery(
            subscription_id=subscription_id,
            event_type=event_type,
            payload=payload,
            status=WebhookDeliveryStatus.PENDING
        )
        db.add(delivery)
        db.commit()
        
        # Prepare the webhook payload
        webhook_payload = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
            "delivery_id": delivery.id
        }
        
        payload_str = json.dumps(webhook_payload, default=str)
        
        # Generate signature if secret is provided
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"TaskManager-Webhook/1.0",
            "X-Webhook-Event": event_type,
            "X-Webhook-Delivery": delivery.id
        }
        
        if subscription.secret:
            signature = generate_webhook_signature(payload_str, subscription.secret)
            headers["X-Webhook-Signature-256"] = f"sha256={signature}"
        
        # Deliver the webhook with retries
        timeout_config = httpx.Timeout(
            connect=5.0,  # 5 seconds to connect
            read=30.0,    # 30 seconds to read response
            write=10.0,   # 10 seconds to write request
            pool=10.0     # 10 seconds to get connection from pool
        )
        
        with httpx.Client(timeout=timeout_config) as client:
            response = client.post(
                subscription.url,
                content=payload_str,
                headers=headers
            )
        
        # Update delivery status
        delivery.delivered_at = datetime.now(timezone.utc)
        delivery.response_status_code = response.status_code
        delivery.response_headers = dict(response.headers)
        delivery.response_body = response.text[:1000]  # Limit response body storage
        
        if 200 <= response.status_code < 300:
            delivery.status = WebhookDeliveryStatus.DELIVERED
            logger.info(f"Webhook delivered successfully to {subscription.url} for event {event_type}")
            
            # Reset failure count on successful delivery
            subscription.failure_count = 0
            subscription.last_delivery_at = delivery.delivered_at
            
        else:
            delivery.status = WebhookDeliveryStatus.FAILED
            delivery.failure_reason = f"HTTP {response.status_code}: {response.text[:200]}"
            
            # Increment failure count
            subscription.failure_count += 1
            subscription.last_failure_at = delivery.delivered_at
            
            logger.warning(f"Webhook delivery failed to {subscription.url}: {response.status_code}")
            
            # Disable subscription after too many failures
            if subscription.failure_count >= 10:
                subscription.is_active = False
                logger.warning(f"Disabled webhook subscription {subscription_id} after {subscription.failure_count} failures")
        
        db.commit()
        
        return {
            "success": delivery.status == WebhookDeliveryStatus.DELIVERED,
            "delivery_id": delivery.id,
            "status_code": response.status_code,
            "subscription_id": subscription_id
        }
        
    except httpx.TimeoutException:
        # Handle timeout specifically
        delivery.status = WebhookDeliveryStatus.FAILED
        delivery.failure_reason = "Request timeout"
        subscription.failure_count += 1
        subscription.last_failure_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.warning(f"Webhook delivery timeout to {subscription.url}")
        raise self.retry(countdown=60 * (self.request.retries + 1), max_retries=3)
        
    except httpx.RequestError as e:
        # Handle connection errors
        delivery.status = WebhookDeliveryStatus.FAILED
        delivery.failure_reason = f"Connection error: {str(e)}"
        subscription.failure_count += 1
        subscription.last_failure_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.error(f"Webhook delivery connection error to {subscription.url}: {str(e)}")
        raise self.retry(countdown=60 * (self.request.retries + 1), max_retries=3)
        
    except Exception as e:
        # Handle other errors
        if 'delivery' in locals():
            delivery.status = WebhookDeliveryStatus.FAILED
            delivery.failure_reason = f"Error: {str(e)}"
            db.commit()
        
        logger.error(f"Webhook delivery error: {str(e)}")
        raise self.retry(countdown=60 * (self.request.retries + 1), max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="webhooks")
def broadcast_webhook_event(self, db: Session, event_type: str, payload: Dict[str, Any], user_id: Optional[str] = None):
    """Broadcast a webhook event to all applicable subscriptions."""
    try:
        # Get all active subscriptions for this event type
        query = db.query(WebhookSubscription).filter(
            WebhookSubscription.is_active == True,
            WebhookSubscription.events.contains([event_type])
        )
        
        # Filter by user if specified
        if user_id:
            query = query.filter(WebhookSubscription.user_id == user_id)
        
        subscriptions = query.all()
        
        if not subscriptions:
            logger.debug(f"No active subscriptions found for event {event_type}")
            return {"success": True, "delivered_count": 0}
        
        # Queue delivery for each subscription
        delivery_tasks = []
        for subscription in subscriptions:
            try:
                task = deliver_webhook.delay(subscription.id, event_type, payload)
                delivery_tasks.append(task.id)
            except Exception as e:
                logger.error(f"Failed to queue webhook delivery for subscription {subscription.id}: {str(e)}")
        
        logger.info(f"Queued {len(delivery_tasks)} webhook deliveries for event {event_type}")
        return {
            "success": True,
            "delivered_count": len(delivery_tasks),
            "delivery_task_ids": delivery_tasks
        }
        
    except Exception as e:
        logger.error(f"Failed to broadcast webhook event {event_type}: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="webhooks")
def retry_failed_webhooks(self, db: Session, max_age_hours: int = 24):
    """Retry failed webhook deliveries that are not too old."""
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        # Find failed deliveries to retry
        failed_deliveries = db.query(WebhookDelivery).filter(
            WebhookDelivery.status == WebhookDeliveryStatus.FAILED,
            WebhookDelivery.created_at >= cutoff_time,
            WebhookDelivery.retry_count < 3  # Limit retries
        ).all()
        
        retry_count = 0
        for delivery in failed_deliveries:
            try:
                # Increment retry count
                delivery.retry_count += 1
                db.commit()
                
                # Queue for retry
                deliver_webhook.delay(
                    delivery.subscription_id,
                    delivery.event_type,
                    delivery.payload
                )
                retry_count += 1
                
            except Exception as e:
                logger.error(f"Failed to queue retry for delivery {delivery.id}: {str(e)}")
        
        logger.info(f"Queued {retry_count} webhook deliveries for retry")
        return {"success": True, "retry_count": retry_count}
        
    except Exception as e:
        logger.error(f"Failed to retry webhook deliveries: {str(e)}")
        raise self.retry(countdown=300, max_retries=2)


@celery_app.task(bind=True, base=DatabaseTask, queue="webhooks")
def cleanup_old_webhook_deliveries(self, db: Session, keep_days: int = 30):
    """Clean up old webhook delivery records."""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=keep_days)
        
        # Delete old delivery records
        deleted_count = db.query(WebhookDelivery).filter(
            WebhookDelivery.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old webhook delivery records")
        return {"success": True, "deleted_count": deleted_count}
        
    except Exception as e:
        logger.error(f"Failed to cleanup webhook deliveries: {str(e)}")
        raise self.retry(countdown=300, max_retries=2)


@celery_app.task(bind=True, base=DatabaseTask, queue="webhooks")
def test_webhook_endpoint(self, db: Session, subscription_id: str):
    """Test a webhook endpoint with a ping event."""
    try:
        subscription = db.query(WebhookSubscription).filter(
            WebhookSubscription.id == subscription_id
        ).first()
        
        if not subscription:
            return {"success": False, "reason": "Subscription not found"}
        
        # Send a test ping
        test_payload = {
            "message": "This is a test webhook from Task Manager",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "subscription_id": subscription_id
        }
        
        result = deliver_webhook.delay(subscription_id, "webhook.ping", test_payload)
        
        logger.info(f"Queued test webhook for subscription {subscription_id}")
        return {
            "success": True,
            "test_delivery_task_id": result.id,
            "subscription_id": subscription_id
        }
        
    except Exception as e:
        logger.error(f"Failed to test webhook endpoint {subscription_id}: {str(e)}")
        raise self.retry(countdown=60, max_retries=2)


# Event-specific webhook tasks
@celery_app.task(bind=True, queue="webhooks")
def send_task_created_webhook(self, task_data: Dict[str, Any]):
    """Send webhook for task created event."""
    return broadcast_webhook_event.delay("task.created", task_data, task_data.get("user_id"))


@celery_app.task(bind=True, queue="webhooks")
def send_task_updated_webhook(self, task_data: Dict[str, Any]):
    """Send webhook for task updated event."""
    return broadcast_webhook_event.delay("task.updated", task_data, task_data.get("user_id"))


@celery_app.task(bind=True, queue="webhooks")
def send_task_completed_webhook(self, task_data: Dict[str, Any]):
    """Send webhook for task completed event."""
    return broadcast_webhook_event.delay("task.completed", task_data, task_data.get("user_id"))


@celery_app.task(bind=True, queue="webhooks")
def send_task_deleted_webhook(self, task_data: Dict[str, Any]):
    """Send webhook for task deleted event."""
    return broadcast_webhook_event.delay("task.deleted", task_data, task_data.get("user_id"))


@celery_app.task(bind=True, queue="webhooks")
def send_project_created_webhook(self, project_data: Dict[str, Any]):
    """Send webhook for project created event."""
    return broadcast_webhook_event.delay("project.created", project_data, project_data.get("owner_id"))


@celery_app.task(bind=True, queue="webhooks")
def send_user_invited_webhook(self, invitation_data: Dict[str, Any]):
    """Send webhook for user invited to project event."""
    return broadcast_webhook_event.delay("project.user_invited", invitation_data, invitation_data.get("inviter_id"))