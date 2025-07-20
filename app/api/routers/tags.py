from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User as UserModel
from app.models.tag import TagCreate, TagUpdate, TagResponse, TagWithTasks, BulkTagOperation
from app.core.middleware.jwt_auth_backend import get_current_active_user
from app.services.tag_service import TagService

router = APIRouter()


def format_tag_response(tag) -> dict:
    """Format tag model for API response"""
    return {
        "id": tag.id,
        "name": tag.name,
        "color": tag.color,
        "task_count": len(tag.tasks),
        "created_at": tag.created_at.isoformat() if tag.created_at else None
    }


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new tag for the current user"""
    db_tag = TagService.create_tag(db, current_user.id, tag_data)
    
    return format_tag_response(db_tag)


@router.post("/bulk", response_model=List[TagResponse])
async def create_tags_bulk(
    bulk_data: BulkTagOperation,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create multiple tags at once"""
    tags = TagService.get_or_create_tags(db, current_user.id, bulk_data.tag_names)
    
    return [format_tag_response(tag) for tag in tags]


@router.get("/", response_model=List[TagResponse])
async def list_tags(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all tags for the current user"""
    tags = TagService.get_user_tags(db, current_user.id)
    
    return [format_tag_response(tag) for tag in tags]


@router.get("/popular", response_model=List[dict])
async def get_popular_tags(
    limit: int = Query(10, ge=1, le=50, description="Number of tags to return"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get most used tags for the current user"""
    popular_tags = TagService.get_popular_tags(db, current_user.id, limit)
    
    # Format response
    return [
        {
            "id": item["tag"].id,
            "name": item["tag"].name,
            "color": item["tag"].color,
            "task_count": item["task_count"],
            "created_at": item["tag"].created_at.isoformat()
        }
        for item in popular_tags
    ]


@router.get("/{tag_id}", response_model=TagWithTasks)
async def get_tag(
    tag_id: str,
    include_tasks: bool = Query(False, description="Include associated tasks"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific tag by ID"""
    tag = TagService.get_tag(db, tag_id, current_user.id)
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id '{tag_id}' not found"
        )
    
    # Format response
    response_data = format_tag_response(tag)
    
    # Always include tasks field for TagWithTasks response model
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
            for task in tag.tasks
        ]
    
    return response_data


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: str,
    tag_update: TagUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a tag"""
    try:
        updated_tag = TagService.update_tag(db, tag_id, current_user.id, tag_update)
        
        if not updated_tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with id '{tag_id}' not found"
            )
        
        return format_tag_response(updated_tag)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a tag"""
    success = TagService.delete_tag(db, tag_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id '{tag_id}' not found"
        )