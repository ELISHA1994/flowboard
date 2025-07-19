from typing import List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.models import Tag, Task, User
from app.models.tag import TagCreate, TagUpdate
from app.core.logging import logger
import uuid


class TagService:
    """Service layer for tag-related business logic"""
    
    @staticmethod
    def create_tag(db: Session, user_id: str, tag: TagCreate) -> Tag:
        """Create a new tag for a user"""
        # Normalize tag name
        tag_name = tag.name.strip().lower()
        
        # Check if tag exists for user
        existing = db.query(Tag).filter(
            Tag.user_id == user_id,
            Tag.name == tag_name
        ).first()
        
        if existing:
            return existing  # Return existing tag instead of error
        
        db_tag = Tag(
            id=str(uuid.uuid4()),
            name=tag_name,
            color=tag.color,
            user_id=user_id
        )
        
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)
        
        logger.info(f"Created tag {db_tag.id} for user {user_id}")
        return db_tag
    
    @staticmethod
    def get_or_create_tags(db: Session, user_id: str, tag_names: List[str]) -> List[Tag]:
        """Get existing tags or create new ones"""
        tags = []
        
        for name in tag_names:
            name = name.strip().lower()
            if not name:
                continue
            
            # Check if tag exists
            tag = db.query(Tag).filter(
                Tag.user_id == user_id,
                Tag.name == name
            ).first()
            
            if not tag:
                # Create new tag with default color
                tag = Tag(
                    id=str(uuid.uuid4()),
                    name=name,
                    color="#808080",  # Default gray color
                    user_id=user_id
                )
                db.add(tag)
                db.flush()  # Flush to get ID without committing
            
            tags.append(tag)
        
        if tags:
            db.commit()
        
        return tags
    
    @staticmethod
    def get_user_tags(db: Session, user_id: str) -> List[Tag]:
        """Get all tags for a user"""
        return db.query(Tag).filter(
            Tag.user_id == user_id
        ).order_by(Tag.name).all()
    
    @staticmethod
    def get_tag(db: Session, tag_id: str, user_id: str) -> Optional[Tag]:
        """Get a specific tag by ID"""
        return db.query(Tag).filter(
            Tag.id == tag_id,
            Tag.user_id == user_id
        ).first()
    
    @staticmethod
    def get_tag_by_name(db: Session, tag_name: str, user_id: str) -> Optional[Tag]:
        """Get a specific tag by name"""
        return db.query(Tag).filter(
            Tag.name == tag_name.strip().lower(),
            Tag.user_id == user_id
        ).first()
    
    @staticmethod
    def update_tag(
        db: Session, 
        tag_id: str, 
        user_id: str, 
        tag_update: TagUpdate
    ) -> Optional[Tag]:
        """Update a tag"""
        db_tag = TagService.get_tag(db, tag_id, user_id)
        
        if not db_tag:
            return None
        
        # Check for duplicate name if name is being updated
        if tag_update.name and tag_update.name != db_tag.name:
            existing = db.query(Tag).filter(
                Tag.user_id == user_id,
                Tag.name == tag_update.name,
                Tag.id != tag_id
            ).first()
            
            if existing:
                raise ValueError("Tag with this name already exists")
        
        # Update fields
        update_data = tag_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_tag, field, value)
        
        db.commit()
        db.refresh(db_tag)
        
        logger.info(f"Updated tag {tag_id} for user {user_id}")
        return db_tag
    
    @staticmethod
    def delete_tag(db: Session, tag_id: str, user_id: str) -> bool:
        """Delete a tag completely"""
        db_tag = TagService.get_tag(db, tag_id, user_id)
        
        if not db_tag:
            return False
        
        # Hard delete - tags are lightweight and don't need soft delete
        db.delete(db_tag)
        db.commit()
        
        logger.info(f"Deleted tag {tag_id} for user {user_id}")
        return True
    
    @staticmethod
    def get_tag_task_count(db: Session, tag_id: str) -> int:
        """Get the number of tasks with a tag"""
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            return 0
        return len(tag.tasks)
    
    @staticmethod
    def set_task_tags(
        db: Session, 
        task_id: str, 
        tag_names: List[str], 
        user_id: str
    ) -> List[Tag]:
        """Set tags for a task (replaces existing tags)"""
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
        
        if not task:
            return []
        
        # Get or create tags
        tags = TagService.get_or_create_tags(db, user_id, tag_names)
        
        # Replace task tags
        task.tags = tags
        db.commit()
        
        logger.info(f"Set {len(tags)} tags for task {task_id}")
        return tags
    
    @staticmethod
    def add_tags_to_task(
        db: Session, 
        task_id: str, 
        tag_names: List[str], 
        user_id: str
    ) -> List[Tag]:
        """Add tags to a task (keeps existing tags)"""
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
        
        if not task:
            return []
        
        # Get or create tags
        new_tags = TagService.get_or_create_tags(db, user_id, tag_names)
        
        # Add only tags not already on task
        existing_tag_names = {tag.name for tag in task.tags}
        for tag in new_tags:
            if tag.name not in existing_tag_names:
                task.tags.append(tag)
        
        db.commit()
        
        logger.info(f"Added tags to task {task_id}")
        return task.tags
    
    @staticmethod
    def remove_tags_from_task(
        db: Session, 
        task_id: str, 
        tag_names: List[str], 
        user_id: str
    ) -> List[Tag]:
        """Remove specific tags from a task"""
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
        
        if not task:
            return []
        
        # Normalize tag names
        tag_names_lower = [name.strip().lower() for name in tag_names]
        
        # Remove matching tags
        task.tags = [tag for tag in task.tags if tag.name not in tag_names_lower]
        db.commit()
        
        logger.info(f"Removed tags from task {task_id}")
        return task.tags
    
    @staticmethod
    def get_popular_tags(db: Session, user_id: str, limit: int = 10) -> List[dict]:
        """Get most used tags for a user"""
        tags = db.query(Tag).filter(Tag.user_id == user_id).all()
        
        # Count task usage for each tag
        tag_counts = []
        for tag in tags:
            count = len(tag.tasks)
            if count > 0:  # Only include used tags
                tag_counts.append({
                    "tag": tag,
                    "task_count": count
                })
        
        # Sort by task count and limit
        tag_counts.sort(key=lambda x: x["task_count"], reverse=True)
        return tag_counts[:limit]