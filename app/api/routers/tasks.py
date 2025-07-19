from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from app.db.database import get_db
from app.db.models import Task as TaskModel, TaskStatus, TaskPriority, User as UserModel
from app.models.task import TaskCreate, TaskUpdate, TaskResponse, TaskTimeUpdate, TaskCategoryUpdate, TaskTagUpdate, TaskDependencyCreate, TaskDependencyResponse
from app.core.middleware.jwt_auth_backend import get_current_active_user
from app.services.task_service import TaskService
from app.services.category_service import CategoryService
from app.services.tag_service import TagService
from app.services.task_dependency_service import TaskDependencyService

router = APIRouter()


def format_task_response(task: TaskModel, include_subtasks: bool = False) -> dict:
    """Format task model for API response"""
    response = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date,
        "start_date": task.start_date,
        "estimated_hours": task.estimated_hours,
        "actual_hours": task.actual_hours,
        "position": task.position,
        "user_id": task.user_id,
        "completed_at": task.completed_at,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "parent_task_id": task.parent_task_id,
        "categories": [{"id": c.id, "name": c.name, "color": c.color} for c in task.categories],
        "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in task.tags],
        "subtasks": [],
        "dependencies": [],
        "dependents": []
    }
    
    # Include subtasks if requested
    if include_subtasks and hasattr(task, 'subtasks'):
        response["subtasks"] = [format_task_response(st) for st in task.subtasks]
    
    # Include dependencies
    if hasattr(task, 'dependencies'):
        response["dependencies"] = [
            {
                "id": dep.id,
                "task_id": dep.task_id,
                "depends_on_id": dep.depends_on_id,
                "created_at": dep.created_at,
                "depends_on": {
                    "id": dep.depends_on.id,
                    "title": dep.depends_on.title,
                    "status": dep.depends_on.status
                } if dep.depends_on else None
            }
            for dep in task.dependencies
        ]
    
    return response

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate, 
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new task for the current user"""
    # Check task limit
    if not TaskService.validate_task_limit(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task limit reached. Maximum {100} tasks allowed per user."
        )
    
    # Set position to be at the end if not specified
    if task_data.position == 0:
        max_position = db.query(TaskModel).filter(
            TaskModel.user_id == current_user.id
        ).count()
        task_data.position = max_position
    
    # Validate parent task if specified
    if task_data.parent_task_id:
        parent_task = db.query(TaskModel).filter(
            TaskModel.id == task_data.parent_task_id,
            TaskModel.user_id == current_user.id
        ).first()
        if not parent_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent task with id '{task_data.parent_task_id}' not found"
            )
    
    db_task = TaskModel(
        id=str(uuid.uuid4()),
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        due_date=task_data.due_date,
        start_date=task_data.start_date,
        estimated_hours=task_data.estimated_hours,
        position=task_data.position,
        parent_task_id=task_data.parent_task_id,
        user_id=current_user.id,
        actual_hours=0.0
    )
    db.add(db_task)
    db.flush()  # Flush to get the ID without committing
    
    # Handle categories
    if task_data.category_ids:
        for category_id in task_data.category_ids:
            CategoryService.add_category_to_task(db, db_task.id, category_id, current_user.id)
    
    # Handle tags
    if task_data.tag_names:
        TagService.set_task_tags(db, db_task.id, task_data.tag_names, current_user.id)
    
    # Handle dependencies
    if task_data.depends_on_ids:
        for depends_on_id in task_data.depends_on_ids:
            try:
                TaskDependencyService.create_dependency(
                    db, db_task.id, depends_on_id, current_user.id
                )
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
    
    db.commit()
    db.refresh(db_task)
    
    # Format response with all relationships
    return format_task_response(db_task)

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str, 
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve a task by ID (must belong to current user)"""
    task = db.query(TaskModel).filter(
        TaskModel.id == task_id,
        TaskModel.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    return format_task_response(task)

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str, 
    task_update: TaskUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a task (must belong to current user)"""
    task = db.query(TaskModel).filter(
        TaskModel.id == task_id,
        TaskModel.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    update_data = task_update.model_dump(exclude_unset=True)
    
    # Handle status change to DONE
    if 'status' in update_data and update_data['status'] == TaskStatus.DONE:
        if task.status != TaskStatus.DONE:
            task.completed_at = datetime.now(timezone.utc)
    elif 'status' in update_data and update_data['status'] != TaskStatus.DONE:
        # If changing from DONE to another status, clear completed_at
        if task.status == TaskStatus.DONE:
            task.completed_at = None
    
    # Handle categories update
    if 'category_ids' in update_data:
        # Clear existing categories
        task.categories = []
        db.flush()
        # Add new categories
        for category_id in update_data['category_ids']:
            CategoryService.add_category_to_task(db, task_id, category_id, current_user.id)
        update_data.pop('category_ids')
    
    # Handle tags update
    if 'tag_names' in update_data:
        TagService.set_task_tags(db, task_id, update_data['tag_names'], current_user.id)
        update_data.pop('tag_names')
    
    # Handle parent task update
    if 'parent_task_id' in update_data:
        try:
            TaskDependencyService.update_task_parent(
                db, task_id, update_data['parent_task_id'], current_user.id
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        update_data.pop('parent_task_id')
    
    # Handle dependencies update
    if 'depends_on_ids' in update_data:
        # Clear existing dependencies
        for dep in task.dependencies:
            db.delete(dep)
        db.flush()
        
        # Add new dependencies
        for depends_on_id in update_data['depends_on_ids']:
            try:
                TaskDependencyService.create_dependency(
                    db, task_id, depends_on_id, current_user.id
                )
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        update_data.pop('depends_on_ids')
    
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    # If the task status changed and it has a parent, update parent status
    if 'status' in update_data and task.parent_task_id:
        parent_task = db.query(TaskModel).filter(TaskModel.id == task.parent_task_id).first()
        if parent_task:
            TaskDependencyService.update_parent_task_status(db, parent_task)
    
    return format_task_response(task)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a task (must belong to current user)"""
    task = db.query(TaskModel).filter(
        TaskModel.id == task_id,
        TaskModel.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    db.delete(task)
    db.commit()

@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    task_status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    due_before: Optional[datetime] = Query(None, description="Filter tasks due before this date"),
    due_after: Optional[datetime] = Query(None, description="Filter tasks due after this date"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    tag_name: Optional[str] = Query(None, description="Filter by tag name"),
    sort_by: str = Query("position", description="Sort by: position, due_date, priority, created_at"),
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of tasks to return"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List tasks for the current user with optional filtering"""
    query = db.query(TaskModel).filter(TaskModel.user_id == current_user.id)
    
    # Apply filters
    if task_status:
        query = query.filter(TaskModel.status == task_status)
    if priority:
        query = query.filter(TaskModel.priority == priority)
    if due_before:
        query = query.filter(TaskModel.due_date <= due_before)
    if due_after:
        query = query.filter(TaskModel.due_date >= due_after)
    if category_id:
        query = query.join(TaskModel.categories).filter(
            TaskModel.categories.any(id=category_id)
        )
    if tag_name:
        tag_name_lower = tag_name.strip().lower()
        query = query.join(TaskModel.tags).filter(
            TaskModel.tags.any(name=tag_name_lower)
        )
    
    # Apply sorting
    if sort_by == "due_date":
        query = query.order_by(TaskModel.due_date.asc().nullslast())
    elif sort_by == "priority":
        # Order by priority (URGENT first, then HIGH, MEDIUM, LOW)
        priority_order = {
            TaskPriority.URGENT: 1,
            TaskPriority.HIGH: 2,
            TaskPriority.MEDIUM: 3,
            TaskPriority.LOW: 4
        }
        query = query.order_by(TaskModel.priority)
    elif sort_by == "created_at":
        query = query.order_by(TaskModel.created_at.desc())
    else:  # Default to position
        query = query.order_by(TaskModel.position)
    
    tasks = query.offset(skip).limit(limit).all()
    
    # Format response with categories and tags
    return [format_task_response(task) for task in tasks]

@router.post("/{task_id}/time", response_model=TaskResponse)
async def add_task_time(
    task_id: str,
    time_update: TaskTimeUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add time to a task's actual hours"""
    task = db.query(TaskModel).filter(
        TaskModel.id == task_id,
        TaskModel.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    task.actual_hours += time_update.hours_to_add
    db.commit()
    db.refresh(task)
    return format_task_response(task)

@router.get("/statistics/overview")
async def get_task_statistics(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get task statistics for the current user"""
    return TaskService.get_task_statistics(db, current_user.id)

@router.get("/overdue", response_model=List[TaskResponse])
async def get_overdue_tasks(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all overdue tasks for the current user"""
    tasks = TaskService.get_overdue_tasks(db, current_user.id)
    return [format_task_response(task) for task in tasks]

@router.get("/upcoming", response_model=List[TaskResponse])
async def get_upcoming_tasks(
    days: int = Query(7, ge=1, le=30, description="Number of days to look ahead"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get tasks due in the next N days"""
    tasks = TaskService.get_upcoming_tasks(db, current_user.id, days)
    return [format_task_response(task) for task in tasks]

@router.put("/{task_id}/position")
async def update_task_position(
    task_id: str,
    new_position: int = Query(..., ge=0, description="New position index"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update task position for manual ordering"""
    success = TaskService.update_task_positions(db, current_user.id, task_id, new_position)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    return {"message": "Task position updated successfully"}


@router.put("/{task_id}/categories", response_model=TaskResponse)
async def update_task_categories(
    task_id: str,
    category_update: TaskCategoryUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update task categories (replaces existing categories)"""
    task = db.query(TaskModel).filter(
        TaskModel.id == task_id,
        TaskModel.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    # Clear existing categories
    task.categories = []
    db.flush()
    
    # Add new categories
    for category_id in category_update.category_ids:
        CategoryService.add_category_to_task(db, task_id, category_id, current_user.id)
    
    db.commit()
    db.refresh(task)
    
    return format_task_response(task)


@router.put("/{task_id}/tags", response_model=TaskResponse)
async def update_task_tags(
    task_id: str,
    tag_update: TaskTagUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update task tags (replaces existing tags)"""
    task = db.query(TaskModel).filter(
        TaskModel.id == task_id,
        TaskModel.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    # Set new tags
    TagService.set_task_tags(db, task_id, tag_update.tag_names, current_user.id)
    
    db.refresh(task)
    
    return format_task_response(task)


@router.post("/{task_id}/tags", response_model=TaskResponse)
async def add_task_tags(
    task_id: str,
    tag_update: TaskTagUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add tags to a task (keeps existing tags)"""
    task = db.query(TaskModel).filter(
        TaskModel.id == task_id,
        TaskModel.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    # Add new tags
    TagService.add_tags_to_task(db, task_id, tag_update.tag_names, current_user.id)
    
    db.refresh(task)
    
    return format_task_response(task)


@router.delete("/{task_id}/tags", response_model=TaskResponse)
async def remove_task_tags(
    task_id: str,
    tag_update: TaskTagUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove specific tags from a task"""
    task = db.query(TaskModel).filter(
        TaskModel.id == task_id,
        TaskModel.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    # Remove tags
    TagService.remove_tags_from_task(db, task_id, tag_update.tag_names, current_user.id)
    
    db.refresh(task)
    
    return format_task_response(task)


# Subtask endpoints
@router.get("/{task_id}/subtasks", response_model=List[TaskResponse])
async def get_subtasks(
    task_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all subtasks of a task"""
    try:
        subtasks = TaskDependencyService.get_subtasks(db, task_id, current_user.id)
        return [format_task_response(task) for task in subtasks]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# Dependency endpoints
@router.post("/{task_id}/dependencies", response_model=TaskDependencyResponse)
async def create_task_dependency(
    task_id: str,
    depends_on_id: str = Query(..., description="ID of the task this task depends on"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a dependency between two tasks"""
    try:
        dependency = TaskDependencyService.create_dependency(
            db, task_id, depends_on_id, current_user.id
        )
        return {
            "id": dependency.id,
            "task_id": dependency.task_id,
            "depends_on_id": dependency.depends_on_id,
            "created_at": dependency.created_at,
            "depends_on": {
                "id": dependency.depends_on.id,
                "title": dependency.depends_on.title,
                "status": dependency.depends_on.status
            } if dependency.depends_on else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{task_id}/dependencies", response_model=List[TaskDependencyResponse])
async def get_task_dependencies(
    task_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all dependencies for a task"""
    try:
        dependencies = TaskDependencyService.get_task_dependencies(
            db, task_id, current_user.id
        )
        return [
            {
                "id": dep.id,
                "task_id": dep.task_id,
                "depends_on_id": dep.depends_on_id,
                "created_at": dep.created_at,
                "depends_on": {
                    "id": dep.depends_on.id,
                    "title": dep.depends_on.title,
                    "status": dep.depends_on.status
                } if dep.depends_on else None
            }
            for dep in dependencies
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{task_id}/dependencies/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_dependency(
    task_id: str,
    dependency_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a task dependency"""
    try:
        TaskDependencyService.delete_dependency(db, dependency_id, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{task_id}/can-complete")
async def check_can_complete_task(
    task_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check if a task can be completed based on its dependencies"""
    try:
        can_complete, incomplete_deps = TaskDependencyService.can_complete_task(
            db, task_id, current_user.id
        )
        return {
            "can_complete": can_complete,
            "incomplete_dependencies": incomplete_deps
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )