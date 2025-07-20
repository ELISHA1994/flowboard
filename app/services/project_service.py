"""
Service layer for project management
"""
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from app.db.models import Project, ProjectMember, ProjectInvitation, User, ProjectRole
from app.models.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse,
    ProjectInvitationCreate, ProjectMemberResponse
)
import uuid


class ProjectService:
    """Service for managing projects"""
    
    @staticmethod
    def create_project(db: Session, project_data: ProjectCreate, owner_id: str) -> Project:
        """Create a new project"""
        project = Project(
            id=str(uuid.uuid4()),
            name=project_data.name,
            description=project_data.description,
            owner_id=owner_id,
            is_active=True
        )
        
        try:
            db.add(project)
            db.commit()
            db.refresh(project)
            return project
        except IntegrityError:
            db.rollback()
            raise ValueError("Project creation failed")
    
    @staticmethod
    def get_user_projects(db: Session, user_id: str, include_inactive: bool = False) -> List[Project]:
        """Get all projects where user is owner or member"""
        query = db.query(Project).outerjoin(ProjectMember).filter(
            (Project.owner_id == user_id) | (ProjectMember.user_id == user_id)
        ).distinct()
        
        if not include_inactive:
            query = query.filter(Project.is_active == True)
            
        return query.all()
    
    @staticmethod
    def get_project_by_id(db: Session, project_id: str, user_id: str) -> Optional[Project]:
        """Get project by ID if user has access"""
        project = db.query(Project).options(
            joinedload(Project.members).joinedload(ProjectMember.user),
            joinedload(Project.owner)
        ).filter(Project.id == project_id).first()
        
        if not project:
            return None
            
        # Check if user has access
        if project.owner_id != user_id:
            member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            ).first()
            if not member:
                return None
                
        return project
    
    @staticmethod
    def update_project(db: Session, project: Project, update_data: ProjectUpdate) -> Project:
        """Update project details"""
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            setattr(project, field, value)
            
        project.updated_at = datetime.now(timezone.utc)
        
        try:
            db.commit()
            db.refresh(project)
            return project
        except IntegrityError:
            db.rollback()
            raise ValueError("Project update failed")
    
    @staticmethod
    def delete_project(db: Session, project: Project) -> None:
        """Delete a project (hard delete)"""
        db.delete(project)
        db.commit()
    
    @staticmethod
    def soft_delete_project(db: Session, project: Project) -> Project:
        """Soft delete a project"""
        project.is_active = False
        project.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(project)
        return project
    
    @staticmethod
    def add_member(db: Session, project_id: str, user_id: str, role: ProjectRole) -> ProjectMember:
        """Add a member to a project"""
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
            
        # Check if already a member
        existing = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        
        if existing:
            raise ValueError("User is already a project member")
            
        member = ProjectMember(
            id=str(uuid.uuid4()),
            project_id=project_id,
            user_id=user_id,
            role=role
        )
        
        db.add(member)
        db.commit()
        db.refresh(member)
        return member
    
    @staticmethod
    def update_member_role(db: Session, member: ProjectMember, new_role: ProjectRole) -> ProjectMember:
        """Update a member's role"""
        member.role = new_role
        db.commit()
        db.refresh(member)
        return member
    
    @staticmethod
    def remove_member(db: Session, member: ProjectMember) -> None:
        """Remove a member from a project"""
        db.delete(member)
        db.commit()
    
    @staticmethod
    def create_invitation(
        db: Session, 
        project_id: str, 
        inviter_id: str, 
        invitation_data: ProjectInvitationCreate
    ) -> ProjectInvitation:
        """Create a project invitation"""
        # Check if user with email already exists and is a member
        existing_user = db.query(User).filter(User.email == invitation_data.invitee_email).first()
        if existing_user:
            existing_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == existing_user.id
            ).first()
            if existing_member:
                raise ValueError("User is already a project member")
        
        # Check for existing pending invitation
        existing_invitation = db.query(ProjectInvitation).filter(
            ProjectInvitation.project_id == project_id,
            ProjectInvitation.invitee_email == invitation_data.invitee_email,
            ProjectInvitation.accepted_at == None,
            ProjectInvitation.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if existing_invitation:
            raise ValueError("An invitation for this email already exists")
        
        invitation = ProjectInvitation(
            id=str(uuid.uuid4()),
            project_id=project_id,
            inviter_id=inviter_id,
            invitee_email=invitation_data.invitee_email,
            role=invitation_data.role,
            token=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)  # 7 day expiry
        )
        
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation
    
    @staticmethod
    def accept_invitation(db: Session, invitation: ProjectInvitation, user: User) -> ProjectMember:
        """Accept a project invitation"""
        if invitation.invitee_email != user.email:
            raise ValueError("This invitation is not for you")
            
        if invitation.accepted_at:
            raise ValueError("Invitation has already been accepted")
            
        if invitation.expires_at < datetime.now(timezone.utc):
            raise ValueError("Invitation has expired")
        
        # Add user as project member
        member = ProjectService.add_member(
            db, 
            invitation.project_id, 
            user.id, 
            invitation.role
        )
        
        # Mark invitation as accepted
        invitation.accepted_at = datetime.now(timezone.utc)
        db.commit()
        
        return member
    
    @staticmethod
    def get_project_member(db: Session, project_id: str, user_id: str) -> Optional[ProjectMember]:
        """Get a specific project member"""
        return db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
    
    @staticmethod
    def to_response(project: Project, user_id: str, db: Session) -> ProjectResponse:
        """Convert project to response model"""
        task_count = len(project.tasks) if project.tasks else 0
        member_count = len(project.members) + 1  # +1 for owner
        
        # Get user's role
        user_role = project.get_member_role(user_id)
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            owner_id=project.owner_id,
            owner_username=project.owner.username if project.owner else "Unknown",
            is_active=project.is_active,
            task_count=task_count,
            member_count=member_count,
            created_at=project.created_at,
            updated_at=project.updated_at,
            user_role=user_role
        )
    
    @staticmethod
    def to_detail_response(project: Project, user_id: str, db: Session) -> ProjectDetailResponse:
        """Convert project to detailed response model"""
        base_response = ProjectService.to_response(project, user_id, db)
        
        # Add owner as a member in the response
        members = []
        
        # Add owner
        if project.owner:
            members.append(ProjectMemberResponse(
                id="owner",
                user_id=project.owner.id,
                username=project.owner.username,
                email=project.owner.email,
                role=ProjectRole.OWNER,
                joined_at=project.created_at
            ))
        
        # Add other members
        for member in project.members:
            if member.user:
                members.append(ProjectMemberResponse(
                    id=member.id,
                    user_id=member.user.id,
                    username=member.user.username,
                    email=member.user.email,
                    role=member.role,
                    joined_at=member.joined_at
                ))
        
        return ProjectDetailResponse(
            **base_response.model_dump(),
            members=members
        )