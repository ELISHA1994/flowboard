"""
Unit tests for ProjectService
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import (Project, ProjectInvitation, ProjectMember,
                           ProjectRole, User)
from app.models.project import (ProjectCreate, ProjectDetailResponse,
                                ProjectInvitationCreate, ProjectResponse,
                                ProjectUpdate)
from app.services.project_service import ProjectService


@pytest.mark.unit
class TestProjectService:
    """Test ProjectService methods"""

    def test_create_project_success(self, mock_db):
        """Test successful project creation"""
        # Arrange
        project_data = ProjectCreate(name="Test Project", description="A test project")
        owner_id = "user123"

        # Act
        project = ProjectService.create_project(mock_db, project_data, owner_id)

        # Assert
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.owner_id == owner_id
        assert project.is_active is True
        assert project.id is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_project_integrity_error(self, mock_db):
        """Test project creation with database error"""
        # Arrange
        project_data = ProjectCreate(name="Test Project")
        owner_id = "user123"
        mock_db.commit.side_effect = IntegrityError("", "", "")

        # Act & Assert
        with pytest.raises(ValueError, match="Project creation failed"):
            ProjectService.create_project(mock_db, project_data, owner_id)
        mock_db.rollback.assert_called_once()

    def test_get_user_projects_active_only(self, mock_db):
        """Test getting user's active projects"""
        # Arrange
        user_id = "user123"
        projects = [
            Project(id="p1", name="Project 1", owner_id=user_id, is_active=True),
            Project(id="p2", name="Project 2", owner_id="other", is_active=True),
        ]

        mock_query = Mock()
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = projects[:1]
        mock_db.query.return_value = mock_query

        # Act
        result = ProjectService.get_user_projects(
            mock_db, user_id, include_inactive=False
        )

        # Assert
        assert len(result) == 1
        assert result[0].name == "Project 1"

    def test_get_project_by_id_owner_access(self, mock_db):
        """Test getting project by ID when user is owner"""
        # Arrange
        user_id = "user123"
        project_id = "project123"
        project = Project(
            id=project_id,
            name="Test Project",
            owner_id=user_id,
            owner=User(id=user_id, username="testuser", email="test@example.com"),
            members=[],
        )

        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = project
        mock_db.query.return_value = mock_query

        # Act
        result = ProjectService.get_project_by_id(mock_db, project_id, user_id)

        # Assert
        assert result == project
        assert result.owner_id == user_id

    def test_get_project_by_id_member_access(self, mock_db):
        """Test getting project by ID when user is member"""
        # Arrange
        user_id = "user123"
        project_id = "project123"
        project = Project(
            id=project_id, name="Test Project", owner_id="owner123", members=[]
        )
        member = ProjectMember(user_id=user_id, project_id=project_id)

        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [project, member]
        mock_db.query.return_value = mock_query

        # Act
        result = ProjectService.get_project_by_id(mock_db, project_id, user_id)

        # Assert
        assert result == project

    def test_get_project_by_id_no_access(self, mock_db):
        """Test getting project by ID when user has no access"""
        # Arrange
        user_id = "user123"
        project_id = "project123"
        project = Project(
            id=project_id, name="Test Project", owner_id="owner123", members=[]
        )

        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [project, None]
        mock_db.query.return_value = mock_query

        # Act
        result = ProjectService.get_project_by_id(mock_db, project_id, user_id)

        # Assert
        assert result is None

    def test_update_project_success(self, mock_db):
        """Test successful project update"""
        # Arrange
        old_time = datetime.now(timezone.utc) - timedelta(days=1)
        project = Project(
            id="project123",
            name="Old Name",
            description="Old description",
            updated_at=old_time,
        )
        update_data = ProjectUpdate(name="New Name", description="New description")

        # Act
        result = ProjectService.update_project(mock_db, project, update_data)

        # Assert
        assert result.name == "New Name"
        assert result.description == "New description"
        assert result.updated_at > old_time
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_soft_delete_project(self, mock_db):
        """Test soft deleting a project"""
        # Arrange
        old_time = datetime.now(timezone.utc) - timedelta(days=1)
        project = Project(
            id="project123", name="Test Project", is_active=True, updated_at=old_time
        )

        # Act
        result = ProjectService.soft_delete_project(mock_db, project)

        # Assert
        assert result.is_active is False
        assert result.updated_at > old_time
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_add_member_success(self, mock_db):
        """Test successfully adding a member to project"""
        # Arrange
        project_id = "project123"
        user_id = "user123"
        role = ProjectRole.MEMBER
        user = User(id=user_id, username="testuser", email="test@example.com")

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [user, None]  # User exists, not already member
        mock_db.query.return_value = mock_query

        # Act
        member = ProjectService.add_member(mock_db, project_id, user_id, role)

        # Assert
        assert member.project_id == project_id
        assert member.user_id == user_id
        assert member.role == role
        assert member.id is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_add_member_user_not_found(self, mock_db):
        """Test adding member when user doesn't exist"""
        # Arrange
        project_id = "project123"
        user_id = "user123"
        role = ProjectRole.MEMBER

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            ProjectService.add_member(mock_db, project_id, user_id, role)

    def test_add_member_already_exists(self, mock_db):
        """Test adding member who is already a member"""
        # Arrange
        project_id = "project123"
        user_id = "user123"
        role = ProjectRole.MEMBER
        user = User(id=user_id, username="testuser", email="test@example.com")
        existing_member = ProjectMember(user_id=user_id, project_id=project_id)

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [user, existing_member]
        mock_db.query.return_value = mock_query

        # Act & Assert
        with pytest.raises(ValueError, match="User is already a project member"):
            ProjectService.add_member(mock_db, project_id, user_id, role)

    def test_create_invitation_success(self, mock_db):
        """Test successfully creating a project invitation"""
        # Arrange
        project_id = "project123"
        inviter_id = "inviter123"
        invitation_data = ProjectInvitationCreate(
            invitee_email="newuser@example.com", role=ProjectRole.MEMBER
        )

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [
            None,
            None,
        ]  # No existing user, no existing invitation
        mock_db.query.return_value = mock_query

        # Act
        invitation = ProjectService.create_invitation(
            mock_db, project_id, inviter_id, invitation_data
        )

        # Assert
        assert invitation.project_id == project_id
        assert invitation.inviter_id == inviter_id
        assert invitation.invitee_email == "newuser@example.com"
        assert invitation.role == ProjectRole.MEMBER
        assert invitation.expires_at > datetime.now(timezone.utc)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_invitation_user_already_member(self, mock_db):
        """Test creating invitation for existing member"""
        # Arrange
        project_id = "project123"
        inviter_id = "inviter123"
        invitation_data = ProjectInvitationCreate(
            invitee_email="existing@example.com", role=ProjectRole.MEMBER
        )
        existing_user = User(id="user123", email="existing@example.com")
        existing_member = ProjectMember(user_id="user123", project_id=project_id)

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [existing_user, existing_member]
        mock_db.query.return_value = mock_query

        # Act & Assert
        with pytest.raises(ValueError, match="User is already a project member"):
            ProjectService.create_invitation(
                mock_db, project_id, inviter_id, invitation_data
            )

    def test_accept_invitation_success(self, mock_db):
        """Test successfully accepting an invitation"""
        # Arrange
        user = User(id="user123", email="test@example.com")
        invitation = ProjectInvitation(
            id="inv123",
            project_id="project123",
            invitee_email="test@example.com",
            role=ProjectRole.MEMBER,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            accepted_at=None,
        )

        # Mock add_member to return a member
        with patch.object(ProjectService, "add_member") as mock_add_member:
            mock_member = ProjectMember(
                id="member123",
                project_id="project123",
                user_id="user123",
                role=ProjectRole.MEMBER,
            )
            mock_add_member.return_value = mock_member

            # Act
            result = ProjectService.accept_invitation(mock_db, invitation, user)

            # Assert
            assert result == mock_member
            assert invitation.accepted_at is not None
            mock_add_member.assert_called_once_with(
                mock_db, "project123", "user123", ProjectRole.MEMBER
            )
            mock_db.commit.assert_called_once()

    def test_accept_invitation_wrong_email(self, mock_db):
        """Test accepting invitation with wrong email"""
        # Arrange
        user = User(id="user123", email="wrong@example.com")
        invitation = ProjectInvitation(
            invitee_email="test@example.com",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )

        # Act & Assert
        with pytest.raises(ValueError, match="This invitation is not for you"):
            ProjectService.accept_invitation(mock_db, invitation, user)

    def test_accept_invitation_already_accepted(self, mock_db):
        """Test accepting already accepted invitation"""
        # Arrange
        user = User(id="user123", email="test@example.com")
        invitation = ProjectInvitation(
            invitee_email="test@example.com",
            accepted_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invitation has already been accepted"):
            ProjectService.accept_invitation(mock_db, invitation, user)

    def test_accept_invitation_expired(self, mock_db):
        """Test accepting expired invitation"""
        # Arrange
        user = User(id="user123", email="test@example.com")
        invitation = ProjectInvitation(
            invitee_email="test@example.com",
            accepted_at=None,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invitation has expired"):
            ProjectService.accept_invitation(mock_db, invitation, user)

    def test_to_response(self, mock_db):
        """Test converting project to response model"""
        # Arrange
        user_id = "user123"
        project = Mock(spec=Project)
        project.id = "project123"
        project.name = "Test Project"
        project.description = "Test description"
        project.color = "#FF5733"  # Add color attribute
        project.owner_id = user_id
        project.owner = Mock(spec=User, id=user_id, username="testuser")
        project.is_active = True
        project.created_at = datetime.now(timezone.utc)
        project.updated_at = datetime.now(timezone.utc)
        project.tasks = [Mock(), Mock()]  # 2 tasks
        project.members = [Mock()]  # 1 member
        project.get_member_role = Mock(return_value=ProjectRole.OWNER)

        # Act
        response = ProjectService.to_response(project, user_id, mock_db)

        # Assert
        assert isinstance(response, ProjectResponse)
        assert response.id == "project123"
        assert response.name == "Test Project"
        assert response.owner_username == "testuser"
        assert response.task_count == 2
        assert response.member_count == 2  # owner + 1 member
        assert response.user_role == ProjectRole.OWNER
        project.get_member_role.assert_called_once_with(user_id)

    def test_to_detail_response(self, mock_db):
        """Test converting project to detailed response model"""
        # Arrange
        user_id = "user123"

        # Create mock project
        project = Mock(spec=Project)
        project.id = "project123"
        project.name = "Test Project"
        project.description = "Test description"
        project.color = "#FF5733"  # Add color attribute
        project.owner_id = user_id
        project.owner = Mock(
            spec=User, id=user_id, username="owner", email="owner@example.com"
        )
        project.is_active = True
        project.created_at = datetime.now(timezone.utc)
        project.updated_at = datetime.now(timezone.utc)
        project.tasks = []

        # Create mock member
        member_mock = Mock(spec=ProjectMember)
        member_mock.id = "m1"
        member_mock.user = Mock(
            spec=User, id="member123", username="member", email="member@example.com"
        )
        member_mock.role = ProjectRole.MEMBER
        member_mock.joined_at = datetime.now(timezone.utc)

        project.members = [member_mock]
        project.get_member_role = Mock(return_value=ProjectRole.OWNER)

        # Act
        response = ProjectService.to_detail_response(project, user_id, mock_db)

        # Assert
        assert isinstance(response, ProjectDetailResponse)
        assert len(response.members) == 2  # owner + member
        assert response.members[0].username == "owner"
        assert response.members[0].role == ProjectRole.OWNER
        assert response.members[1].username == "member"
        assert response.members[1].role == ProjectRole.MEMBER
