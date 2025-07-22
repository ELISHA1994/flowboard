from datetime import datetime, timedelta, timezone
from typing import List, Optional

from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.db.models import User as UserModel


class UserService:
    """Service layer for user-related business logic"""

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
        """Get user by email address"""
        return db.query(UserModel).filter(UserModel.email == email).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[UserModel]:
        """Get user by username"""
        return db.query(UserModel).filter(UserModel.username == username).first()

    @staticmethod
    def is_user_active(user: UserModel) -> bool:
        """Check if user account is active"""
        if not user.is_active:
            logger.info(f"User {user.username} is not active")
            return False
        return True

    @staticmethod
    def get_active_users_count(db: Session) -> int:
        """Get count of active users"""
        return db.query(UserModel).filter(UserModel.is_active == True).count()

    @staticmethod
    def get_recent_users(db: Session, days: int = 7) -> List[UserModel]:
        """Get users created in the last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return db.query(UserModel).filter(UserModel.created_at >= cutoff_date).all()

    @staticmethod
    def create_access_token(
        user_id: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token for a user"""
        to_encode = {"sub": user_id}

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update(
            {"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"}
        )

        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt
