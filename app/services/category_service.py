from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Category, Task
from app.models.category import CategoryCreate, CategoryUpdate
from app.core.logging import logger
import uuid


class CategoryService:
    """Service layer for category-related business logic"""
    
    @staticmethod
    def create_category(db: Session, user_id: str, category: CategoryCreate) -> Category:
        """Create a new category for a user"""
        # Check if category with same name exists for user
        existing = db.query(Category).filter(
            Category.user_id == user_id,
            Category.name == category.name
        ).first()
        
        if existing:
            raise ValueError("Category with this name already exists")
        
        db_category = Category(
            id=str(uuid.uuid4()),
            name=category.name,
            description=category.description,
            color=category.color,
            icon=category.icon,
            user_id=user_id,
            is_active=True
        )
        
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        
        logger.info(f"Created category {db_category.id} for user {user_id}")
        return db_category
    
    @staticmethod
    def get_user_categories(
        db: Session, 
        user_id: str, 
        include_inactive: bool = False
    ) -> List[Category]:
        """Get all categories for a user"""
        query = db.query(Category).filter(Category.user_id == user_id)
        
        if not include_inactive:
            query = query.filter(Category.is_active == True)
        
        return query.order_by(Category.name).all()
    
    @staticmethod
    def get_category(db: Session, category_id: str, user_id: str) -> Optional[Category]:
        """Get a specific category by ID"""
        return db.query(Category).filter(
            Category.id == category_id,
            Category.user_id == user_id
        ).first()
    
    @staticmethod
    def update_category(
        db: Session, 
        category_id: str, 
        user_id: str, 
        category_update: CategoryUpdate
    ) -> Optional[Category]:
        """Update a category"""
        db_category = CategoryService.get_category(db, category_id, user_id)
        
        if not db_category:
            return None
        
        # Check for duplicate name if name is being updated
        if category_update.name and category_update.name != db_category.name:
            existing = db.query(Category).filter(
                Category.user_id == user_id,
                Category.name == category_update.name,
                Category.id != category_id
            ).first()
            
            if existing:
                raise ValueError("Category with this name already exists")
        
        # Update fields
        update_data = category_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)
        
        db.commit()
        db.refresh(db_category)
        
        logger.info(f"Updated category {category_id} for user {user_id}")
        return db_category
    
    @staticmethod
    def delete_category(db: Session, category_id: str, user_id: str) -> bool:
        """Delete a category (soft delete by setting is_active=False)"""
        db_category = CategoryService.get_category(db, category_id, user_id)
        
        if not db_category:
            return False
        
        # Soft delete - just mark as inactive
        db_category.is_active = False
        db.commit()
        
        logger.info(f"Soft deleted category {category_id} for user {user_id}")
        return True
    
    @staticmethod
    def get_category_task_count(db: Session, category_id: str) -> int:
        """Get the number of tasks in a category"""
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            return 0
        return len(category.tasks)
    
    @staticmethod
    def add_category_to_task(
        db: Session, 
        task_id: str, 
        category_id: str, 
        user_id: str
    ) -> bool:
        """Add a category to a task"""
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
        
        category = CategoryService.get_category(db, category_id, user_id)
        
        if not task or not category:
            return False
        
        if category not in task.categories:
            task.categories.append(category)
            db.commit()
            logger.info(f"Added category {category_id} to task {task_id}")
        
        return True
    
    @staticmethod
    def remove_category_from_task(
        db: Session, 
        task_id: str, 
        category_id: str, 
        user_id: str
    ) -> bool:
        """Remove a category from a task"""
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
        
        category = CategoryService.get_category(db, category_id, user_id)
        
        if not task or not category:
            return False
        
        if category in task.categories:
            task.categories.remove(category)
            db.commit()
            logger.info(f"Removed category {category_id} from task {task_id}")
        
        return True