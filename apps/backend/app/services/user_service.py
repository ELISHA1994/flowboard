from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

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
