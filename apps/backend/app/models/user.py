from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime

class UserBase(BaseModel):
    """Base user model with common attributes"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    """Model for user registration"""
    password: str = Field(..., min_length=6)

class UserResponse(UserBase):
    """Model for user response (excludes password)"""
    id: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    """Model for JWT token response"""
    access_token: str
    token_type: str