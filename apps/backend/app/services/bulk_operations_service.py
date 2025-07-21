"""
Service layer for bulk operations on tasks.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db.models import (Category, Project, ProjectRole, Task, TaskPriority,
                           TaskStatus, User)
from app.services.tag_service import TagService


class BulkOperationsService:
    """Service for performing bulk operations on tasks"""

    @staticmethod
    def validate_task_access(
        db: Session, user_id: str, task_ids: List[str]
    ) -> List[Task]:
        """
        Validate that user has access to all tasks.
        Returns list of tasks user can access.
        """
        # Get tasks owned by user
        owned_tasks = (
            db.query(Task)
            .filter(and_(Task.id.in_(task_ids), Task.user_id == user_id))
            .all()
        )

        # Get tasks in projects where user has at least MEMBER role
        project_tasks = []
        remaining_ids = set(task_ids) - set([t.id for t in owned_tasks])

        if remaining_ids:
            tasks_with_projects = (
                db.query(Task)
                .filter(and_(Task.id.in_(remaining_ids), Task.project_id != None))
                .all()
            )

            for task in tasks_with_projects:
                project = task.project
                if project and project.has_permission(user_id, ProjectRole.MEMBER):
                    project_tasks.append(task)

        return owned_tasks + project_tasks

    @staticmethod
    def update_status(
        db: Session, user_id: str, task_ids: List[str], new_status: TaskStatus
    ) -> Dict[str, Any]:
        """Update status for multiple tasks"""
        accessible_tasks = BulkOperationsService.validate_task_access(
            db, user_id, task_ids
        )

        if not accessible_tasks:
            return {
                "success": False,
                "message": "No accessible tasks found",
                "updated_count": 0,
            }

        updated_count = 0
        for task in accessible_tasks:
            task.status = new_status
            # Handle completion timestamp
            if new_status == TaskStatus.DONE and not task.completed_at:
                from datetime import datetime, timezone

                task.completed_at = datetime.now(timezone.utc)
            elif new_status != TaskStatus.DONE:
                task.completed_at = None
            updated_count += 1

        db.commit()

        return {
            "success": True,
            "message": f"Updated status for {updated_count} tasks",
            "updated_count": updated_count,
            "inaccessible_count": len(task_ids) - updated_count,
        }

    @staticmethod
    def update_priority(
        db: Session, user_id: str, task_ids: List[str], new_priority: TaskPriority
    ) -> Dict[str, Any]:
        """Update priority for multiple tasks"""
        accessible_tasks = BulkOperationsService.validate_task_access(
            db, user_id, task_ids
        )

        if not accessible_tasks:
            return {
                "success": False,
                "message": "No accessible tasks found",
                "updated_count": 0,
            }

        updated_count = 0
        for task in accessible_tasks:
            task.priority = new_priority
            updated_count += 1

        db.commit()

        return {
            "success": True,
            "message": f"Updated priority for {updated_count} tasks",
            "updated_count": updated_count,
            "inaccessible_count": len(task_ids) - updated_count,
        }

    @staticmethod
    def update_assigned_to(
        db: Session, user_id: str, task_ids: List[str], assigned_to_id: Optional[str]
    ) -> Dict[str, Any]:
        """Update assigned user for multiple tasks"""
        # Validate assigned user exists if provided
        if assigned_to_id:
            assigned_user = db.query(User).filter(User.id == assigned_to_id).first()
            if not assigned_user:
                return {
                    "success": False,
                    "message": "Assigned user not found",
                    "updated_count": 0,
                }

        accessible_tasks = BulkOperationsService.validate_task_access(
            db, user_id, task_ids
        )

        if not accessible_tasks:
            return {
                "success": False,
                "message": "No accessible tasks found",
                "updated_count": 0,
            }

        updated_count = 0
        skipped_count = 0

        for task in accessible_tasks:
            # If task is in a project, verify assigned user is a member
            if task.project_id and assigned_to_id:
                project = task.project
                if not project.has_permission(assigned_to_id, ProjectRole.VIEWER):
                    skipped_count += 1
                    continue

            task.assigned_to_id = assigned_to_id
            updated_count += 1

        db.commit()

        return {
            "success": True,
            "message": f"Updated assignment for {updated_count} tasks",
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "inaccessible_count": len(task_ids) - len(accessible_tasks),
        }

    @staticmethod
    def add_tags(
        db: Session, user_id: str, task_ids: List[str], tag_names: List[str]
    ) -> Dict[str, Any]:
        """Add tags to multiple tasks"""
        accessible_tasks = BulkOperationsService.validate_task_access(
            db, user_id, task_ids
        )

        if not accessible_tasks:
            return {
                "success": False,
                "message": "No accessible tasks found",
                "updated_count": 0,
            }

        updated_count = 0
        for task in accessible_tasks:
            # Get current tag names
            current_tag_names = [tag.name for tag in task.tags]
            # Add new tags that aren't already present
            new_tags = [name for name in tag_names if name not in current_tag_names]
            if new_tags:
                TagService.add_tags_to_task(db, task.id, new_tags, user_id)
                updated_count += 1

        db.commit()

        return {
            "success": True,
            "message": f"Added tags to {updated_count} tasks",
            "updated_count": updated_count,
            "inaccessible_count": len(task_ids) - len(accessible_tasks),
        }

    @staticmethod
    def remove_tags(
        db: Session, user_id: str, task_ids: List[str], tag_names: List[str]
    ) -> Dict[str, Any]:
        """Remove tags from multiple tasks"""
        accessible_tasks = BulkOperationsService.validate_task_access(
            db, user_id, task_ids
        )

        if not accessible_tasks:
            return {
                "success": False,
                "message": "No accessible tasks found",
                "updated_count": 0,
            }

        # Convert tag names to lowercase for matching
        tag_names_lower = [name.lower() for name in tag_names]

        updated_count = 0
        for task in accessible_tasks:
            # Remove matching tags
            original_count = len(task.tags)
            task.tags = [tag for tag in task.tags if tag.name not in tag_names_lower]
            if len(task.tags) < original_count:
                updated_count += 1

        db.commit()

        return {
            "success": True,
            "message": f"Removed tags from {updated_count} tasks",
            "updated_count": updated_count,
            "inaccessible_count": len(task_ids) - len(accessible_tasks),
        }

    @staticmethod
    def add_categories(
        db: Session, user_id: str, task_ids: List[str], category_ids: List[str]
    ) -> Dict[str, Any]:
        """Add categories to multiple tasks"""
        # Validate categories exist and belong to user
        categories = (
            db.query(Category)
            .filter(and_(Category.id.in_(category_ids), Category.user_id == user_id))
            .all()
        )

        if len(categories) != len(category_ids):
            return {
                "success": False,
                "message": "Some categories not found or not accessible",
                "updated_count": 0,
            }

        accessible_tasks = BulkOperationsService.validate_task_access(
            db, user_id, task_ids
        )

        if not accessible_tasks:
            return {
                "success": False,
                "message": "No accessible tasks found",
                "updated_count": 0,
            }

        updated_count = 0
        for task in accessible_tasks:
            # Get current category IDs
            current_category_ids = [cat.id for cat in task.categories]
            # Add new categories that aren't already present
            for category in categories:
                if category.id not in current_category_ids:
                    task.categories.append(category)
            updated_count += 1

        db.commit()

        return {
            "success": True,
            "message": f"Added categories to {updated_count} tasks",
            "updated_count": updated_count,
            "inaccessible_count": len(task_ids) - len(accessible_tasks),
        }

    @staticmethod
    def remove_categories(
        db: Session, user_id: str, task_ids: List[str], category_ids: List[str]
    ) -> Dict[str, Any]:
        """Remove categories from multiple tasks"""
        accessible_tasks = BulkOperationsService.validate_task_access(
            db, user_id, task_ids
        )

        if not accessible_tasks:
            return {
                "success": False,
                "message": "No accessible tasks found",
                "updated_count": 0,
            }

        updated_count = 0
        for task in accessible_tasks:
            # Remove matching categories
            original_count = len(task.categories)
            task.categories = [
                cat for cat in task.categories if cat.id not in category_ids
            ]
            if len(task.categories) < original_count:
                updated_count += 1

        db.commit()

        return {
            "success": True,
            "message": f"Removed categories from {updated_count} tasks",
            "updated_count": updated_count,
            "inaccessible_count": len(task_ids) - len(accessible_tasks),
        }

    @staticmethod
    def delete_tasks(db: Session, user_id: str, task_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple tasks"""
        # For deletion, user must own the task or be project ADMIN
        owned_tasks = (
            db.query(Task)
            .filter(and_(Task.id.in_(task_ids), Task.user_id == user_id))
            .all()
        )

        # Check project tasks where user is ADMIN
        admin_tasks = []
        remaining_ids = set(task_ids) - set([t.id for t in owned_tasks])

        if remaining_ids:
            tasks_with_projects = (
                db.query(Task)
                .filter(and_(Task.id.in_(remaining_ids), Task.project_id != None))
                .all()
            )

            for task in tasks_with_projects:
                project = task.project
                if project and project.has_permission(user_id, ProjectRole.ADMIN):
                    admin_tasks.append(task)

        deletable_tasks = owned_tasks + admin_tasks

        if not deletable_tasks:
            return {
                "success": False,
                "message": "No tasks found that you can delete",
                "deleted_count": 0,
            }

        deleted_count = len(deletable_tasks)

        for task in deletable_tasks:
            db.delete(task)

        db.commit()

        return {
            "success": True,
            "message": f"Deleted {deleted_count} tasks",
            "deleted_count": deleted_count,
            "inaccessible_count": len(task_ids) - deleted_count,
        }

    @staticmethod
    def move_to_project(
        db: Session, user_id: str, task_ids: List[str], project_id: Optional[str]
    ) -> Dict[str, Any]:
        """Move tasks to a different project"""
        # Validate project if provided
        if project_id:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {
                    "success": False,
                    "message": "Project not found",
                    "updated_count": 0,
                }

            # User must have at least MEMBER role in target project
            if not project.has_permission(user_id, ProjectRole.MEMBER):
                return {
                    "success": False,
                    "message": "You don't have permission to add tasks to this project",
                    "updated_count": 0,
                }

        accessible_tasks = BulkOperationsService.validate_task_access(
            db, user_id, task_ids
        )

        if not accessible_tasks:
            return {
                "success": False,
                "message": "No accessible tasks found",
                "updated_count": 0,
            }

        updated_count = 0
        for task in accessible_tasks:
            task.project_id = project_id
            updated_count += 1

        db.commit()

        return {
            "success": True,
            "message": f"Moved {updated_count} tasks to project",
            "updated_count": updated_count,
            "inaccessible_count": len(task_ids) - len(accessible_tasks),
        }
