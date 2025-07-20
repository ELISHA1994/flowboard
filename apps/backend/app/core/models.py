from pydantic import BaseModel
from typing import Optional, Any

class APIResponse(BaseModel):
    """Standard API response model"""
    status: str
    status_code: int
    message: str
    data: Optional[Any] = None