"""
Service for managing task dependencies and subtasks.
Handles validation, circular dependency detection, and constraint enforcement.
"""
from typing import List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.sql import func
from app.db.models import Task, TaskDependency, TaskStatus
from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    ConflictException
)
import uuid


class TaskDependencyService:
    """Service for managing task dependencies and subtasks"""
    
    @staticmethod
    def create_dependency(
        db: Session,
        task_id: str,
        depends_on_id: str,
        user_id: str
    ) -> TaskDependency:
        """
        Create a dependency between two tasks.
        
        Args:
            db: Database session
            task_id: ID of the task that has the dependency
            depends_on_id: ID of the task being depended on
            user_id: ID of the user creating the dependency
            
        Returns:
            Created TaskDependency
            
        Raises:
            NotFoundException: If either task is not found
            BadRequestException: If dependency would create a circular reference
            ConflictException: If dependency already exists
        """
        # Validate both tasks exist and belong to the user
        task = db.query(Task).filter(
            and_(Task.id == task_id, Task.user_id == user_id)
        ).first()
        if not task:
            raise NotFoundException(f"Task {task_id} not found")
            
        depends_on = db.query(Task).filter(
            and_(Task.id == depends_on_id, Task.user_id == user_id)
        ).first()
        if not depends_on:
            raise NotFoundException(f"Task {depends_on_id} not found")
        
        # Check if dependency already exists
        existing = db.query(TaskDependency).filter(
            and_(
                TaskDependency.task_id == task_id,
                TaskDependency.depends_on_id == depends_on_id
            )
        ).first()
        if existing:
            raise ConflictException("Dependency already exists")
        
        # Check for self-dependency
        if task_id == depends_on_id:
            raise BadRequestException("A task cannot depend on itself")
        
        # Check for circular dependencies
        if TaskDependencyService._would_create_cycle(db, task_id, depends_on_id):
            raise BadRequestException("This dependency would create a circular reference")
        
        # Create the dependency
        dependency = TaskDependency(
            id=str(uuid.uuid4()),
            task_id=task_id,
            depends_on_id=depends_on_id
        )
        db.add(dependency)
        db.commit()
        db.refresh(dependency)
        
        return dependency
    
    @staticmethod
    def _would_create_cycle(
        db: Session,
        task_id: str,
        depends_on_id: str
    ) -> bool:
        """
        Check if adding a dependency would create a cycle.
        Uses DFS to detect cycles.
        """
        visited = set()
        
        def has_path(from_id: str, to_id: str, visited_set: Set[str]) -> bool:
            """Check if there's a path from from_id to to_id"""
            if from_id == to_id:
                return True
            
            if from_id in visited_set:
                return False
                
            visited_set.add(from_id)
            
            # Get all tasks that from_id depends on
            dependencies = db.query(TaskDependency).filter(
                TaskDependency.task_id == from_id
            ).all()
            
            for dep in dependencies:
                if has_path(dep.depends_on_id, to_id, visited_set):
                    return True
                    
            return False
        
        # Check if depends_on_id can reach task_id (which would create a cycle)
        return has_path(depends_on_id, task_id, visited)
    
    @staticmethod
    def delete_dependency(
        db: Session,
        dependency_id: str,
        user_id: str
    ) -> bool:
        """Delete a task dependency"""
        # Find the dependency and verify ownership
        dependency = db.query(TaskDependency).join(
            Task, TaskDependency.task_id == Task.id
        ).filter(
            and_(
                TaskDependency.id == dependency_id,
                Task.user_id == user_id
            )
        ).first()
        
        if not dependency:
            raise NotFoundException("Dependency not found")
        
        db.delete(dependency)
        db.commit()
        return True
    
    @staticmethod
    def get_task_dependencies(
        db: Session,
        task_id: str,
        user_id: str
    ) -> List[TaskDependency]:
        """Get all dependencies for a task"""
        # Verify task ownership
        task = db.query(Task).filter(
            and_(Task.id == task_id, Task.user_id == user_id)
        ).first()
        if not task:
            raise NotFoundException(f"Task {task_id} not found")
        
        return db.query(TaskDependency).filter(
            TaskDependency.task_id == task_id
        ).all()
    
    @staticmethod
    def can_complete_task(
        db: Session,
        task_id: str,
        user_id: str
    ) -> tuple[bool, List[str]]:
        """
        Check if a task can be completed based on its dependencies.
        
        Returns:
            Tuple of (can_complete, list_of_incomplete_dependency_ids)
        """
        # Get all dependencies for this task
        dependencies = db.query(TaskDependency).join(
            Task, TaskDependency.depends_on_id == Task.id
        ).filter(
            and_(
                TaskDependency.task_id == task_id,
                Task.user_id == user_id
            )
        ).all()
        
        incomplete_deps = []
        for dep in dependencies:
            if dep.depends_on.status != TaskStatus.DONE:
                incomplete_deps.append(dep.depends_on_id)
        
        return len(incomplete_deps) == 0, incomplete_deps
    
    @staticmethod
    def update_task_parent(
        db: Session,
        task_id: str,
        parent_task_id: Optional[str],
        user_id: str
    ) -> Task:
        """
        Update a task's parent (make it a subtask or remove parent).
        
        Args:
            db: Database session
            task_id: ID of the task to update
            parent_task_id: ID of the new parent task (None to remove parent)
            user_id: ID of the user
            
        Returns:
            Updated task
            
        Raises:
            NotFoundException: If task or parent task not found
            BadRequestException: If operation would create invalid hierarchy
        """
        # Get the task
        task = db.query(Task).filter(
            and_(Task.id == task_id, Task.user_id == user_id)
        ).first()
        if not task:
            raise NotFoundException(f"Task {task_id} not found")
        
        # If removing parent, just update and return
        if parent_task_id is None:
            task.parent_task_id = None
            db.commit()
            db.refresh(task)
            return task
        
        # Validate parent task exists and belongs to user
        parent_task = db.query(Task).filter(
            and_(Task.id == parent_task_id, Task.user_id == user_id)
        ).first()
        if not parent_task:
            raise NotFoundException(f"Parent task {parent_task_id} not found")
        
        # Check for self-parenting
        if task_id == parent_task_id:
            raise BadRequestException("A task cannot be its own parent")
        
        # Check for circular hierarchy
        if TaskDependencyService._would_create_circular_hierarchy(
            db, task_id, parent_task_id
        ):
            raise BadRequestException("This would create a circular task hierarchy")
        
        # Update the parent
        task.parent_task_id = parent_task_id
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def _would_create_circular_hierarchy(
        db: Session,
        task_id: str,
        new_parent_id: str
    ) -> bool:
        """Check if setting new_parent_id as parent of task_id would create a cycle"""
        current = new_parent_id
        
        while current:
            if current == task_id:
                return True
            
            parent_task = db.query(Task).filter(Task.id == current).first()
            if not parent_task:
                break
                
            current = parent_task.parent_task_id
        
        return False
    
    @staticmethod
    def get_subtasks(
        db: Session,
        task_id: str,
        user_id: str
    ) -> List[Task]:
        """Get all direct subtasks of a task"""
        # Verify task ownership
        task = db.query(Task).filter(
            and_(Task.id == task_id, Task.user_id == user_id)
        ).first()
        if not task:
            raise NotFoundException(f"Task {task_id} not found")
        
        return db.query(Task).filter(
            Task.parent_task_id == task_id
        ).order_by(Task.position).all()
    
    @staticmethod
    def update_parent_task_status(
        db: Session,
        parent_task: Task
    ) -> None:
        """
        Update parent task status based on subtasks.
        Called after subtask status changes.
        """
        subtasks = db.query(Task).filter(
            Task.parent_task_id == parent_task.id
        ).all()
        
        if not subtasks:
            return
        
        # Count subtask statuses
        all_done = all(st.status == TaskStatus.DONE for st in subtasks)
        any_in_progress = any(st.status == TaskStatus.IN_PROGRESS for st in subtasks)
        all_todo = all(st.status == TaskStatus.TODO for st in subtasks)
        
        # Update parent status based on subtasks
        if all_done and parent_task.status != TaskStatus.DONE:
            parent_task.status = TaskStatus.DONE
            parent_task.completed_at = func.now()
        elif any_in_progress and parent_task.status == TaskStatus.TODO:
            parent_task.status = TaskStatus.IN_PROGRESS
        elif all_todo and parent_task.status != TaskStatus.TODO:
            parent_task.status = TaskStatus.TODO
            parent_task.completed_at = None
        
        db.commit()