import { ApiClient } from '@/lib/api-client';

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
  static async createComment(taskId: string, data: CommentCreate): Promise<Comment> {
    return ApiClient.fetchJSON(ApiClient.buildUrl(`/tasks/${taskId}/comments`), {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  static async getTaskComments(taskId: string, includeReplies: boolean = true): Promise<Comment[]> {
    const params = new URLSearchParams({
      include_replies: includeReplies.toString(),
    });
    return ApiClient.fetchJSON(ApiClient.buildUrl(`/tasks/${taskId}/comments?${params}`));
  }

  static async updateComment(commentId: string, data: CommentUpdate): Promise<Comment> {
    return ApiClient.fetchJSON(ApiClient.buildUrl(`/comments/${commentId}`), {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  static async deleteComment(commentId: string): Promise<void> {
    await ApiClient.fetchJSON(ApiClient.buildUrl(`/comments/${commentId}`), {
      method: 'DELETE',
    });
  }
}
