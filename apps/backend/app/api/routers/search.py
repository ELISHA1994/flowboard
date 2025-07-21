"""
API endpoints for advanced search and filtering functionality.
"""

import json
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.middleware.jwt_auth_backend import get_current_user
from app.db.db_instance import get_db
from app.db.models import SavedSearch, TaskPriority, TaskStatus, User
from app.models.search import (BulkOperation, BulkOperationRequest,
                               SavedSearchCreate, SavedSearchResponse,
                               SavedSearchUpdate, SearchSuggestionResponse,
                               TaskSearchRequest)
from app.models.task import TaskResponse
from app.services.bulk_operations_service import BulkOperationsService
from app.services.search_service import (SearchService, TaskSearchFilter,
                                         TaskSearchQuery)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/tasks", response_model=Dict[str, Any])
async def search_tasks(
    search_request: TaskSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Perform advanced search on tasks with multiple filters and operators.

    - **text**: Search in task title and description
    - **filters**: Apply multiple filters with various operators
    - **sort_by**: Field to sort results by
    - **sort_order**: Sort direction (asc/desc)
    - **include_shared**: Include tasks shared with you
    - **include_assigned**: Include tasks assigned to you
    """
    # Build search query
    search_query = TaskSearchQuery()

    if search_request.text:
        search_query.set_text_search(search_request.text)

    # Convert Pydantic filters to service filters
    for filter in search_request.filters:
        service_filter = TaskSearchFilter(
            field=filter.field, operator=filter.operator, value=filter.value
        )
        search_query.add_filter(service_filter)

    search_query.set_sort(search_request.sort_by, search_request.sort_order)
    search_query.include_shared = search_request.include_shared
    search_query.include_assigned = search_request.include_assigned

    # Perform search
    tasks, total_count = SearchService.search_tasks(db, current_user.id, search_query)

    # Apply pagination
    start = search_request.skip
    end = start + search_request.limit
    paginated_tasks = tasks[start:end]

    # Convert to response model
    task_responses = [TaskResponse.model_validate(task) for task in paginated_tasks]

    return {
        "tasks": task_responses,
        "total": total_count,
        "skip": search_request.skip,
        "limit": search_request.limit,
    }


@router.get("/suggestions", response_model=SearchSuggestionResponse)
async def get_search_suggestions(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get search filter suggestions based on user's data.
    Returns available values for filters like categories, tags, assigned users, etc.
    """
    suggestions = SearchService.get_suggested_filters(db, current_user.id)

    return SearchSuggestionResponse(
        statuses=suggestions["statuses"],
        priorities=suggestions["priorities"],
        categories=suggestions["categories"],
        tags=suggestions["tags"],
        assigned_users=suggestions["assigned_users"],
        projects=suggestions["projects"],
    )


@router.post("/saved", response_model=SavedSearchResponse)
async def create_saved_search(
    search_data: SavedSearchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a saved search query for easy reuse."""
    # If setting as default, unset any existing default
    if search_data.is_default:
        db.query(SavedSearch).filter(
            SavedSearch.user_id == current_user.id, SavedSearch.is_default == True
        ).update({"is_default": False})

    # Create saved search
    saved_search = SavedSearch(
        user_id=current_user.id,
        name=search_data.name,
        description=search_data.description,
        search_query=search_data.search_query.model_dump_json(),
        is_default=search_data.is_default,
    )

    db.add(saved_search)
    db.commit()
    db.refresh(saved_search)

    # Convert for response
    return SavedSearchResponse(
        id=saved_search.id,
        user_id=saved_search.user_id,
        name=saved_search.name,
        description=saved_search.description,
        search_query=json.loads(saved_search.search_query),
        is_default=saved_search.is_default,
        created_at=saved_search.created_at,
        updated_at=saved_search.updated_at,
    )


@router.get("/saved", response_model=List[SavedSearchResponse])
async def get_saved_searches(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all saved searches for the current user."""
    saved_searches = (
        db.query(SavedSearch)
        .filter(SavedSearch.user_id == current_user.id)
        .order_by(SavedSearch.created_at.desc())
        .all()
    )

    return [
        SavedSearchResponse(
            id=search.id,
            user_id=search.user_id,
            name=search.name,
            description=search.description,
            search_query=json.loads(search.search_query),
            is_default=search.is_default,
            created_at=search.created_at,
            updated_at=search.updated_at,
        )
        for search in saved_searches
    ]


@router.get("/saved/{search_id}", response_model=SavedSearchResponse)
async def get_saved_search(
    search_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific saved search."""
    saved_search = (
        db.query(SavedSearch)
        .filter(SavedSearch.id == search_id, SavedSearch.user_id == current_user.id)
        .first()
    )

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found"
        )

    return SavedSearchResponse(
        id=saved_search.id,
        user_id=saved_search.user_id,
        name=saved_search.name,
        description=saved_search.description,
        search_query=json.loads(saved_search.search_query),
        is_default=saved_search.is_default,
        created_at=saved_search.created_at,
        updated_at=saved_search.updated_at,
    )


@router.put("/saved/{search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
    search_id: str,
    update_data: SavedSearchUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a saved search."""
    saved_search = (
        db.query(SavedSearch)
        .filter(SavedSearch.id == search_id, SavedSearch.user_id == current_user.id)
        .first()
    )

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found"
        )

    # Update fields
    if update_data.name is not None:
        saved_search.name = update_data.name
    if update_data.description is not None:
        saved_search.description = update_data.description
    if update_data.search_query is not None:
        saved_search.search_query = update_data.search_query.model_dump_json()
    if update_data.is_default is not None:
        # If setting as default, unset any existing default
        if update_data.is_default:
            db.query(SavedSearch).filter(
                SavedSearch.user_id == current_user.id,
                SavedSearch.is_default == True,
                SavedSearch.id != search_id,
            ).update({"is_default": False})
        saved_search.is_default = update_data.is_default

    db.commit()
    db.refresh(saved_search)

    return SavedSearchResponse(
        id=saved_search.id,
        user_id=saved_search.user_id,
        name=saved_search.name,
        description=saved_search.description,
        search_query=json.loads(saved_search.search_query),
        is_default=saved_search.is_default,
        created_at=saved_search.created_at,
        updated_at=saved_search.updated_at,
    )


@router.delete("/saved/{search_id}")
async def delete_saved_search(
    search_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a saved search."""
    saved_search = (
        db.query(SavedSearch)
        .filter(SavedSearch.id == search_id, SavedSearch.user_id == current_user.id)
        .first()
    )

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found"
        )

    db.delete(saved_search)
    db.commit()

    return {"message": "Saved search deleted successfully"}


@router.post("/bulk", response_model=Dict[str, Any])
async def bulk_operation(
    bulk_request: BulkOperationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Perform bulk operations on multiple tasks.

    Available operations:
    - **update_status**: Change status for multiple tasks
    - **update_priority**: Change priority for multiple tasks
    - **update_assigned_to**: Assign tasks to a user
    - **add_tags**: Add tags to multiple tasks
    - **remove_tags**: Remove tags from multiple tasks
    - **add_categories**: Add categories to multiple tasks
    - **remove_categories**: Remove categories from multiple tasks
    - **delete**: Delete multiple tasks
    - **move_to_project**: Move tasks to a project
    """
    operation = bulk_request.operation
    task_ids = bulk_request.task_ids
    value = bulk_request.value

    # Execute the appropriate operation
    if operation == BulkOperation.UPDATE_STATUS:
        if not value or value not in [s.value for s in TaskStatus]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status value: {value}",
            )
        result = BulkOperationsService.update_status(
            db, current_user.id, task_ids, TaskStatus(value)
        )

    elif operation == BulkOperation.UPDATE_PRIORITY:
        if not value or value not in [p.value for p in TaskPriority]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority value: {value}",
            )
        result = BulkOperationsService.update_priority(
            db, current_user.id, task_ids, TaskPriority(value)
        )

    elif operation == BulkOperation.UPDATE_ASSIGNED_TO:
        result = BulkOperationsService.update_assigned_to(
            db, current_user.id, task_ids, value
        )

    elif operation == BulkOperation.ADD_TAGS:
        if not isinstance(value, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Value must be a list of tag names",
            )
        result = BulkOperationsService.add_tags(db, current_user.id, task_ids, value)

    elif operation == BulkOperation.REMOVE_TAGS:
        if not isinstance(value, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Value must be a list of tag names",
            )
        result = BulkOperationsService.remove_tags(db, current_user.id, task_ids, value)

    elif operation == BulkOperation.ADD_CATEGORIES:
        if not isinstance(value, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Value must be a list of category IDs",
            )
        result = BulkOperationsService.add_categories(
            db, current_user.id, task_ids, value
        )

    elif operation == BulkOperation.REMOVE_CATEGORIES:
        if not isinstance(value, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Value must be a list of category IDs",
            )
        result = BulkOperationsService.remove_categories(
            db, current_user.id, task_ids, value
        )

    elif operation == BulkOperation.DELETE:
        result = BulkOperationsService.delete_tasks(db, current_user.id, task_ids)

    elif operation == BulkOperation.MOVE_TO_PROJECT:
        result = BulkOperationsService.move_to_project(
            db, current_user.id, task_ids, value
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation: {operation}",
        )

    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Operation failed"),
        )

    return result
