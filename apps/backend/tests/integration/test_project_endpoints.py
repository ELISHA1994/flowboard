"""
Integration tests for project API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models import User, Project, ProjectMember, ProjectInvitation, ProjectRole
import uuid
from datetime import datetime, timedelta, timezone


@pytest.mark.integration
class TestProjectEndpoints:
    """Test project API endpoints"""
    
    def test_create_project(self, test_client: TestClient, test_user: User, auth_headers: dict):
        """Test creating a new project"""
        project_data = {
            "name": "Test Project",
            "description": "A test project description"
        }
        
        response = test_client.post("/projects/", json=project_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["description"] == "A test project description"
        assert data["owner_id"] == test_user.id
        assert data["owner_username"] == test_user.username
        assert data["is_active"] is True
        assert data["task_count"] == 0
        assert data["member_count"] == 1  # Owner counts as member
        assert data["user_role"] == "owner"
        assert "id" in data
        assert "created_at" in data
    
    def test_list_projects(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test listing user's projects"""
        # Create test projects
        project1 = Project(
            id=str(uuid.uuid4()),
            name="Project 1",
            owner_id=test_user.id,
            is_active=True
        )
        project2 = Project(
            id=str(uuid.uuid4()),
            name="Project 2",
            owner_id=test_user.id,
            is_active=False
        )
        # Project where user is member
        project3 = Project(
            id=str(uuid.uuid4()),
            name="Project 3",
            owner_id=str(uuid.uuid4()),
            is_active=True
        )
        member = ProjectMember(
            id=str(uuid.uuid4()),
            project_id=project3.id,
            user_id=test_user.id,
            role=ProjectRole.MEMBER
        )
        
        test_db.add_all([project1, project2, project3, member])
        test_db.commit()
        
        # Test getting active projects only
        response = test_client.get("/projects/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # project1 and project3 (active only)
        assert any(p["name"] == "Project 1" and p["user_role"] == "owner" for p in data)
        assert any(p["name"] == "Project 3" and p["user_role"] == "member" for p in data)
        
        # Test including inactive projects
        response = test_client.get("/projects/?include_inactive=true", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # All projects
    
    def test_get_project_details(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test getting project details"""
        # Create project with members
        project = Project(
            id=str(uuid.uuid4()),
            name="Test Project",
            description="Project description",
            owner_id=test_user.id,
            is_active=True
        )
        
        # Add another member
        other_user = User(
            id=str(uuid.uuid4()),
            username="otheruser",
            email="other@example.com",
            hashed_password="hash"
        )
        member = ProjectMember(
            id=str(uuid.uuid4()),
            project_id=project.id,
            user_id=other_user.id,
            role=ProjectRole.MEMBER
        )
        
        test_db.add_all([project, other_user, member])
        test_db.commit()
        
        response = test_client.get(f"/projects/{project.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project.id
        assert data["name"] == "Test Project"
        assert data["description"] == "Project description"
        assert data["member_count"] == 2
        assert len(data["members"]) == 2
        
        # Check members
        owner_member = next(m for m in data["members"] if m["user_id"] == test_user.id)
        assert owner_member["role"] == "owner"
        assert owner_member["username"] == test_user.username
        
        other_member = next(m for m in data["members"] if m["user_id"] == other_user.id)
        assert other_member["role"] == "member"
        assert other_member["username"] == "otheruser"
    
    def test_get_project_no_access(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test getting project without access"""
        # Create project owned by another user
        other_user = User(
            id=str(uuid.uuid4()),
            username="otherowner",
            email="owner@example.com",
            hashed_password="hash"
        )
        project = Project(
            id=str(uuid.uuid4()),
            name="Private Project",
            owner_id=other_user.id
        )
        
        test_db.add_all([other_user, project])
        test_db.commit()
        
        response = test_client.get(f"/projects/{project.id}", headers=auth_headers)
        
        assert response.status_code == 404
        response_data = response.json()
        assert "Project not found" in response_data.get("detail", response_data.get("message", ""))
    
    def test_update_project(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test updating a project"""
        # Create project as owner
        project = Project(
            id=str(uuid.uuid4()),
            name="Old Name",
            description="Old description",
            owner_id=test_user.id
        )
        test_db.add(project)
        test_db.commit()
        
        update_data = {
            "name": "New Name",
            "description": "New description"
        }
        
        response = test_client.put(f"/projects/{project.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "New description"
    
    def test_update_project_insufficient_permissions(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test updating project without admin permissions"""
        # Create project where user is just a member
        project = Project(
            id=str(uuid.uuid4()),
            name="Test Project",
            owner_id=str(uuid.uuid4())
        )
        member = ProjectMember(
            id=str(uuid.uuid4()),
            project_id=project.id,
            user_id=test_user.id,
            role=ProjectRole.MEMBER  # Not admin
        )
        
        test_db.add_all([project, member])
        test_db.commit()
        
        update_data = {"name": "New Name"}
        
        response = test_client.put(f"/projects/{project.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 403
        response_data = response.json()
        assert "Insufficient permissions" in response_data.get("detail", response_data.get("message", ""))
    
    def test_delete_project_soft(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test soft deleting a project"""
        project = Project(
            id=str(uuid.uuid4()),
            name="To Delete",
            owner_id=test_user.id,
            is_active=True
        )
        test_db.add(project)
        test_db.commit()
        
        project_id = project.id
        response = test_client.delete(f"/projects/{project_id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify soft delete by querying it
        updated_project = test_db.query(Project).filter_by(id=project_id).first()
        assert updated_project is not None
        assert updated_project.is_active is False
    
    def test_delete_project_not_owner(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test deleting project when not owner"""
        project = Project(
            id=str(uuid.uuid4()),
            name="Test Project",
            owner_id=str(uuid.uuid4())
        )
        test_db.add(project)
        test_db.commit()
        
        response = test_client.delete(f"/projects/{project.id}", headers=auth_headers)
        
        assert response.status_code == 404  # No access = not found
    
    def test_add_project_member(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test adding a member to project"""
        # Create project and another user
        project = Project(
            id=str(uuid.uuid4()),
            name="Test Project",
            owner_id=test_user.id
        )
        new_user = User(
            id=str(uuid.uuid4()),
            username="newmember",
            email="new@example.com",
            hashed_password="hash"
        )
        
        test_db.add_all([project, new_user])
        test_db.commit()
        
        member_data = {"role": "member"}
        
        response = test_client.post(
            f"/projects/{project.id}/members/{new_user.id}",
            json=member_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Member added successfully"
        assert "member_id" in data
        
        # Verify member was added
        member = test_db.query(ProjectMember).filter_by(
            project_id=project.id,
            user_id=new_user.id
        ).first()
        assert member is not None
        assert member.role == ProjectRole.MEMBER
    
    def test_update_member_role(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test updating a member's role"""
        # Create project with member
        project = Project(
            id=str(uuid.uuid4()),
            name="Test Project",
            owner_id=test_user.id
        )
        other_user = User(
            id=str(uuid.uuid4()),
            username="member",
            email="member@example.com",
            hashed_password="hash"
        )
        member = ProjectMember(
            id=str(uuid.uuid4()),
            project_id=project.id,
            user_id=other_user.id,
            role=ProjectRole.MEMBER
        )
        
        test_db.add_all([project, other_user, member])
        test_db.commit()
        
        update_data = {"role": "admin"}
        
        response = test_client.put(
            f"/projects/{project.id}/members/{other_user.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Member role updated successfully"
        
        # Verify role was updated
        updated_member = test_db.query(ProjectMember).filter_by(
            project_id=project.id,
            user_id=other_user.id
        ).first()
        assert updated_member.role == ProjectRole.ADMIN
    
    def test_remove_project_member(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test removing a member from project"""
        # Create project with member
        project = Project(
            id=str(uuid.uuid4()),
            name="Test Project",
            owner_id=test_user.id
        )
        other_user = User(
            id=str(uuid.uuid4()),
            username="member",
            email="member@example.com",
            hashed_password="hash"
        )
        member = ProjectMember(
            id=str(uuid.uuid4()),
            project_id=project.id,
            user_id=other_user.id,
            role=ProjectRole.MEMBER
        )
        
        test_db.add_all([project, other_user, member])
        test_db.commit()
        
        response = test_client.delete(
            f"/projects/{project.id}/members/{other_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify member was removed
        member_check = test_db.query(ProjectMember).filter_by(
            project_id=project.id,
            user_id=other_user.id
        ).first()
        assert member_check is None
    
    def test_member_self_remove(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test member removing themselves from project"""
        # Create project where test_user is member (not owner)
        project = Project(
            id=str(uuid.uuid4()),
            name="Test Project",
            owner_id=str(uuid.uuid4())
        )
        member = ProjectMember(
            id=str(uuid.uuid4()),
            project_id=project.id,
            user_id=test_user.id,
            role=ProjectRole.MEMBER
        )
        
        test_db.add_all([project, member])
        test_db.commit()
        
        response = test_client.delete(
            f"/projects/{project.id}/members/{test_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
    
    def test_create_invitation(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test creating a project invitation"""
        project = Project(
            id=str(uuid.uuid4()),
            name="Test Project",
            owner_id=test_user.id
        )
        test_db.add(project)
        test_db.commit()
        
        invitation_data = {
            "invitee_email": "newuser@example.com",
            "role": "member"
        }
        
        response = test_client.post(
            f"/projects/{project.id}/invitations",
            json=invitation_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project.id
        assert data["project_name"] == "Test Project"
        assert data["inviter_name"] == test_user.username
        assert data["invitee_email"] == "newuser@example.com"
        assert data["role"] == "member"
        assert "token" in data
        assert "expires_at" in data
        assert "id" in data
    
    def test_accept_invitation(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test accepting a project invitation"""
        # Create project and invitation
        project = Project(
            id=str(uuid.uuid4()),
            name="Test Project",
            owner_id=str(uuid.uuid4())
        )
        invitation = ProjectInvitation(
            id=str(uuid.uuid4()),
            project_id=project.id,
            inviter_id=project.owner_id,
            invitee_email=test_user.email,
            role=ProjectRole.MEMBER,
            token=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        
        test_db.add_all([project, invitation])
        test_db.commit()
        
        response = test_client.post(
            f"/projects/invitations/{invitation.token}/accept",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Invitation accepted successfully"
        assert data["project_id"] == project.id
        assert data["role"] == "member"
        
        # Verify member was added
        member = test_db.query(ProjectMember).filter_by(
            project_id=project.id,
            user_id=test_user.id
        ).first()
        assert member is not None
        assert member.role == ProjectRole.MEMBER
        
        # Verify invitation was marked as accepted
        updated_invitation = test_db.query(ProjectInvitation).filter_by(id=invitation.id).first()
        assert updated_invitation.accepted_at is not None
    
    def test_accept_invitation_wrong_email(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test accepting invitation meant for different email"""
        invitation = ProjectInvitation(
            id=str(uuid.uuid4()),
            project_id=str(uuid.uuid4()),
            inviter_id=str(uuid.uuid4()),
            invitee_email="other@example.com",  # Different email
            role=ProjectRole.MEMBER,
            token=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        
        test_db.add(invitation)
        test_db.commit()
        
        response = test_client.post(
            f"/projects/invitations/{invitation.token}/accept",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        response_data = response.json()
        assert "This invitation is not for you" in response_data.get("detail", response_data.get("message", ""))
    
    def test_project_permissions(self, test_client: TestClient, test_user: User, auth_headers: dict, test_db: Session):
        """Test project permission hierarchy"""
        # Create users with different roles
        viewer_user = User(id=str(uuid.uuid4()), username="viewer", email="viewer@example.com", hashed_password="hash")
        member_user = User(id=str(uuid.uuid4()), username="member", email="member@example.com", hashed_password="hash")
        admin_user = User(id=str(uuid.uuid4()), username="admin", email="admin@example.com", hashed_password="hash")
        
        # Create project with members
        project = Project(
            id=str(uuid.uuid4()),
            name="Test Project",
            owner_id=test_user.id  # test_user is owner
        )
        
        viewer_member = ProjectMember(id=str(uuid.uuid4()), project_id=project.id, user_id=viewer_user.id, role=ProjectRole.VIEWER)
        member_member = ProjectMember(id=str(uuid.uuid4()), project_id=project.id, user_id=member_user.id, role=ProjectRole.MEMBER)
        admin_member = ProjectMember(id=str(uuid.uuid4()), project_id=project.id, user_id=admin_user.id, role=ProjectRole.ADMIN)
        
        test_db.add_all([viewer_user, member_user, admin_user, project, viewer_member, member_member, admin_member])
        test_db.commit()
        
        # Test permissions in project model
        assert project.has_permission(test_user.id, ProjectRole.VIEWER) is True  # Owner has all permissions
        assert project.has_permission(test_user.id, ProjectRole.OWNER) is True
        
        assert project.has_permission(viewer_user.id, ProjectRole.VIEWER) is True
        assert project.has_permission(viewer_user.id, ProjectRole.MEMBER) is False
        
        assert project.has_permission(member_user.id, ProjectRole.MEMBER) is True
        assert project.has_permission(member_user.id, ProjectRole.ADMIN) is False
        
        assert project.has_permission(admin_user.id, ProjectRole.ADMIN) is True
        assert project.has_permission(admin_user.id, ProjectRole.OWNER) is False