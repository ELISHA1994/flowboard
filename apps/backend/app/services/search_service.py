"""
Service layer for advanced search and filtering operations.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session, Query
from sqlalchemy import or_
from enum import Enum

from app.db.models import (
    Task, TaskStatus, TaskPriority, User, Category, Tag,
    Project, ProjectRole, TaskShare
)
from app.core.config import settings
from app.services.cache_service import cached, cache_service


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


class TaskSearchFilter:
    """Represents a single search filter"""
    def __init__(
        self,
        field: str,
        operator: SearchOperator,
        value: Any = None
    ):
        self.field = field
        self.operator = operator
        self.value = value


class TaskSearchQuery:
    """Complex search query builder"""
    def __init__(self):
        self.filters: List[TaskSearchFilter] = []
        self.text_search: Optional[str] = None
        self.sort_by: str = "created_at"
        self.sort_order: str = "desc"
        self.include_shared: bool = True
        self.include_assigned: bool = True
        
    def add_filter(self, filter: TaskSearchFilter):
        """Add a filter to the search query"""
        self.filters.append(filter)
        
    def set_text_search(self, text: str):
        """Set text search query"""
        self.text_search = text.strip() if text else None
        
    def set_sort(self, field: str, order: str = "asc"):
        """Set sort parameters"""
        self.sort_by = field
        self.sort_order = order


class SearchService:
    """Service for handling advanced search operations"""
    
    # Mapping of user-friendly field names to database fields
    FIELD_MAPPING = {
        "title": Task.title,
        "description": Task.description,
        "status": Task.status,
        "priority": Task.priority,
        "due_date": Task.due_date,
        "start_date": Task.start_date,
        "completed_at": Task.completed_at,
        "created_at": Task.created_at,
        "updated_at": Task.updated_at,
        "estimated_hours": Task.estimated_hours,
        "actual_hours": Task.actual_hours,
        "assigned_to": Task.assigned_to_id,
        "project": Task.project_id,
        "is_recurring": Task.is_recurring,
        "has_subtasks": Task.parent_task_id,
    }
    
    @staticmethod
    def search_tasks(
        db: Session,
        user_id: str,
        search_query: TaskSearchQuery
    ) -> Tuple[List[Task], int]:
        """
        Perform advanced search on tasks.
        Returns tuple of (tasks, total_count)
        """
        # Base query - user's own tasks
        base_query = db.query(Task).filter(Task.user_id == user_id)
        
        # Include assigned tasks if requested
        if search_query.include_assigned:
            assigned_query = db.query(Task).filter(Task.assigned_to_id == user_id)
            base_query = base_query.union(assigned_query)
        
        # Include shared tasks if requested
        if search_query.include_shared:
            shared_task_ids = db.query(TaskShare.task_id).filter(
                TaskShare.shared_with_id == user_id,
                or_(
                    TaskShare.expires_at == None,
                    TaskShare.expires_at > datetime.now(timezone.utc)
                )
            ).subquery()
            
            shared_query = db.query(Task).filter(Task.id.in_(shared_task_ids))
            base_query = base_query.union(shared_query)
        
        # Apply text search if provided
        if search_query.text_search:
            text_filter = or_(
                Task.title.ilike(f"%{search_query.text_search}%"),
                Task.description.ilike(f"%{search_query.text_search}%")
            )
            base_query = base_query.filter(text_filter)
        
        # Apply filters
        for filter in search_query.filters:
            base_query = SearchService._apply_filter(base_query, filter)
        
        # Get total count before pagination
        total_count = base_query.count()
        
        # Apply sorting
        base_query = SearchService._apply_sort(base_query, search_query.sort_by, search_query.sort_order)
        
        tasks = base_query.all()
        
        return tasks, total_count
    
    @staticmethod
    def _apply_filter(query: Query, filter: TaskSearchFilter) -> Query:
        """Apply a single filter to the query"""
        field = SearchService.FIELD_MAPPING.get(filter.field)
        if not field:
            return query
            
        operator = filter.operator
        value = filter.value
        
        if operator == SearchOperator.EQUALS:
            return query.filter(field == value)
        elif operator == SearchOperator.NOT_EQUALS:
            return query.filter(field != value)
        elif operator == SearchOperator.GREATER_THAN:
            return query.filter(field > value)
        elif operator == SearchOperator.GREATER_THAN_OR_EQUAL:
            return query.filter(field >= value)
        elif operator == SearchOperator.LESS_THAN:
            return query.filter(field < value)
        elif operator == SearchOperator.LESS_THAN_OR_EQUAL:
            return query.filter(field <= value)
        elif operator == SearchOperator.CONTAINS:
            return query.filter(field.ilike(f"%{value}%"))
        elif operator == SearchOperator.NOT_CONTAINS:
            return query.filter(~field.ilike(f"%{value}%"))
        elif operator == SearchOperator.IN:
            return query.filter(field.in_(value))
        elif operator == SearchOperator.NOT_IN:
            return query.filter(~field.in_(value))
        elif operator == SearchOperator.IS_NULL:
            return query.filter(field == None)
        elif operator == SearchOperator.IS_NOT_NULL:
            return query.filter(field != None)
        
        return query
    
    @staticmethod
    def _apply_sort(query: Query, sort_by: str, sort_order: str) -> Query:
        """Apply sorting to the query"""
        field = SearchService.FIELD_MAPPING.get(sort_by)
        if not field:
            field = Task.created_at  # Default
            
        if sort_order.lower() == "desc":
            return query.order_by(field.desc())
        else:
            return query.order_by(field.asc())
    
    @staticmethod
    def search_by_category(
        db: Session,
        user_id: str,
        category_ids: List[str]
    ) -> List[Task]:
        """Search tasks by categories"""
        return db.query(Task).filter(
            Task.user_id == user_id,
            Task.categories.any(Category.id.in_(category_ids))
        ).all()
    
    @staticmethod
    def search_by_tags(
        db: Session,
        user_id: str,
        tag_names: List[str]
    ) -> List[Task]:
        """Search tasks by tag names"""
        # Convert to lowercase for case-insensitive search
        tag_names_lower = [name.lower() for name in tag_names]
        
        return db.query(Task).filter(
            Task.user_id == user_id,
            Task.tags.any(Tag.name.in_(tag_names_lower))
        ).all()
    
    @staticmethod
    def search_in_project(
        db: Session,
        user_id: str,
        project_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Task]:
        """Search tasks within a specific project"""
        # Verify user has access to project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.has_permission(user_id, ProjectRole.VIEWER):
            return []
        
        query = db.query(Task).filter(Task.project_id == project_id)
        
        # Apply additional filters if provided
        if filters:
            if "status" in filters:
                query = query.filter(Task.status == filters["status"])
            if "priority" in filters:
                query = query.filter(Task.priority == filters["priority"])
            if "assigned_to_id" in filters:
                query = query.filter(Task.assigned_to_id == filters["assigned_to_id"])
        
        return query.all()
    
    @staticmethod
    @cached(prefix=settings.CACHE_PREFIX_SEARCH, ttl=600)  # Cache for 10 minutes
    def get_suggested_filters(
        db: Session,
        user_id: str
    ) -> Dict[str, List[Any]]:
        """Get suggested filter values based on user's tasks"""
        # Get all accessible task IDs
        user_tasks = db.query(Task.id).filter(Task.user_id == user_id)
        assigned_tasks = db.query(Task.id).filter(Task.assigned_to_id == user_id)
        shared_tasks = db.query(TaskShare.task_id).filter(
            TaskShare.shared_with_id == user_id
        )
        
        all_task_ids = user_tasks.union(assigned_tasks).union(shared_tasks).subquery()
        
        # Get unique values for filters
        suggestions = {
            "statuses": [status.value for status in TaskStatus],
            "priorities": [priority.value for priority in TaskPriority],
            "categories": [],
            "tags": [],
            "assigned_users": [],
            "projects": []
        }
        
        # Get user's categories
        categories = db.query(Category).filter(Category.user_id == user_id).all()
        suggestions["categories"] = [
            {"id": cat.id, "name": cat.name, "color": cat.color}
            for cat in categories
        ]
        
        # Get user's tags
        tags = db.query(Tag).filter(Tag.user_id == user_id).all()
        suggestions["tags"] = [
            {"id": tag.id, "name": tag.name, "color": tag.color}
            for tag in tags
        ]
        
        # Get assigned users from tasks
        assigned_user_ids = db.query(Task.assigned_to_id).filter(
            Task.id.in_(all_task_ids),
            Task.assigned_to_id != None
        ).distinct().all()
        
        if assigned_user_ids:
            users = db.query(User).filter(
                User.id.in_([uid[0] for uid in assigned_user_ids])
            ).all()
            suggestions["assigned_users"] = [
                {"id": user.id, "username": user.username}
                for user in users
            ]
        
        # Get accessible projects
        user_projects = db.query(Project).filter(Project.owner_id == user_id)
        member_projects = db.query(Project).join(Project.members).filter(
            Project.members.any(user_id=user_id)
        )
        
        all_projects = user_projects.union(member_projects).all()
        suggestions["projects"] = [
            {"id": proj.id, "name": proj.name}
            for proj in all_projects
        ]
        
        return suggestions