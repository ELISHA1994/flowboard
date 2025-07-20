"""
Pydantic models for search and filtering functionality.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SearchOperator(str, Enum):
    """Search operators for filter conditions"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class SearchFilter(BaseModel):
    """Individual search filter"""
    field: str = Field(..., description="Field to filter on")
    operator: SearchOperator = Field(..., description="Filter operator")
    value: Optional[Any] = Field(None, description="Filter value")
    
    @field_validator('field')
    def validate_field(cls, v: str) -> str:
        allowed_fields = {
            "title", "description", "status", "priority", 
            "due_date", "start_date", "completed_at", "created_at",
            "updated_at", "estimated_hours", "actual_hours",
            "assigned_to", "project", "is_recurring", "has_subtasks"
        }
        if v not in allowed_fields:
            raise ValueError(f"Invalid field: {v}. Allowed fields: {allowed_fields}")
        return v


class TaskSearchRequest(BaseModel):
    """Request model for task search"""
    text: Optional[str] = Field(None, description="Text to search in title and description")
    filters: List[SearchFilter] = Field(default=[], description="List of filters to apply")
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")
    include_shared: bool = Field(default=True, description="Include tasks shared with user")
    include_assigned: bool = Field(default=True, description="Include tasks assigned to user")
    skip: int = Field(default=0, ge=0, description="Number of tasks to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Number of tasks to return")
    
    @field_validator('sort_order')
    def validate_sort_order(cls, v: str) -> str:
        if v.lower() not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v.lower()


class SavedSearchCreate(BaseModel):
    """Model for creating a saved search"""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the saved search")
    description: Optional[str] = Field(None, max_length=500, description="Description of the search")
    search_query: TaskSearchRequest = Field(..., description="The search query to save")
    is_default: bool = Field(default=False, description="Set as default search view")


class SavedSearchUpdate(BaseModel):
    """Model for updating a saved search"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    search_query: Optional[TaskSearchRequest] = None
    is_default: Optional[bool] = None


class SavedSearchResponse(BaseModel):
    """Response model for saved search"""
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    search_query: Dict[str, Any]
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class BulkOperation(str, Enum):
    """Bulk operation types"""
    UPDATE_STATUS = "update_status"
    UPDATE_PRIORITY = "update_priority"
    UPDATE_ASSIGNED_TO = "update_assigned_to"
    ADD_TAGS = "add_tags"
    REMOVE_TAGS = "remove_tags"
    ADD_CATEGORIES = "add_categories"
    REMOVE_CATEGORIES = "remove_categories"
    DELETE = "delete"
    ARCHIVE = "archive"
    MOVE_TO_PROJECT = "move_to_project"


class BulkOperationRequest(BaseModel):
    """Request model for bulk operations"""
    task_ids: List[str] = Field(..., min_items=1, description="List of task IDs to operate on")
    operation: BulkOperation = Field(..., description="Operation to perform")
    value: Optional[Any] = Field(None, description="Value for the operation")
    
    @field_validator('task_ids')
    def validate_task_ids(cls, v: List[str]) -> List[str]:
        if len(v) > 100:
            raise ValueError("Cannot perform bulk operations on more than 100 tasks at once")
        return v


class SearchSuggestionResponse(BaseModel):
    """Response model for search suggestions"""
    statuses: List[str]
    priorities: List[str]
    categories: List[Dict[str, Any]]
    tags: List[Dict[str, Any]]
    assigned_users: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]