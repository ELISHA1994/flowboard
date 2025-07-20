"""
Pydantic models for webhook functionality.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class WebhookSubscriptionCreate(BaseModel):
    """Model for creating a webhook subscription."""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the webhook")
    url: HttpUrl = Field(..., description="URL to send webhook events to")
    events: List[str] = Field(..., min_length=1, description="List of events to subscribe to")
    secret: Optional[str] = Field(None, min_length=16, max_length=255, description="Secret for HMAC signature")
    project_id: Optional[str] = Field(None, description="Optional project ID to limit webhook to specific project")


class WebhookSubscriptionUpdate(BaseModel):
    """Model for updating a webhook subscription."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[HttpUrl] = Field(None)
    events: Optional[List[str]] = Field(None, min_length=1)
    is_active: Optional[bool] = Field(None)


class WebhookSubscriptionResponse(BaseModel):
    """Model for webhook subscription response."""
    id: str
    user_id: str
    name: str
    url: str
    events: List[str]
    is_active: bool
    project_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookDeliveryResponse(BaseModel):
    """Model for webhook delivery response."""
    id: str
    subscription_id: str
    event_type: str
    status_code: Optional[int]
    error: Optional[str]
    delivered_at: datetime
    retry_count: int
    next_retry_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookTestRequest(BaseModel):
    """Model for testing a webhook."""
    url: HttpUrl = Field(..., description="URL to test")
    secret: Optional[str] = Field(None, description="Optional secret for HMAC signature")
    event_type: str = Field(default="test.webhook", description="Event type to send")