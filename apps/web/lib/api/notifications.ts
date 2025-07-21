import { AuthService } from '@/lib/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  data?: Record<string, any>;
  read: boolean;
  read_at?: string;
  created_at: string;
}

export interface NotificationStats {
  total: number;
  unread: number;
  by_type: Record<string, number>;
}

export interface ActivityItem {
  id: string;
  user: string;
  user_initials: string;
  action: string;
  task?: string;
  project?: string;
  message?: string;
  time: string;
  type: string;
}

export class NotificationsService {
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

  static async getNotifications(params?: {
    unread_only?: boolean;
    notification_type?: string;
    skip?: number;
    limit?: number;
  }): Promise<Notification[]> {
    const queryParams = new URLSearchParams();

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }

    const url = `${API_BASE_URL}/notifications${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return this.fetchWithAuth(url);
  }

  static async getNotificationStats(): Promise<NotificationStats> {
    return this.fetchWithAuth(`${API_BASE_URL}/notifications/stats`);
  }

  static async markNotificationRead(notificationId: string): Promise<void> {
    await this.fetchWithAuth(`${API_BASE_URL}/notifications/read/${notificationId}`, {
      method: 'PUT',
    });
  }

  static async markAllNotificationsRead(notificationType?: string): Promise<void> {
    const queryParams = notificationType ? `?notification_type=${notificationType}` : '';
    await this.fetchWithAuth(`${API_BASE_URL}/notifications/read-all${queryParams}`, {
      method: 'PUT',
    });
  }

  static async deleteNotification(notificationId: string): Promise<void> {
    await this.fetchWithAuth(`${API_BASE_URL}/notifications/${notificationId}`, {
      method: 'DELETE',
    });
  }

  // Transform notifications into activity items for the dashboard
  static notificationsToActivityItems(notifications: Notification[]): ActivityItem[] {
    return notifications.map((notification) => {
      const data = notification.data || {};

      // Extract user information
      const user = data.user_name || data.created_by || 'System';
      const userInitials = user
        .split(' ')
        .map((n: string) => n[0])
        .join('')
        .toUpperCase();

      // Map notification types to human-readable actions
      const actionMap: Record<string, string> = {
        task_assigned: 'assigned',
        task_completed: 'completed',
        task_updated: 'updated',
        task_created: 'created',
        comment_added: 'commented on',
        comment_mention: 'mentioned you in',
        project_invite: 'invited you to',
        task_due: 'is due',
        task_overdue: 'is overdue',
      };

      const action = actionMap[notification.type] || notification.type;

      // Calculate relative time
      const time = this.getRelativeTime(notification.created_at);

      return {
        id: notification.id,
        user,
        user_initials: userInitials,
        action,
        task: data.task_title,
        project: data.project_name,
        message: notification.message,
        time,
        type: notification.type,
      };
    });
  }

  private static getRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInMinutes = Math.floor(diffInMs / 60000);
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);

    if (diffInMinutes < 1) {
      return 'just now';
    } else if (diffInMinutes < 60) {
      return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
    } else if (diffInHours < 24) {
      return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
    } else if (diffInDays < 7) {
      return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString();
    }
  }
}
