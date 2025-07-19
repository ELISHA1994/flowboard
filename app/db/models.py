from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Boolean, ForeignKey, Integer, Float, Table, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid


class TaskStatus(str, enum.Enum):
    """Task status enumeration"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    """Task priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Association tables for many-to-many relationships
task_categories = Table(
    'task_categories',
    Base.metadata,
    Column('task_id', String, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', String, ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)
)

task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', String, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', String, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class User(Base):
    """
    SQLAlchemy model for User table.
    Stores user authentication and profile information.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="user", cascade="all, delete-orphan")
    owned_projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan", foreign_keys="Project.owner_id")
    project_memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")


class Task(Base):
    """
    SQLAlchemy model for Task table.
    This model defines the structure of the tasks table in the database.
    """
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Date fields
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Time tracking fields
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, default=0.0, nullable=False)
    
    # Ordering field
    position = Column(Integer, default=0, nullable=False)
    
    # Subtask support
    parent_task_id = Column(String, ForeignKey("tasks.id"), nullable=True, index=True)
    
    # Project support
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    categories = relationship("Category", secondary=task_categories, back_populates="tasks")
    tags = relationship("Tag", secondary=task_tags, back_populates="tasks")
    
    # Self-referential relationship for subtasks
    parent_task = relationship("Task", remote_side=[id], backref="subtasks", foreign_keys=[parent_task_id])
    
    # Dependencies relationships
    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    dependents = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.depends_on_id",
        back_populates="depends_on",
        cascade="all, delete-orphan"
    )
    
    # Project relationship
    project = relationship("Project", back_populates="tasks")


class Category(Base):
    """
    SQLAlchemy model for Category table.
    Categories are used to organize tasks into groups.
    """
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    icon = Column(String(50), nullable=True)  # Icon name/emoji
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="categories")
    tasks = relationship("Task", secondary=task_categories, back_populates="categories")


class Tag(Base):
    """
    SQLAlchemy model for Tag table.
    Tags provide flexible labeling for tasks.
    """
    __tablename__ = "tags"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    color = Column(String(7), nullable=False, default="#808080")  # Hex color code
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="tags")
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")


class TaskDependency(Base):
    """
    SQLAlchemy model for TaskDependency table.
    Represents dependencies between tasks (e.g., Task A must be completed before Task B).
    """
    __tablename__ = "task_dependencies"
    
    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    depends_on_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on = relationship("Task", foreign_keys=[depends_on_id], back_populates="dependents")
    
    # Unique constraint to prevent duplicate dependencies
    __table_args__ = (
        UniqueConstraint('task_id', 'depends_on_id', name='_task_dependency_uc'),
    )


class ProjectRole(str, enum.Enum):
    """Enum for project member roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Project(Base):
    """Project model for organizing tasks"""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="owned_projects", foreign_keys=[owner_id])
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    
    def get_member_role(self, user_id: str) -> ProjectRole:
        """Get the role of a user in this project"""
        member = next((m for m in self.members if m.user_id == user_id), None)
        if member:
            return member.role
        if self.owner_id == user_id:
            return ProjectRole.OWNER
        return None
    
    def has_permission(self, user_id: str, required_role: ProjectRole) -> bool:
        """Check if user has required permission level"""
        role_hierarchy = {
            ProjectRole.VIEWER: 1,
            ProjectRole.MEMBER: 2,
            ProjectRole.ADMIN: 3,
            ProjectRole.OWNER: 4
        }
        
        user_role = self.get_member_role(user_id)
        if not user_role:
            return False
            
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)


class ProjectMember(Base):
    """Project membership model"""
    __tablename__ = "project_members"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLEnum(ProjectRole), default=ProjectRole.MEMBER, nullable=False)
    joined_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")
    
    # Unique constraint to prevent duplicate memberships
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='_project_user_uc'),
    )


class ProjectInvitation(Base):
    """Project invitation model"""
    __tablename__ = "project_invitations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    inviter_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    invitee_email = Column(String(320), nullable=False)
    role = Column(SQLEnum(ProjectRole), default=ProjectRole.MEMBER, nullable=False)
    token = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    project = relationship("Project")
    inviter = relationship("User")