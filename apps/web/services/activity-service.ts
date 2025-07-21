/**
 * Frontend service for task activity tracking API interactions
 */
import { ApiClient } from '@/lib/api-client';

export interface ActivityType {
  CREATED: 'created';
  STATUS_CHANGED: 'status_changed';
  PRIORITY_CHANGED: 'priority_changed';
  ASSIGNED: 'assigned';
  UNASSIGNED: 'unassigned';
  DUE_DATE_CHANGED: 'due_date_changed';
  START_DATE_CHANGED: 'start_date_changed';
  TITLE_CHANGED: 'title_changed';
  DESCRIPTION_CHANGED: 'description_changed';
  COMMENT_ADDED: 'comment_added';
  COMMENT_EDITED: 'comment_edited';
  COMMENT_DELETED: 'comment_deleted';
  ATTACHMENT_ADDED: 'attachment_added';
  ATTACHMENT_DELETED: 'attachment_deleted';
  TIME_LOGGED: 'time_logged';
  DEPENDENCY_ADDED: 'dependency_added';
  DEPENDENCY_REMOVED: 'dependency_removed';
  SUBTASK_ADDED: 'subtask_added';
  SUBTASK_REMOVED: 'subtask_removed';
  SHARED: 'shared';
  UNSHARED: 'unshared';
  PROJECT_CHANGED: 'project_changed';
  TAG_ADDED: 'tag_added';
  TAG_REMOVED: 'tag_removed';
  CATEGORY_ADDED: 'category_added';
  CATEGORY_REMOVED: 'category_removed';
  COMPLETED: 'completed';
  REOPENED: 'reopened';
  DELETED: 'deleted';
}

export interface Activity {
  id: string;
  task_id: string;
  user_id: string | null;
  activity_type: keyof ActivityType;
  details: any | null;
  old_value: string | null;
  new_value: string | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
  user: {
    id: string;
    username: string;
    email: string;
  } | null;
}

export interface ActivityListResponse {
  activities: Activity[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ActivityFilter {
  task_id?: string;
  user_id?: string;
  activity_types?: (keyof ActivityType)[];
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export interface ActivityStats {
  total_activities: number;
  activities_by_type: Record<string, number>;
  activities_by_user: Record<string, number>;
  most_active_day: string | null;
  most_active_hour: number | null;
}

export interface TaskActivityOverview {
  task_id: string;
  task_title: string;
  total_activities: number;
  latest_activity: Activity | null;
  activity_types: string[];
  contributors: Array<{ id: string; username: string }>;
  first_activity_date: string | null;
  last_activity_date: string | null;
}

export interface ActivityCreate {
  task_id: string;
  user_id?: string;
  activity_type: keyof ActivityType;
  details?: any;
  old_value?: string;
  new_value?: string;
  ip_address?: string;
  user_agent?: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ActivityService {
  private static async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    return ApiClient.fetchJSON<T>(url, options);
  }

  /**
   * Get activities for a specific task
   */
  static async getTaskActivities(
    taskId: string,
    options: {
      limit?: number;
      offset?: number;
      activity_types?: (keyof ActivityType)[];
    } = {}
  ): Promise<ActivityListResponse> {
    const params = new URLSearchParams();

    if (options.limit) params.append('limit', options.limit.toString());
    if (options.offset) params.append('offset', options.offset.toString());
    if (options.activity_types?.length) {
      options.activity_types.forEach((type) => params.append('activity_types', type));
    }

    const queryString = params.toString();
    const endpoint = `/tasks/${taskId}/activities${queryString ? `?${queryString}` : ''}`;

    return this.makeRequest<ActivityListResponse>(endpoint);
  }

  /**
   * Get activities performed by a specific user
   */
  static async getUserActivities(
    userId: string,
    options: {
      limit?: number;
      offset?: number;
      activity_types?: (keyof ActivityType)[];
    } = {}
  ): Promise<ActivityListResponse> {
    const params = new URLSearchParams();

    if (options.limit) params.append('limit', options.limit.toString());
    if (options.offset) params.append('offset', options.offset.toString());
    if (options.activity_types?.length) {
      options.activity_types.forEach((type) => params.append('activity_types', type));
    }

    const queryString = params.toString();
    const endpoint = `/users/${userId}/activities${queryString ? `?${queryString}` : ''}`;

    return this.makeRequest<ActivityListResponse>(endpoint);
  }

  /**
   * Get a specific activity by ID
   */
  static async getActivity(activityId: string): Promise<Activity> {
    return this.makeRequest<Activity>(`/activities/${activityId}`);
  }

  /**
   * Create a new activity (mainly for admin/system use)
   */
  static async createActivity(activityData: ActivityCreate): Promise<Activity> {
    return this.makeRequest<Activity>('/activities', {
      method: 'POST',
      body: JSON.stringify(activityData),
    });
  }

  /**
   * Create multiple activities in bulk
   */
  static async createBulkActivities(activities: ActivityCreate[]): Promise<Activity[]> {
    return this.makeRequest<Activity[]>('/activities/bulk', {
      method: 'POST',
      body: JSON.stringify({ activities }),
    });
  }

  /**
   * Get an overview of all activities for a specific task
   */
  static async getTaskActivityOverview(taskId: string): Promise<TaskActivityOverview> {
    return this.makeRequest<TaskActivityOverview>(`/tasks/${taskId}/activities/overview`);
  }

  /**
   * Get activity statistics with optional filters
   */
  static async getActivityStats(
    options: {
      task_id?: string;
      user_id?: string;
      start_date?: string;
      end_date?: string;
    } = {}
  ): Promise<ActivityStats> {
    const params = new URLSearchParams();

    if (options.task_id) params.append('task_id', options.task_id);
    if (options.user_id) params.append('user_id', options.user_id);
    if (options.start_date) params.append('start_date', options.start_date);
    if (options.end_date) params.append('end_date', options.end_date);

    const queryString = params.toString();
    const endpoint = `/activities/stats${queryString ? `?${queryString}` : ''}`;

    return this.makeRequest<ActivityStats>(endpoint);
  }

  /**
   * Clean up old activity records (admin only)
   */
  static async cleanupOldActivities(
    days: number = 365
  ): Promise<{ success: boolean; message: string }> {
    const params = new URLSearchParams();
    params.append('days', days.toString());

    return this.makeRequest<{ success: boolean; message: string }>(
      `/activities/cleanup?${params.toString()}`,
      { method: 'DELETE' }
    );
  }

  /**
   * Format activity type for display
   */
  static formatActivityType(activityType: keyof ActivityType): string {
    const typeMap: Record<keyof ActivityType, string> = {
      CREATED: 'Created',
      STATUS_CHANGED: 'Status Changed',
      PRIORITY_CHANGED: 'Priority Changed',
      ASSIGNED: 'Assigned',
      UNASSIGNED: 'Unassigned',
      DUE_DATE_CHANGED: 'Due Date Changed',
      START_DATE_CHANGED: 'Start Date Changed',
      TITLE_CHANGED: 'Title Changed',
      DESCRIPTION_CHANGED: 'Description Changed',
      COMMENT_ADDED: 'Comment Added',
      COMMENT_EDITED: 'Comment Edited',
      COMMENT_DELETED: 'Comment Deleted',
      ATTACHMENT_ADDED: 'File Attached',
      ATTACHMENT_DELETED: 'File Deleted',
      TIME_LOGGED: 'Time Logged',
      DEPENDENCY_ADDED: 'Dependency Added',
      DEPENDENCY_REMOVED: 'Dependency Removed',
      SUBTASK_ADDED: 'Subtask Added',
      SUBTASK_REMOVED: 'Subtask Removed',
      SHARED: 'Task Shared',
      UNSHARED: 'Sharing Removed',
      PROJECT_CHANGED: 'Project Changed',
      TAG_ADDED: 'Tag Added',
      TAG_REMOVED: 'Tag Removed',
      CATEGORY_ADDED: 'Category Added',
      CATEGORY_REMOVED: 'Category Removed',
      COMPLETED: 'Completed',
      REOPENED: 'Reopened',
      DELETED: 'Deleted',
    };

    return typeMap[activityType] || activityType;
  }

  /**
   * Format activity description for display
   */
  static formatActivityDescription(activity: Activity): string {
    const { activity_type, old_value, new_value, details, user } = activity;
    const userName = user?.username || 'Unknown User';

    switch (activity_type) {
      case 'CREATED':
        return `${userName} created this task`;

      case 'STATUS_CHANGED':
        return `${userName} changed status from "${old_value}" to "${new_value}"`;

      case 'PRIORITY_CHANGED':
        return `${userName} changed priority from "${old_value}" to "${new_value}"`;

      case 'ASSIGNED':
        if (old_value && new_value) {
          return `${userName} reassigned the task`;
        } else if (new_value) {
          return `${userName} assigned the task`;
        } else {
          return `${userName} unassigned the task`;
        }

      case 'DUE_DATE_CHANGED':
        if (old_value && new_value) {
          return `${userName} changed due date from ${new Date(old_value).toLocaleDateString()} to ${new Date(new_value).toLocaleDateString()}`;
        } else if (new_value) {
          return `${userName} set due date to ${new Date(new_value).toLocaleDateString()}`;
        } else {
          return `${userName} removed due date`;
        }

      case 'TITLE_CHANGED':
        return `${userName} changed title from "${old_value}" to "${new_value}"`;

      case 'DESCRIPTION_CHANGED':
        return `${userName} updated the description`;

      case 'COMMENT_ADDED':
        return `${userName} added a comment`;

      case 'ATTACHMENT_ADDED':
        const filename = details?.filename || 'a file';
        return `${userName} attached ${filename}`;

      case 'TIME_LOGGED':
        const hours = details?.hours || new_value;
        return `${userName} logged ${hours} hours`;

      case 'SUBTASK_ADDED':
        const subtaskTitle = details?.subtask_title || 'a subtask';
        return `${userName} added subtask "${subtaskTitle}"`;

      case 'COMPLETED':
        return `${userName} completed this task`;

      case 'REOPENED':
        return `${userName} reopened this task`;

      case 'DELETED':
        return `${userName} deleted this task`;

      case 'SHARED':
        return `${userName} shared this task`;

      default:
        return `${userName} ${this.formatActivityType(activity_type).toLowerCase()}`;
    }
  }

  /**
   * Get activity icon for display
   */
  static getActivityIcon(activityType: keyof ActivityType): string {
    const iconMap: Record<keyof ActivityType, string> = {
      CREATED: '🆕',
      STATUS_CHANGED: '🔄',
      PRIORITY_CHANGED: '⚡',
      ASSIGNED: '👤',
      UNASSIGNED: '👤',
      DUE_DATE_CHANGED: '📅',
      START_DATE_CHANGED: '📅',
      TITLE_CHANGED: '✏️',
      DESCRIPTION_CHANGED: '📝',
      COMMENT_ADDED: '💬',
      COMMENT_EDITED: '✏️',
      COMMENT_DELETED: '🗑️',
      ATTACHMENT_ADDED: '📎',
      ATTACHMENT_DELETED: '🗑️',
      TIME_LOGGED: '⏱️',
      DEPENDENCY_ADDED: '🔗',
      DEPENDENCY_REMOVED: '🔗',
      SUBTASK_ADDED: '📋',
      SUBTASK_REMOVED: '📋',
      SHARED: '🔗',
      UNSHARED: '🔗',
      PROJECT_CHANGED: '📁',
      TAG_ADDED: '🏷️',
      TAG_REMOVED: '🏷️',
      CATEGORY_ADDED: '📂',
      CATEGORY_REMOVED: '📂',
      COMPLETED: '✅',
      REOPENED: '🔄',
      DELETED: '🗑️',
    };

    return iconMap[activityType] || '📝';
  }

  /**
   * Get relative time string for activity
   */
  static getRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) {
      return 'just now';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours} hour${hours === 1 ? '' : 's'} ago`;
    } else if (diffInSeconds < 2592000) {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days} day${days === 1 ? '' : 's'} ago`;
    } else {
      return date.toLocaleDateString();
    }
  }
}
