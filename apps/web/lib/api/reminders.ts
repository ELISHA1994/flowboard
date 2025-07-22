import { ApiClient } from '@/lib/api-client';

export interface TaskReminder {
  id: string;
  task_id: string;
  user_id: string;
  remind_at: string;
  reminder_type: 'due_date' | 'custom';
  offset_minutes?: number;
  message?: string;
  sent: boolean;
  sent_at?: string;
  created_at: string;
}

export interface TaskReminderCreate {
  task_id: string;
  remind_at: string;
  reminder_type: 'due_date' | 'custom';
  offset_minutes?: number;
  message?: string;
}

export interface TaskReminderUpdate {
  remind_at?: string;
  message?: string;
}

export interface TaskDueDateRemindersCreate {
  task_id: string;
  offset_minutes: number[];
}

export interface NotificationPreferences {
  user_id: string;
  in_app_notifications: boolean;
  email_notifications: boolean;
  notification_frequency: 'immediate' | 'daily_digest' | 'weekly_digest';
  reminder_notifications: boolean;
  task_assignment_notifications: boolean;
  task_completion_notifications: boolean;
  comment_notifications: boolean;
  project_notifications: boolean;
  created_at: string;
  updated_at?: string;
}

export interface NotificationPreferencesUpdate {
  in_app_notifications?: boolean;
  email_notifications?: boolean;
  notification_frequency?: 'immediate' | 'daily_digest' | 'weekly_digest';
  reminder_notifications?: boolean;
  task_assignment_notifications?: boolean;
  task_completion_notifications?: boolean;
  comment_notifications?: boolean;
  project_notifications?: boolean;
}

export class RemindersService {
  static async createTaskReminder(reminder: TaskReminderCreate): Promise<TaskReminder> {
    return ApiClient.fetchJSON(ApiClient.buildUrl('/notifications/reminders'), {
      method: 'POST',
      body: JSON.stringify(reminder),
    });
  }

  static async createDueDateReminders(data: TaskDueDateRemindersCreate): Promise<TaskReminder[]> {
    return ApiClient.fetchJSON(ApiClient.buildUrl('/notifications/reminders/due-date'), {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  static async getTaskReminders(taskId: string): Promise<TaskReminder[]> {
    return ApiClient.fetchJSON(ApiClient.buildUrl(`/notifications/reminders?task_id=${taskId}`));
  }

  static async updateTaskReminder(
    reminderId: string,
    update: TaskReminderUpdate
  ): Promise<TaskReminder> {
    return ApiClient.fetchJSON(ApiClient.buildUrl(`/notifications/reminders/${reminderId}`), {
      method: 'PUT',
      body: JSON.stringify(update),
    });
  }

  static async deleteTaskReminder(reminderId: string): Promise<void> {
    await ApiClient.fetchJSON(ApiClient.buildUrl(`/notifications/reminders/${reminderId}`), {
      method: 'DELETE',
    });
  }

  static async getNotificationPreferences(): Promise<NotificationPreferences> {
    return ApiClient.fetchJSON(ApiClient.buildUrl('/notifications/preferences'));
  }

  static async updateNotificationPreferences(
    preferences: NotificationPreferencesUpdate
  ): Promise<NotificationPreferences> {
    return ApiClient.fetchJSON(ApiClient.buildUrl('/notifications/preferences'), {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  }

  static async processReminders(): Promise<void> {
    await ApiClient.fetchJSON(ApiClient.buildUrl('/notifications/process-reminders'), {
      method: 'POST',
    });
  }
}
