import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import (APIRouter, Cookie, Depends, HTTPException, Request,
                     Response, status)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.middleware.jwt_auth_backend import (get_current_active_user,
                                                  get_password_hash,
                                                  verify_password)
from app.db.database import get_db
from app.db.models import User as UserModel
from app.models.auth import RefreshTokenRequest, SessionInfo, TokenPair
from app.models.user import Token, UserCreate, UserResponse
from app.services.refresh_token_service import RefreshTokenService
from app.services.user_service import UserService

# Removed user_agents dependency


router = APIRouter()

# Determine cookie settings based on environment
IS_PRODUCTION = settings.ENVIRONMENT == "production"
# For development with different ports, we need SameSite=None
# But SameSite=None requires Secure=True, which requires HTTPS
# So we'll check if we're in true local development
IS_LOCAL_DEV = settings.ENVIRONMENT == "development" and not IS_PRODUCTION

if IS_LOCAL_DEV:
    # For local development with different ports
    SECURE_COOKIES = False
    COOKIE_SAMESITE = "none" if settings.ENVIRONMENT == "production" else "lax"
    # Actually, for cross-port in dev, we need a workaround
    # Let's use the proxy approach instead
    COOKIE_SAMESITE = "lax"
else:
    # Production settings
    SECURE_COOKIES = True
    COOKIE_SAMESITE = "lax"


def get_device_info(request: Request) -> dict:
    """Extract device information from request."""
    user_agent_string = request.headers.get("User-Agent", "")

    # Simple user agent parsing without external dependency
    device_type = "desktop"
    browser_name = "Unknown"
    os_name = "Unknown"

    # Detect device type
    if any(
        mobile in user_agent_string.lower()
        for mobile in ["mobile", "android", "iphone", "ipad"]
    ):
        if "ipad" in user_agent_string.lower() or "tablet" in user_agent_string.lower():
            device_type = "tablet"
        else:
            device_type = "mobile"

    # Detect browser
    if "Chrome" in user_agent_string and "Edg" not in user_agent_string:
        browser_name = "Chrome"
    elif "Firefox" in user_agent_string:
        browser_name = "Firefox"
    elif "Safari" in user_agent_string and "Chrome" not in user_agent_string:
        browser_name = "Safari"
    elif "Edg" in user_agent_string:
        browser_name = "Edge"
    elif "Opera" in user_agent_string or "OPR" in user_agent_string:
        browser_name = "Opera"

    # Detect OS
    if "Windows" in user_agent_string:
        os_name = "Windows"
    elif "Mac OS" in user_agent_string or "Macintosh" in user_agent_string:
        os_name = "macOS"
    elif "Linux" in user_agent_string:
        os_name = "Linux"
    elif "Android" in user_agent_string:
        os_name = "Android"
    elif "iPhone" in user_agent_string or "iPad" in user_agent_string:
        os_name = "iOS"

    # Get client IP
    ip = request.client.host if request.client else None

    return {
        "device_name": f"{browser_name} on {os_name}",
        "device_type": device_type,
        "browser": browser_name,
        "ip_address": ip,
    }


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username already exists
    if db.query(UserModel).filter(UserModel.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    if db.query(UserModel).filter(UserModel.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    db_user = UserModel(
        id=str(uuid.uuid4()),
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=TokenPair)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login and receive access token + set refresh token in HttpOnly cookie"""
    # Find user by username
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get device info
    device_info = get_device_info(request)

    # Create access token
    access_token = UserService.create_access_token(user.id)

    # Create refresh token
    refresh_token, family, expires_at = RefreshTokenService.create_refresh_token(
        db, user.id, device_info
    )

    # Set refresh token in HttpOnly cookie
    print(
        f"[LOGIN] Setting refresh token cookie, secure={SECURE_COOKIES}, samesite={COOKIE_SAMESITE}"
    )
    print(f"[LOGIN] Environment: {settings.ENVIRONMENT}")
    print(f"[LOGIN] Token family: {family}")
    print(
        f"[LOGIN] Cookie will be set with: httponly=True, secure={SECURE_COOKIES}, samesite={COOKIE_SAMESITE}"
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=30 * 24 * 60 * 60,  # 30 days
        expires=expires_at,
        httponly=True,
        secure=SECURE_COOKIES,  # HTTPS only in production
        samesite=COOKIE_SAMESITE,
        path="/",
        domain=None,  # Let browser handle domain
    )

    # Set family ID in a separate cookie for CSRF protection
    response.set_cookie(
        key="token_family",
        value=family,
        max_age=30 * 24 * 60 * 60,  # 30 days
        expires=expires_at,
        httponly=False,  # Accessible to JS for CSRF check
        secure=SECURE_COOKIES,
        samesite=COOKIE_SAMESITE,
        path="/",
        domain=None,  # Let browser handle domain
    )

    return TokenPair(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(None),
    token_family: Optional[str] = Cookie(None),
):
    """Exchange refresh token for new access token (with rotation)"""
    # Debug logging
    print(f"[REFRESH] Received refresh token cookie: {bool(refresh_token)}")
    print(f"[REFRESH] Received token family cookie: {bool(token_family)}")
    print(f"[REFRESH] All cookies: {request.cookies}")

    if not refresh_token:
        print("[REFRESH] No refresh token found in cookies")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get device info for new token
    device_info = get_device_info(request)

    # Validate and rotate token
    new_access_token, new_refresh_token, family, expires_at = (
        RefreshTokenService.validate_and_rotate_token(db, refresh_token, device_info)
    )

    if not new_access_token:
        # Clear cookies on failure
        response.delete_cookie("refresh_token")
        response.delete_cookie("token_family")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify family matches (CSRF protection)
    if token_family and token_family != family:
        # Potential CSRF attack - revoke the family
        RefreshTokenService.revoke_token_family(db, family, "csrf_mismatch")
        response.delete_cookie("refresh_token")
        response.delete_cookie("token_family")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Security validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Set new refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        max_age=30 * 24 * 60 * 60,  # 30 days
        expires=expires_at,
        httponly=True,
        secure=SECURE_COOKIES,
        samesite=COOKIE_SAMESITE,
        path="/",
        domain=None,
    )

    # Update family cookie
    response.set_cookie(
        key="token_family",
        value=family,
        max_age=30 * 24 * 60 * 60,  # 30 days
        expires=expires_at,
        httponly=False,
        secure=SECURE_COOKIES,
        samesite=COOKIE_SAMESITE,
        path="/",
        domain=None,
    )

    return TokenPair(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    refresh_token: Optional[str] = Cookie(None),
):
    """Logout current session (revoke refresh token)"""
    if refresh_token:
        # Hash and revoke the token
        token_hash = RefreshTokenService._hash_token(refresh_token)
        RefreshTokenService.revoke_token(db, token_hash, "user_logout")

    # Clear cookies
    response.delete_cookie("refresh_token")
    response.delete_cookie("token_family")

    return None


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    response: Response,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """Logout all sessions (revoke all refresh tokens)"""
    RefreshTokenService.revoke_all_user_tokens(db, current_user.id, "logout_all")

    # Clear cookies
    response.delete_cookie("refresh_token")
    response.delete_cookie("token_family")

    return None


@router.get("/sessions", response_model=list[SessionInfo])
async def get_sessions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    token_family: Optional[str] = Cookie(None),
):
    """Get all active sessions for the current user"""
    sessions = RefreshTokenService.get_user_sessions(db, current_user.id)

    # Mark current session
    if token_family:
        for session in sessions:
            if session.id == token_family:
                session.is_current = True
                break

    return sessions


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """Revoke a specific session (by family ID)"""
    # Check if the session belongs to the user
    sessions = RefreshTokenService.get_user_sessions(db, current_user.id)
    session_ids = [s.id for s in sessions]

    if session_id not in session_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    # Revoke the session
    RefreshTokenService.revoke_token_family(db, session_id, "user_revoked")

    return None


@router.get("/test-cookies")
async def test_cookies(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    token_family: Optional[str] = Cookie(None),
):
    """Test endpoint to verify cookies are being sent"""
    # Also set a test cookie to verify cookie setting works
    response.set_cookie(
        key="test_cookie",
        value="test_value",
        max_age=60,  # 1 minute
        httponly=False,
        secure=False,  # Allow HTTP for testing
        samesite="lax",
        path="/",
        domain=None,
    )

    return {
        "has_refresh_token": bool(refresh_token),
        "has_token_family": bool(token_family),
        "all_cookies": list(request.cookies.keys()),
        "cookie_count": len(request.cookies),
        "test_cookie_set": True,
    }
