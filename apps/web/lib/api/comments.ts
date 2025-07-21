import { AuthService } from '@/lib/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Comment {
  id: string;
  task_id: string;
  user_id: string;
  parent_comment_id: string | null;
  content: string;
  created_at: string;
  updated_at: string;
  is_edited: boolean;
  user: {
    id: string;
    username: string;
    email: string;
  };
  mentions: Array<{
    id: string;
    username: string;
    email: string;
  }>;
  replies: Comment[];
}

export interface CommentCreate {
  content: string;
  parent_comment_id?: string;
}

export interface CommentUpdate {
  content: string;
}

export class CommentsService {
  private static async fetchWithAuth(url: string, options: RequestInit = {}) {
    const token = AuthService.getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `Request failed with status ${response.status}`);
    }

    return response.json();
  }

  static async createComment(taskId: string, data: CommentCreate): Promise<Comment> {
    return this.fetchWithAuth(`${API_BASE_URL}/tasks/${taskId}/comments`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  static async getTaskComments(taskId: string, includeReplies: boolean = true): Promise<Comment[]> {
    const params = new URLSearchParams({
      include_replies: includeReplies.toString(),
    });
    return this.fetchWithAuth(`${API_BASE_URL}/tasks/${taskId}/comments?${params}`);
  }

  static async updateComment(commentId: string, data: CommentUpdate): Promise<Comment> {
    return this.fetchWithAuth(`${API_BASE_URL}/comments/${commentId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  static async deleteComment(commentId: string): Promise<void> {
    await this.fetchWithAuth(`${API_BASE_URL}/comments/${commentId}`, {
      method: 'DELETE',
    });
  }
}
