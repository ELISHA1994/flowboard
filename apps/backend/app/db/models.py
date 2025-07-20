from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Boolean, ForeignKey, Integer, Float, Table, Text, UniqueConstraint, Index
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


class RecurrencePattern(str, enum.Enum):
    """Recurrence pattern enumeration"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEEKDAYS = "weekdays"  # Monday to Friday
    CUSTOM = "custom"  # For advanced patterns


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
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan", foreign_keys="Task.user_id")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="user", cascade="all, delete-orphan")
    owned_projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan", foreign_keys="Project.owner_id")
    project_memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    mentions = relationship("CommentMention", back_populates="mentioned_user", cascade="all, delete-orphan")
    uploaded_files = relationship("FileAttachment", back_populates="uploaded_by", cascade="all, delete-orphan")
    saved_searches = relationship("SavedSearch", back_populates="user", cascade="all, delete-orphan")
    time_logs = relationship("TimeLog", back_populates="user", cascade="all, delete-orphan")
    webhook_subscriptions = relationship("WebhookSubscription", back_populates="user", cascade="all, delete-orphan")
    calendar_integrations = relationship("CalendarIntegration", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreference", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    task_reminders = relationship("TaskReminder", back_populates="user", cascade="all, delete-orphan")


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
    
    # Assignment support
    assigned_to_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    
    # Recurrence fields
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_pattern = Column(SQLEnum(RecurrencePattern), nullable=True)
    recurrence_interval = Column(Integer, nullable=True)  # e.g., every 2 days
    recurrence_days_of_week = Column(String(20), nullable=True)  # For weekly: "1,3,5" (Mon, Wed, Fri)
    recurrence_day_of_month = Column(Integer, nullable=True)  # For monthly: day number
    recurrence_month_of_year = Column(Integer, nullable=True)  # For yearly: month number
    recurrence_end_date = Column(DateTime(timezone=True), nullable=True)
    recurrence_count = Column(Integer, nullable=True)  # Number of occurrences
    recurrence_parent_id = Column(String, ForeignKey("tasks.id"), nullable=True)  # Original recurring task
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks", foreign_keys=[user_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
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
    
    # Task shares relationship
    shares = relationship("TaskShare", back_populates="task", cascade="all, delete-orphan")
    
    # Comments relationship
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    
    # File attachments
    attachments = relationship("FileAttachment", back_populates="task", cascade="all, delete-orphan")
    
    # Recurrence relationships
    recurrence_parent = relationship("Task", remote_side=[id], backref="recurrence_instances", foreign_keys=[recurrence_parent_id])
    
    # Time logs relationship
    time_logs = relationship("TimeLog", back_populates="task", cascade="all, delete-orphan")
    
    # Calendar sync relationship
    calendar_syncs = relationship("TaskCalendarSync", back_populates="task", cascade="all, delete-orphan")
    
    # Reminders relationship
    reminders = relationship("TaskReminder", back_populates="task", cascade="all, delete-orphan")


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
    webhook_subscriptions = relationship("WebhookSubscription", back_populates="project", cascade="all, delete-orphan")
    
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


class TaskSharePermission(str, enum.Enum):
    """Enum for task share permissions"""
    VIEW = "view"
    EDIT = "edit"
    COMMENT = "comment"


class WebhookDeliveryStatus(str, enum.Enum):
    """Webhook delivery status enumeration"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"


class TaskShare(Base):
    """Task sharing model for sharing individual tasks with other users"""
    __tablename__ = "task_shares"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    shared_by_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shared_with_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    permission = Column(SQLEnum(TaskSharePermission), default=TaskSharePermission.VIEW, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    task = relationship("Task", back_populates="shares")
    shared_by = relationship("User", foreign_keys=[shared_by_id])
    shared_with = relationship("User", foreign_keys=[shared_with_id])
    
    # Unique constraint to prevent duplicate shares
    __table_args__ = (
        UniqueConstraint('task_id', 'shared_with_id', name='_task_share_uc'),
    )


class Comment(Base):
    """Comment model for task comments with @mention support"""
    __tablename__ = "comments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_comment_id = Column(String, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    is_edited = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    task = relationship("Task", back_populates="comments")
    user = relationship("User", back_populates="comments")
    parent_comment = relationship("Comment", remote_side=[id], backref="replies")
    mentions = relationship("CommentMention", back_populates="comment", cascade="all, delete-orphan")


class CommentMention(Base):
    """Tracks @mentions in comments"""
    __tablename__ = "comment_mentions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    comment_id = Column(String, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)
    mentioned_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    comment = relationship("Comment", back_populates="mentions")
    mentioned_user = relationship("User", back_populates="mentions")
    
    # Unique constraint to prevent duplicate mentions
    __table_args__ = (
        UniqueConstraint('comment_id', 'mentioned_user_id', name='_comment_mention_uc'),
    )


class FileAttachment(Base):
    """Model for file attachments on tasks"""
    __tablename__ = "file_attachments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    uploaded_by_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String(100), nullable=True)
    storage_path = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    task = relationship("Task", back_populates="attachments")
    uploaded_by = relationship("User", back_populates="uploaded_files")


class SavedSearch(Base):
    """Model for saved search queries"""
    __tablename__ = "saved_searches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    search_query = Column(Text, nullable=False)  # JSON serialized search query
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="saved_searches")
    
    # Unique constraint: only one default search per user
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='_user_search_name_uc'),
    )


class TimeLog(Base):
    """Model for time tracking entries"""
    __tablename__ = "time_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    hours = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    logged_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    task = relationship("Task", back_populates="time_logs")
    user = relationship("User", back_populates="time_logs")


class WebhookSubscription(Base):
    """Model for webhook subscriptions"""
    __tablename__ = "webhook_subscriptions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=True)  # For HMAC signature verification
    events = Column(Text, nullable=False)  # JSON array of event types
    is_active = Column(Boolean, default=True, nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="webhook_subscriptions")
    project = relationship("Project", back_populates="webhook_subscriptions")
    deliveries = relationship("WebhookDelivery", back_populates="subscription", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    """Model for tracking webhook deliveries"""
    __tablename__ = "webhook_deliveries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String, ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)
    payload = Column(Text, nullable=False)  # JSON payload as string
    status = Column(SQLEnum(WebhookDeliveryStatus), default=WebhookDeliveryStatus.PENDING, nullable=False)
    response_status_code = Column(Integer, nullable=True)
    response_headers = Column(Text, nullable=True)  # JSON as string
    response_body = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    subscription = relationship("WebhookSubscription", back_populates="deliveries")


class CalendarIntegration(Base):
    """Model for calendar integrations"""
    __tablename__ = "calendar_integrations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(20), nullable=False)  # google, microsoft
    calendar_id = Column(String(255), nullable=False)
    calendar_name = Column(String(255), nullable=True)
    access_token = Column(Text, nullable=False)  # Encrypted
    refresh_token = Column(Text, nullable=True)  # Encrypted
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    sync_enabled = Column(Boolean, default=True, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_direction = Column(String(20), default="both", nullable=False)  # to_calendar, from_calendar, both
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="calendar_integrations")
    task_sync_mappings = relationship("TaskCalendarSync", back_populates="calendar_integration", cascade="all, delete-orphan")


class TaskCalendarSync(Base):
    """Model for mapping tasks to calendar events"""
    __tablename__ = "task_calendar_sync"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    calendar_integration_id = Column(String, ForeignKey("calendar_integrations.id", ondelete="CASCADE"), nullable=False)
    calendar_event_id = Column(String(255), nullable=False)
    last_synced_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    task = relationship("Task", back_populates="calendar_syncs")
    calendar_integration = relationship("CalendarIntegration", back_populates="task_sync_mappings")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('task_id', 'calendar_integration_id', name='_task_calendar_uc'),
    )


class NotificationPreference(Base):
    """Model for user notification preferences"""
    __tablename__ = "notification_preferences"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_type = Column(String(50), nullable=False)  # task_due, task_assigned, comment_mention, etc.
    channel = Column(String(20), nullable=False)  # email, in_app, push
    enabled = Column(Boolean, default=True, nullable=False)
    frequency = Column(String(20), default="immediate", nullable=False)  # immediate, daily_digest, weekly_digest
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'notification_type', 'channel', name='_user_notification_uc'),
    )


class Notification(Base):
    """Model for notifications"""
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # task_due, task_assigned, comment_mention, etc.
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(Text, nullable=True)  # JSON data for notification context
    read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    # Indexes
    __table_args__ = (
        Index('ix_notifications_user_read', 'user_id', 'read'),
        Index('ix_notifications_created_at', 'created_at'),
    )


class TaskReminder(Base):
    """Model for task reminders"""
    __tablename__ = "task_reminders"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    remind_at = Column(DateTime(timezone=True), nullable=False)
    reminder_type = Column(String(20), default="due_date", nullable=False)  # due_date, custom
    offset_minutes = Column(Integer, nullable=True)  # Minutes before due date
    message = Column(Text, nullable=True)  # Custom reminder message
    sent = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    task = relationship("Task", back_populates="reminders")
    user = relationship("User", back_populates="task_reminders")
    
    # Indexes
    __table_args__ = (
        Index('ix_task_reminders_remind_at', 'remind_at'),
        Index('ix_task_reminders_sent', 'sent'),
    )