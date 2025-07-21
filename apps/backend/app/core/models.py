from typing import Any, Optional

from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standard API response model"""

    status: str
    status_code: int
    message: str
    data: Optional[Any] = None
