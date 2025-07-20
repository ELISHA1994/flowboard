from fastapi import APIRouter, HTTPException, status, Query, Depends, BackgroundTasks
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from app.db.database import get_db
from app.db.models import (
    Task as TaskModel, TaskStatus, TaskPriority, User as UserModel,
    Project, ProjectRole, TaskShare, User
)
from app.models.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskTimeUpdate,
    TaskCategoryUpdate, TaskTagUpdate, TaskDependencyResponse,
    TaskShareCreate, TaskShareResponse, RecurrenceConfig
)
from app.core.middleware.jwt_auth_backend import get_current_active_user
from app.services.task_service import TaskService
from app.services.category_service import CategoryService
from app.services.tag_service import TagService
from app.services.webhook_service import WebhookService, WebhookEvent
from app.services.task_dependency_service import TaskDependencyService
from app.services.recurrence_service import RecurrenceService
from app.services.calendar_service import CalendarService
from app.services.notification_service import NotificationService

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
        "project_id": task.project_id,
        "assigned_to_id": task.assigned_to_id,
        "completed_at": task.completed_at,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "parent_task_id": task.parent_task_id,
        "categories": [{"id": c.id, "name": c.name, "color": c.color} for c in task.categories],
        "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in task.tags],
        "subtasks": [],
        "dependencies": [],
        "dependents": [],
        "project": None,
        "assigned_to": None,
        # Recurrence fields
        "is_recurring": task.is_recurring if hasattr(task, 'is_recurring') else False,
        "recurrence_pattern": task.recurrence_pattern if hasattr(task, 'recurrence_pattern') else None,
        "recurrence_interval": task.recurrence_interval if hasattr(task, 'recurrence_interval') else None,
        "recurrence_days_of_week": task.recurrence_days_of_week if hasattr(task, 'recurrence_days_of_week') else None,
        "recurrence_day_of_month": task.recurrence_day_of_month if hasattr(task, 'recurrence_day_of_month') else None,
        "recurrence_month_of_year": task.recurrence_month_of_year if hasattr(task, 'recurrence_month_of_year') else None,
        "recurrence_end_date": task.recurrence_end_date if hasattr(task, 'recurrence_end_date') else None,
        "recurrence_count": task.recurrence_count if hasattr(task, 'recurrence_count') else None,
        "recurrence_parent_id": task.recurrence_parent_id if hasattr(task, 'recurrence_parent_id') else None
    }
    
    # Include project info if available
    if task.project_id and hasattr(task, 'project') and task.project:
        response["project"] = {
            "id": task.project.id,
            "name": task.project.name,
            "description": task.project.description
        }
    
    # Include assigned_to user info if available
    if task.assigned_to_id and hasattr(task, 'assigned_to') and task.assigned_to:
        response["assigned_to"] = {
            "id": task.assigned_to.id,
            "username": task.assigned_to.username,
            "email": task.assigned_to.email
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
    background_tasks: BackgroundTasks,
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
    
    # Validate project permissions if project_id is specified
    if task_data.project_id:
        project = db.query(Project).filter(Project.id == task_data.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id '{task_data.project_id}' not found"
            )
        
        # Check if user has permission to create tasks in this project
        if not project.has_permission(current_user.id, ProjectRole.MEMBER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create tasks in this project"
            )
    
    # Validate assigned_to_id if specified
    if task_data.assigned_to_id:
        # If task is in a project, ensure assigned user is a project member
        if task_data.project_id:
            assigned_user_role = project.get_member_role(task_data.assigned_to_id)
            if not assigned_user_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User '{task_data.assigned_to_id}' is not a member of this project"
                )
        else:
            # For personal tasks, verify the assigned user exists
            assigned_user = db.query(User).filter(User.id == task_data.assigned_to_id).first()
            if not assigned_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id '{task_data.assigned_to_id}' not found"
                )
    
    # Check if this is a recurring task
    if task_data.recurrence:
        # Use RecurrenceService to create task with recurrence
        task_dict = {
            "title": task_data.title,
            "description": task_data.description,
            "status": task_data.status,
            "priority": task_data.priority,
            "due_date": task_data.due_date,
            "start_date": task_data.start_date,
            "estimated_hours": task_data.estimated_hours,
            "position": task_data.position,
            "parent_task_id": task_data.parent_task_id,
            "project_id": task_data.project_id,
            "assigned_to_id": task_data.assigned_to_id,
            "actual_hours": 0.0
        }
        db_task = RecurrenceService.create_task_with_recurrence(
            db, task_dict, task_data.recurrence, current_user.id
        )
    else:
        # Create regular task
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
            project_id=task_data.project_id,
            assigned_to_id=task_data.assigned_to_id,
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
    
    # Trigger webhook for task creation
    task_data_for_webhook = format_task_response(db_task)
    WebhookService.trigger_webhook(
        db,
        WebhookEvent.TASK_CREATED,
        task_data_for_webhook,
        user_id=current_user.id,
        project_id=db_task.project_id
    )
    
    # Send notification if task was assigned to someone else
    if db_task.assigned_to_id and db_task.assigned_to_id != current_user.id:
        NotificationService.notify_task_assigned(db, db_task, current_user)
    
    # Create due date reminders if task has a due date
    if db_task.due_date:
        NotificationService.create_due_date_reminders(db, db_task)
    
    # Sync with calendar integrations in background
    async def sync_task_to_calendars():
        integrations = CalendarService.get_user_integrations(db, current_user.id)
        for integration in integrations:
            try:
                await CalendarService.sync_task(db, db_task, integration, "create")
            except Exception as e:
                # Log error but don't fail the request
                pass
    
    background_tasks.add_task(sync_task_to_calendars)
    
    # Format response with all relationships
    return task_data_for_webhook

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str, 
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve a task by ID"""
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    # Check if user has access to the task
    if task.user_id != current_user.id:
        # If task belongs to a project, check project permissions
        if task.project_id:
            project = db.query(Project).filter(Project.id == task.project_id).first()
            if not project or not project.has_permission(current_user.id, ProjectRole.VIEWER):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this task"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this task"
            )
    
    return format_task_response(task)

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str, 
    task_update: TaskUpdate,
    background_tasks: BackgroundTasks,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a task"""
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    # Check if user has permission to update the task
    if task.user_id != current_user.id:
        # If task belongs to a project, check project permissions
        if task.project_id:
            project = db.query(Project).filter(Project.id == task.project_id).first()
            if not project or not project.has_permission(current_user.id, ProjectRole.MEMBER):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to update this task"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this task"
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
    
    # Handle project update
    if 'project_id' in update_data:
        if update_data['project_id'] != task.project_id:
            # If changing project, verify permissions for both old and new projects
            if task.project_id:
                old_project = db.query(Project).filter(Project.id == task.project_id).first()
                if old_project and not old_project.has_permission(current_user.id, ProjectRole.MEMBER):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have permission to remove tasks from the current project"
                    )
            
            if update_data['project_id']:
                new_project = db.query(Project).filter(Project.id == update_data['project_id']).first()
                if not new_project:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Project with id '{update_data['project_id']}' not found"
                    )
                if not new_project.has_permission(current_user.id, ProjectRole.MEMBER):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have permission to add tasks to this project"
                    )
    
    # Handle assigned_to_id update
    if 'assigned_to_id' in update_data:
        if update_data['assigned_to_id']:
            # If task is in a project, ensure assigned user is a project member
            if task.project_id:
                project = db.query(Project).filter(Project.id == task.project_id).first()
                if project:
                    assigned_user_role = project.get_member_role(update_data['assigned_to_id'])
                    if not assigned_user_role:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"User '{update_data['assigned_to_id']}' is not a member of this project"
                        )
            else:
                # For personal tasks, verify the assigned user exists
                assigned_user = db.query(User).filter(User.id == update_data['assigned_to_id']).first()
                if not assigned_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"User with id '{update_data['assigned_to_id']}' not found"
                    )
    
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
    
    # Handle recurrence update
    if 'recurrence' in update_data:
        if update_data['recurrence']:
            recurrence_config = RecurrenceConfig(**update_data['recurrence'])
            RecurrenceService.update_recurrence(db, task, recurrence_config)
        else:
            # Remove recurrence if set to None
            RecurrenceService.delete_recurrence(db, task, delete_instances=False)
        update_data.pop('recurrence')
    
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    # If the task status changed and it has a parent, update parent status
    if 'status' in update_data and task.parent_task_id:
        parent_task = db.query(TaskModel).filter(TaskModel.id == task.parent_task_id).first()
        if parent_task:
            TaskDependencyService.update_parent_task_status(db, parent_task)
    
    # Trigger webhook for task update
    task_data_for_webhook = format_task_response(task)
    WebhookService.trigger_webhook(
        db,
        WebhookEvent.TASK_UPDATED,
        task_data_for_webhook,
        user_id=current_user.id,
        project_id=task.project_id
    )
    
    # Check if task was completed
    if 'status' in update_data and update_data['status'] == TaskStatus.DONE:
        WebhookService.trigger_webhook(
            db,
            WebhookEvent.TASK_COMPLETED,
            task_data_for_webhook,
            user_id=current_user.id,
            project_id=task.project_id
        )
    
    # Send notification if task was assigned
    if 'assigned_to_id' in update_data and task.assigned_to_id and task.assigned_to_id != current_user.id:
        NotificationService.notify_task_assigned(db, task, current_user)
    
    # Sync with calendar integrations in background
    async def sync_task_to_calendars():
        integrations = CalendarService.get_user_integrations(db, current_user.id)
        for integration in integrations:
            try:
                await CalendarService.sync_task(db, task, integration, "update")
            except Exception as e:
                # Log error but don't fail the request
                pass
    
    background_tasks.add_task(sync_task_to_calendars)
    
    return task_data_for_webhook

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a task"""
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    # Check if user has permission to delete the task
    if task.user_id != current_user.id:
        # If task belongs to a project, check project permissions
        if task.project_id:
            project = db.query(Project).filter(Project.id == task.project_id).first()
            if not project or not project.has_permission(current_user.id, ProjectRole.ADMIN):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this task"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this task"
            )
    
    # Prepare task data for webhook before deletion
    task_data_for_webhook = format_task_response(task)
    project_id = task.project_id
    
    # Sync with calendar integrations in background (delete events)
    async def sync_task_deletion_to_calendars():
        integrations = CalendarService.get_user_integrations(db, current_user.id)
        for integration in integrations:
            try:
                await CalendarService.sync_task(db, task, integration, "delete")
            except Exception as e:
                # Log error but don't fail the request
                pass
    
    background_tasks.add_task(sync_task_deletion_to_calendars)
    
    db.delete(task)
    db.commit()
    
    # Trigger webhook for task deletion
    WebhookService.trigger_webhook(
        db,
        WebhookEvent.TASK_DELETED,
        task_data_for_webhook,
        user_id=current_user.id,
        project_id=project_id
    )

@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    task_status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    due_before: Optional[datetime] = Query(None, description="Filter tasks due before this date"),
    due_after: Optional[datetime] = Query(None, description="Filter tasks due after this date"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    tag_name: Optional[str] = Query(None, description="Filter by tag name"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    assigned_to_id: Optional[str] = Query(None, description="Filter by assigned user ID"),
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
    if project_id:
        # Verify user has access to the project
        project = db.query(Project).filter(Project.id == project_id).first()
        if project and project.has_permission(current_user.id, ProjectRole.VIEWER):
            query = query.filter(TaskModel.project_id == project_id)
        else:
            # Return empty list if user doesn't have access
            return []
    if assigned_to_id:
        query = query.filter(TaskModel.assigned_to_id == assigned_to_id)
    
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


@router.get("/project/{project_id}", response_model=List[TaskResponse])
async def get_project_tasks(
    project_id: str,
    task_status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    include_subtasks: bool = Query(False, description="Include subtasks in response"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all tasks for a specific project"""
    # Verify user has access to the project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id '{project_id}' not found"
        )
    
    if not project.has_permission(current_user.id, ProjectRole.VIEWER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view tasks in this project"
        )
    
    # Build query
    query = db.query(TaskModel).filter(TaskModel.project_id == project_id)
    
    # Apply filters
    if task_status:
        query = query.filter(TaskModel.status == task_status)
    if priority:
        query = query.filter(TaskModel.priority == priority)
    
    # Order by position by default
    query = query.order_by(TaskModel.position)
    
    tasks = query.all()
    
    return [format_task_response(task, include_subtasks=include_subtasks) for task in tasks]


# Task sharing endpoints
@router.post("/{task_id}/share", response_model=TaskShareResponse)
async def share_task(
    task_id: str,
    share_data: TaskShareCreate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Share a task with another user"""
    # Verify task exists and user has permission to share it
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    # Check if user can share this task
    can_share = False
    if task.user_id == current_user.id:
        can_share = True
    elif task.project_id:
        project = db.query(Project).filter(Project.id == task.project_id).first()
        if project and project.has_permission(current_user.id, ProjectRole.MEMBER):
            can_share = True
    
    if not can_share:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to share this task"
        )
    
    # Verify the user to share with exists
    shared_with_user = db.query(User).filter(User.id == share_data.shared_with_id).first()
    if not shared_with_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{share_data.shared_with_id}' not found"
        )
    
    # Check if task is already shared with this user
    existing_share = db.query(TaskShare).filter(
        TaskShare.task_id == task_id,
        TaskShare.shared_with_id == share_data.shared_with_id
    ).first()
    
    if existing_share:
        # Update existing share
        existing_share.permission = share_data.permission
        existing_share.expires_at = share_data.expires_at
        db.commit()
        db.refresh(existing_share)
        share = existing_share
    else:
        # Create new share
        share = TaskShare(
            id=str(uuid.uuid4()),
            task_id=task_id,
            shared_by_id=current_user.id,
            shared_with_id=share_data.shared_with_id,
            permission=share_data.permission,
            expires_at=share_data.expires_at
        )
        db.add(share)
        db.commit()
        db.refresh(share)
    
    # Return formatted response
    return {
        "id": share.id,
        "task_id": share.task_id,
        "shared_by_id": share.shared_by_id,
        "shared_with_id": share.shared_with_id,
        "permission": share.permission,
        "created_at": share.created_at,
        "expires_at": share.expires_at,
        "task": {
            "id": task.id,
            "title": task.title,
            "description": task.description
        },
        "shared_by": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        },
        "shared_with": {
            "id": shared_with_user.id,
            "username": shared_with_user.username,
            "email": shared_with_user.email
        }
    }


@router.get("/shared/with-me", response_model=List[TaskShareResponse])
async def get_tasks_shared_with_me(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all tasks shared with the current user"""
    shares = db.query(TaskShare).filter(
        TaskShare.shared_with_id == current_user.id
    ).all()
    
    result = []
    for share in shares:
        # Skip expired shares
        if share.expires_at and share.expires_at < datetime.now(timezone.utc):
            continue
            
        task = share.task
        shared_by = share.shared_by
        
        result.append({
            "id": share.id,
            "task_id": share.task_id,
            "shared_by_id": share.shared_by_id,
            "shared_with_id": share.shared_with_id,
            "permission": share.permission,
            "created_at": share.created_at,
            "expires_at": share.expires_at,
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority
            },
            "shared_by": {
                "id": shared_by.id,
                "username": shared_by.username,
                "email": shared_by.email
            },
            "shared_with": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email
            }
        })
    
    return result


@router.delete("/{task_id}/share/{share_id}")
async def remove_task_share(
    task_id: str,
    share_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a task share"""
    share = db.query(TaskShare).filter(
        TaskShare.id == share_id,
        TaskShare.task_id == task_id
    ).first()
    
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task share not found"
        )
    
    # Only the person who shared or the task owner can remove the share
    task = share.task
    if share.shared_by_id != current_user.id and task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to remove this share"
        )
    
    db.delete(share)
    db.commit()
    
    return {"message": "Task share removed successfully"}


# Recurring task endpoints
@router.get("/{task_id}/recurrence/instances", response_model=List[TaskResponse])
async def get_recurring_task_instances(
    task_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all instances of a recurring task"""
    # Get the parent recurring task
    parent_task = db.query(TaskModel).filter(
        TaskModel.id == task_id
    ).first()
    
    if not parent_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    # Check if user has access to the task
    if parent_task.user_id != current_user.id:
        if parent_task.project_id:
            project = db.query(Project).filter(Project.id == parent_task.project_id).first()
            if not project or not project.has_permission(current_user.id, ProjectRole.VIEWER):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this task"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this task"
            )
    
    if not parent_task.is_recurring:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This is not a recurring task"
        )
    
    # Get all instances
    instances = db.query(TaskModel).filter(
        TaskModel.recurrence_parent_id == task_id
    ).order_by(TaskModel.start_date).all()
    
    # Include the parent task as well
    all_tasks = [parent_task] + instances
    
    return [format_task_response(task) for task in all_tasks]


@router.post("/{task_id}/recurrence/next-occurrence")
async def get_next_occurrence_date(
    task_id: str,
    reference_date: datetime = Query(None, description="Reference date to calculate from (defaults to now)"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calculate the next occurrence date for a recurring task"""
    task = db.query(TaskModel).filter(
        TaskModel.id == task_id,
        TaskModel.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    if not task.is_recurring:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This is not a recurring task"
        )
    
    # Use reference date or current date
    base_date = reference_date or datetime.now(timezone.utc)
    
    # Parse days of week if needed
    days_of_week = None
    if task.recurrence_days_of_week:
        days_of_week = [int(d) for d in task.recurrence_days_of_week.split(',')]
    
    next_date = RecurrenceService.calculate_next_occurrence(
        base_date=base_date,
        pattern=task.recurrence_pattern,
        interval=task.recurrence_interval or 1,
        days_of_week=days_of_week,
        day_of_month=task.recurrence_day_of_month,
        month_of_year=task.recurrence_month_of_year
    )
    
    if not next_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not calculate next occurrence date"
        )
    
    return {
        "next_occurrence": next_date,
        "pattern": task.recurrence_pattern,
        "interval": task.recurrence_interval
    }


@router.delete("/{task_id}/recurrence")
async def delete_task_recurrence(
    task_id: str,
    delete_instances: bool = Query(False, description="Also delete future instances"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove recurrence from a task"""
    task = db.query(TaskModel).filter(
        TaskModel.id == task_id,
        TaskModel.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found"
        )
    
    if not task.is_recurring:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This is not a recurring task"
        )
    
    RecurrenceService.delete_recurrence(db, task, delete_instances=delete_instances)
    db.commit()
    
    return {
        "message": "Recurrence removed successfully",
        "instances_deleted": delete_instances
    }
