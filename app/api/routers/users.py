from fastapi import APIRouter, Depends

from app.db.models import User as UserModel
from app.models.user import UserResponse
from app.core.middleware.jwt_auth_backend import get_current_active_user

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    """Get current user profile"""
    return current_user