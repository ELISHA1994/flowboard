"""
API endpoints for project management
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.middleware.jwt_auth_backend import \
    get_current_active_user as get_current_user
from app.db.database import get_db
from app.db.models import ProjectInvitation, ProjectRole, User
from app.models.project import (ProjectCreate, ProjectDetailResponse,
                                ProjectInvitationCreate,
                                ProjectInvitationResponse, ProjectMemberAdd,
                                ProjectMemberResponse, ProjectMemberUpdate,
                                ProjectResponse, ProjectUpdate)
from app.services.project_service import ProjectService

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new project"""
    try:
        new_project = ProjectService.create_project(db, project, current_user.id)
        return ProjectService.to_response(new_project, current_user.id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all projects where user is owner or member"""
    projects = ProjectService.get_user_projects(db, current_user.id, include_inactive)
    return [ProjectService.to_response(p, current_user.id, db) for p in projects]


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get project details"""
    project = ProjectService.get_project_by_id(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectService.to_detail_response(project, current_user.id, db)


@router.get("/{project_id}/members", response_model=List[ProjectMemberResponse])
def list_project_members(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List project members"""
    project = ProjectService.get_project_by_id(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Return only the members from the detail response
    detail_response = ProjectService.to_detail_response(project, current_user.id, db)
    return detail_response.members


@router.post("/{project_id}/members", response_model=dict)
def add_project_member_via_body(
    project_id: str,
    member_data: ProjectMemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a member to the project using request body (requires ADMIN or OWNER role)"""
    project = ProjectService.get_project_by_id(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check permissions
    if not project.has_permission(current_user.id, ProjectRole.ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    try:
        member = ProjectService.add_member(
            db, project_id, member_data.user_id, member_data.role
        )
        return {"message": "Member added successfully", "member_id": member.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update project details (requires ADMIN or OWNER role)"""
    project = ProjectService.get_project_by_id(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check permissions
    if not project.has_permission(current_user.id, ProjectRole.ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    try:
        updated_project = ProjectService.update_project(db, project, project_update)
        return ProjectService.to_response(updated_project, current_user.id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    soft_delete: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a project (requires OWNER role)"""
    project = ProjectService.get_project_by_id(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Only owner can delete
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Only project owner can delete the project"
        )

    if soft_delete:
        ProjectService.soft_delete_project(db, project)
    else:
        ProjectService.delete_project(db, project)


@router.post("/{project_id}/members/{user_id}", response_model=dict)
def add_project_member(
    project_id: str,
    user_id: str,
    member_data: ProjectMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a member to the project (requires ADMIN or OWNER role)"""
    project = ProjectService.get_project_by_id(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check permissions
    if not project.has_permission(current_user.id, ProjectRole.ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    try:
        member = ProjectService.add_member(db, project_id, user_id, member_data.role)
        return {"message": "Member added successfully", "member_id": member.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{project_id}/members/{user_id}", response_model=dict)
def update_member_role(
    project_id: str,
    user_id: str,
    member_data: ProjectMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a member's role (requires ADMIN or OWNER role)"""
    project = ProjectService.get_project_by_id(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check permissions
    if not project.has_permission(current_user.id, ProjectRole.ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Cannot change owner's role
    if user_id == project.owner_id:
        raise HTTPException(status_code=400, detail="Cannot change owner's role")

    member = ProjectService.get_project_member(db, project_id, user_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    ProjectService.update_member_role(db, member, member_data.role)
    return {"message": "Member role updated successfully"}


@router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_project_member(
    project_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a member from the project (requires ADMIN or OWNER role)"""
    project = ProjectService.get_project_by_id(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check permissions (members can remove themselves)
    if user_id != current_user.id and not project.has_permission(
        current_user.id, ProjectRole.ADMIN
    ):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Cannot remove owner
    if user_id == project.owner_id:
        raise HTTPException(status_code=400, detail="Cannot remove project owner")

    member = ProjectService.get_project_member(db, project_id, user_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    ProjectService.remove_member(db, member)


@router.post("/{project_id}/invitations", response_model=ProjectInvitationResponse)
def create_invitation(
    project_id: str,
    invitation: ProjectInvitationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a project invitation (requires ADMIN or OWNER role)"""
    project = ProjectService.get_project_by_id(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check permissions
    if not project.has_permission(current_user.id, ProjectRole.ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    try:
        new_invitation = ProjectService.create_invitation(
            db, project_id, current_user.id, invitation
        )

        return ProjectInvitationResponse(
            id=new_invitation.id,
            project_id=new_invitation.project_id,
            project_name=project.name,
            inviter_name=current_user.username,
            invitee_email=new_invitation.invitee_email,
            role=new_invitation.role,
            token=new_invitation.token,
            expires_at=new_invitation.expires_at,
            created_at=new_invitation.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invitations/{token}/accept", response_model=dict)
def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept a project invitation"""
    invitation = (
        db.query(ProjectInvitation).filter(ProjectInvitation.token == token).first()
    )

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    try:
        member = ProjectService.accept_invitation(db, invitation, current_user)
        return {
            "message": "Invitation accepted successfully",
            "project_id": invitation.project_id,
            "role": member.role,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
