"""
Pydantic models for authentication and refresh tokens.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TokenPair(BaseModel):
    """Response model for login containing both access and refresh tokens"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expiry


class RefreshTokenRequest(BaseModel):
    """Request model for refresh token endpoint"""

    # Refresh token will be sent via HttpOnly cookie, so no field needed here
    pass


class RefreshTokenData(BaseModel):
    """Internal model for refresh token data stored in JWT"""

    user_id: str
    family: str  # Token family for rotation tracking
    device_id: Optional[str] = None


class RefreshTokenRecord(BaseModel):
    """Model for refresh token database record"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    token_hash: str
    family: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    last_used_at: Optional[datetime] = None
    is_revoked: bool = False
    revoked_at: Optional[datetime] = None
    revoke_reason: Optional[str] = None


class SessionInfo(BaseModel):
    """Model for active session information"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    ip_address: Optional[str] = None
    last_active: Optional[datetime] = None
    created_at: datetime
    is_current: bool = False
