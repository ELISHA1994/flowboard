"""
Service for handling refresh token operations.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from jose import JWTError, jwt
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import RefreshToken, User
from app.models.auth import RefreshTokenData, SessionInfo


class RefreshTokenService:
    """Service for managing JWT refresh tokens with rotation support."""

    # Separate secret for refresh tokens
    REFRESH_SECRET_KEY = settings.SECRET_KEY + "_refresh"
    REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days for refresh tokens
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def _generate_token_family() -> str:
        """Generate a new token family identifier."""
        return str(uuid.uuid4())

    @staticmethod
    def create_refresh_token(
        db: Session, user_id: str, device_info: Optional[dict] = None
    ) -> Tuple[str, str, datetime]:
        """
        Create a new refresh token for a user.

        Returns:
            Tuple of (refresh_token, family_id, expiry_datetime)
        """
        # Generate token family for rotation tracking
        family = RefreshTokenService._generate_token_family()

        # Create token data
        token_data = RefreshTokenData(
            user_id=user_id,
            family=family,
            device_id=device_info.get("device_id") if device_info else None,
        )

        # Set expiration
        expires_delta = timedelta(days=RefreshTokenService.REFRESH_TOKEN_EXPIRE_DAYS)
        expire = datetime.now(timezone.utc) + expires_delta

        # Create JWT token
        to_encode = {
            **token_data.model_dump(),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),  # Unique token ID
        }

        refresh_token = jwt.encode(
            to_encode,
            RefreshTokenService.REFRESH_SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        # Hash token for storage
        token_hash = RefreshTokenService._hash_token(refresh_token)

        # Store in database
        db_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            family=family,
            device_name=device_info.get("device_name") if device_info else None,
            device_type=device_info.get("device_type") if device_info else None,
            browser=device_info.get("browser") if device_info else None,
            ip_address=device_info.get("ip_address") if device_info else None,
            expires_at=expire,
        )

        db.add(db_token)
        db.commit()

        return refresh_token, family, expire

    @staticmethod
    def validate_and_rotate_token(
        db: Session, refresh_token: str, device_info: Optional[dict] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[datetime]]:
        """
        Validate a refresh token and rotate it (issue new one).

        Returns:
            Tuple of (new_access_token, new_refresh_token, family_id, expiry) or (None, None, None, None) if invalid
        """
        try:
            # Decode token
            payload = jwt.decode(
                refresh_token,
                RefreshTokenService.REFRESH_SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )

            user_id = payload.get("user_id")
            family = payload.get("family")

            print(
                f"[REFRESH SERVICE] Decoded token - user_id: {user_id}, family: {family}"
            )

            if not user_id or not family:
                print("[REFRESH SERVICE] Missing user_id or family in token")
                return None, None, None, None

            # Hash the token to look it up
            token_hash = RefreshTokenService._hash_token(refresh_token)

            # Find the token in database
            db_token = (
                db.query(RefreshToken)
                .filter(RefreshToken.token_hash == token_hash)
                .first()
            )

            if not db_token:
                print(
                    f"[REFRESH SERVICE] Token not found in DB. Hash: {token_hash[:20]}..."
                )
                # Token not found - might be reuse attack
                # Revoke entire family as a security measure
                RefreshTokenService.revoke_token_family(db, family, "reuse_detected")
                return None, None, None, None

            # Check if token is revoked
            if db_token.is_revoked:
                print(
                    f"[REFRESH SERVICE] Token is revoked. Reason: {db_token.revoke_reason}"
                )
                return None, None, None, None

            # Check if token is expired (double check)
            if db_token.expires_at < datetime.now(timezone.utc):
                print(
                    f"[REFRESH SERVICE] Token expired. Expires at: {db_token.expires_at}, Now: {datetime.now(timezone.utc)}"
                )
                return None, None, None, None

            # Token is valid - rotate it
            # First, revoke the old token
            db_token.is_revoked = True
            db_token.revoked_at = datetime.now(timezone.utc)
            db_token.revoke_reason = "rotated"
            db_token.last_used_at = datetime.now(timezone.utc)

            # Create new tokens
            from app.services.user_service import UserService

            # Generate new access token
            access_token = UserService.create_access_token(user_id)

            # Generate new refresh token with same family
            new_refresh_token, _, new_expiry = (
                RefreshTokenService.create_refresh_token_with_family(
                    db, user_id, family, device_info
                )
            )

            db.commit()

            return access_token, new_refresh_token, family, new_expiry

        except JWTError as e:
            # Invalid token - could be tampering
            print(f"[REFRESH SERVICE] JWT Error: {str(e)}")
            return None, None, None, None

    @staticmethod
    def create_refresh_token_with_family(
        db: Session, user_id: str, family: str, device_info: Optional[dict] = None
    ) -> Tuple[str, str, datetime]:
        """Create a refresh token with a specific family (for rotation)."""
        # Create token data
        token_data = RefreshTokenData(
            user_id=user_id,
            family=family,
            device_id=device_info.get("device_id") if device_info else None,
        )

        # Set expiration
        expires_delta = timedelta(days=RefreshTokenService.REFRESH_TOKEN_EXPIRE_DAYS)
        expire = datetime.now(timezone.utc) + expires_delta

        # Create JWT token
        to_encode = {
            **token_data.model_dump(),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),
        }

        refresh_token = jwt.encode(
            to_encode,
            RefreshTokenService.REFRESH_SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        # Hash token for storage
        token_hash = RefreshTokenService._hash_token(refresh_token)

        # Store in database
        db_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            family=family,
            device_name=device_info.get("device_name") if device_info else None,
            device_type=device_info.get("device_type") if device_info else None,
            browser=device_info.get("browser") if device_info else None,
            ip_address=device_info.get("ip_address") if device_info else None,
            expires_at=expire,
        )

        db.add(db_token)

        return refresh_token, family, expire

    @staticmethod
    def revoke_token(db: Session, token_hash: str, reason: str = "user_logout"):
        """Revoke a specific refresh token."""
        db_token = (
            db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        )

        if db_token and not db_token.is_revoked:
            db_token.is_revoked = True
            db_token.revoked_at = datetime.now(timezone.utc)
            db_token.revoke_reason = reason
            db.commit()

    @staticmethod
    def revoke_token_family(db: Session, family: str, reason: str = "security"):
        """Revoke all tokens in a family (security measure)."""
        db.query(RefreshToken).filter(
            and_(RefreshToken.family == family, RefreshToken.is_revoked == False)
        ).update(
            {
                "is_revoked": True,
                "revoked_at": datetime.now(timezone.utc),
                "revoke_reason": reason,
            }
        )
        db.commit()

    @staticmethod
    def revoke_all_user_tokens(db: Session, user_id: str, reason: str = "logout_all"):
        """Revoke all refresh tokens for a user."""
        db.query(RefreshToken).filter(
            and_(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
        ).update(
            {
                "is_revoked": True,
                "revoked_at": datetime.now(timezone.utc),
                "revoke_reason": reason,
            }
        )
        db.commit()

    @staticmethod
    def get_user_sessions(db: Session, user_id: str) -> List[SessionInfo]:
        """Get all active sessions for a user."""
        # Get all non-revoked, non-expired tokens
        tokens = (
            db.query(RefreshToken)
            .filter(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > datetime.now(timezone.utc),
                )
            )
            .order_by(RefreshToken.last_used_at.desc().nullsfirst())
            .all()
        )

        # Group by family (each family represents a session)
        families_seen = set()
        sessions = []

        for token in tokens:
            if token.family not in families_seen:
                families_seen.add(token.family)
                sessions.append(
                    SessionInfo(
                        id=token.family,  # Use family as session ID
                        device_name=token.device_name,
                        device_type=token.device_type,
                        browser=token.browser,
                        ip_address=token.ip_address,
                        last_active=token.last_used_at,
                        created_at=token.created_at,
                        is_current=False,  # Will be set by the endpoint
                    )
                )

        return sessions

    @staticmethod
    def cleanup_expired_tokens(db: Session) -> int:
        """Remove expired tokens from database. Returns count of deleted tokens."""
        result = (
            db.query(RefreshToken)
            .filter(RefreshToken.expires_at < datetime.now(timezone.utc))
            .delete()
        )
        db.commit()
        return result
