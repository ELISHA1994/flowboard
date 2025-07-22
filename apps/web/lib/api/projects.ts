import { ApiClient } from '@/lib/api-client';

export type ProjectRole = 'owner' | 'admin' | 'member' | 'viewer';

export interface Project {
  id: string;
  name: string;
  description?: string;
  color?: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
}

export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: string;
  role: ProjectRole;
  joined_at: string;
  user: User;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  color?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
  color?: string;
}

export interface AddProjectMemberRequest {
  user_id: string;
  role: 'ADMIN' | 'MEMBER' | 'VIEWER';
}

export interface UpdateMemberRoleRequest {
  role: 'ADMIN' | 'MEMBER' | 'VIEWER';
}

export class ProjectsService {
  private static async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    return ApiClient.fetchJSON(ApiClient.buildUrl(endpoint), options);
  }

  // Get all projects
  static async getProjects(): Promise<Project[]> {
    return this.makeRequest<Project[]>('/projects');
  }

  // Get single project
  static async getProject(projectId: string): Promise<Project> {
    return this.makeRequest<Project>(`/projects/${projectId}`);
  }

  // Create project
  static async createProject(data: CreateProjectRequest): Promise<Project> {
    return this.makeRequest<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Update project
  static async updateProject(projectId: string, data: UpdateProjectRequest): Promise<Project> {
    return this.makeRequest<Project>(`/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Delete project
  static async deleteProject(projectId: string): Promise<void> {
    await this.makeRequest<void>(`/projects/${projectId}`, {
      method: 'DELETE',
    });
  }

  // Get project members
  static async getProjectMembers(projectId: string): Promise<ProjectMember[]> {
    const response = await this.makeRequest<any[]>(`/projects/${projectId}/members`);

    // Transform flat backend response to nested structure expected by frontend
    return response.map((member) => ({
      ...member,
      user: {
        id: member.user_id,
        username: member.username,
        email: member.email,
      },
    }));
  }

  // Search users by email
  static async searchUsers(email: string): Promise<User[]> {
    // For now, we'll use a simple implementation that searches for exact email match
    // In a real implementation, this would call a user search endpoint
    try {
      // Mock implementation - replace with actual API call when available
      const response = await this.makeRequest<any[]>('/users');
      return response.filter((user) => user.email.toLowerCase().includes(email.toLowerCase()));
    } catch (error) {
      // If users endpoint doesn't exist, return empty array
      console.warn('User search not implemented in backend');
      return [];
    }
  }

  // Add project member
  static async addProjectMember(
    projectId: string,
    userId: string,
    role: ProjectRole
  ): Promise<ProjectMember> {
    return this.makeRequest<ProjectMember>(`/projects/${projectId}/members`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, role }),
    });
  }

  // Update member role
  static async updateProjectMemberRole(
    projectId: string,
    userId: string,
    role: ProjectRole
  ): Promise<ProjectMember> {
    return this.makeRequest<ProjectMember>(`/projects/${projectId}/members/${userId}`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    });
  }

  // Remove project member
  static async removeProjectMember(projectId: string, userId: string): Promise<void> {
    await this.makeRequest<void>(`/projects/${projectId}/members/${userId}`, {
      method: 'DELETE',
    });
  }

  // Get project role for current user
  static getUserRole(
    project: Project,
    members: ProjectMember[],
    currentUserId: string
  ): ProjectMember['role'] | null {
    const member = members.find((m) => m.user_id === currentUserId);
    return member?.role || null;
  }

  // Check if user can edit project
  static canEditProject(role: ProjectMember['role'] | null): boolean {
    return role === 'owner' || role === 'admin';
  }

  // Check if user can manage members
  static canManageMembers(role: ProjectMember['role'] | null): boolean {
    return role === 'owner' || role === 'admin';
  }

  // Format project color for display
  static formatProjectColor(color?: string): string {
    return color || '#6366f1'; // Default indigo color
  }
}
