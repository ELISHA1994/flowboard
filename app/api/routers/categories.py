from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User as UserModel
from app.models.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryWithTasks
from app.core.middleware.jwt_auth_backend import get_current_active_user
from app.services.category_service import CategoryService

router = APIRouter()


def format_category_response(category) -> dict:
    """Format category model for API response"""
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "color": category.color,
        "icon": category.icon,
        "is_active": category.is_active,
        "task_count": len(category.tasks),
        "created_at": category.created_at.isoformat() if category.created_at else None,
        "updated_at": category.updated_at.isoformat() if category.updated_at else None
    }


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new category for the current user"""
    try:
        db_category = CategoryService.create_category(db, current_user.id, category_data)
        return format_category_response(db_category)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[CategoryResponse])
async def list_categories(
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all categories for the current user"""
    categories = CategoryService.get_user_categories(db, current_user.id, include_inactive)
    
    return [format_category_response(category) for category in categories]


@router.get("/{category_id}", response_model=CategoryWithTasks)
async def get_category(
    category_id: str,
    include_tasks: bool = Query(False, description="Include associated tasks"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific category by ID"""
    category = CategoryService.get_category(db, category_id, current_user.id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id '{category_id}' not found"
        )
    
    # Format response
    response_data = format_category_response(category)
    
    # Always include tasks field for CategoryWithTasks response model
    response_data["tasks"] = []
    if include_tasks:
        response_data["tasks"] = [
            {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "due_date": task.due_date.isoformat() if task.due_date else None
            }
            for task in category.tasks
        ]
    
    return response_data


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    category_update: CategoryUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a category"""
    try:
        updated_category = CategoryService.update_category(
            db, category_id, current_user.id, category_update
        )
        
        if not updated_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id '{category_id}' not found"
            )
        
        return format_category_response(updated_category)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a category (soft delete)"""
    success = CategoryService.delete_category(db, category_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id '{category_id}' not found"
        )