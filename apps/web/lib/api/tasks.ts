import { ApiClient } from '@/lib/api-client';

export type TaskStatus = 'todo' | 'in_progress' | 'done' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date?: string;
  start_date?: string;
  completed_at?: string;
  estimated_hours?: number;
  actual_hours?: number;
  position?: number;
  is_recurring?: boolean;
  assigned_to_id?: string;
  user_id: string;
  project_id?: string;
  parent_task_id?: string;
  created_at: string;
  updated_at: string;

  // Relationships
  assigned_to?: User;
  project?: {
    id: string;
    name: string;
    description?: string;
  };
  tags: Tag[];
  categories: Category[];
  dependencies: any[];
  dependents: any[];
  subtasks: any[];
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
}

export interface Tag {
  id: string;
  name: string;
  color?: string;
}

export interface Category {
  id: string;
  name: string;
  color?: string;
  description?: string;
}

export interface TasksResponse {
  tasks: Task[];
  total: number;
  skip: number;
  limit: number;
}

export interface TaskStatistics {
  total_tasks: number;
  tasks_by_status: {
    todo: number;
    in_progress: number;
    done: number;
  };
  tasks_by_priority: {
    low: number;
    medium: number;
    high: number;
    urgent: number;
  };
  completion_rate: number;
  overdue_tasks: number;
  average_completion_time?: number;
}

export interface CreateTaskRequest {
  title: string;
  description?: string;
  status?: 'todo' | 'in_progress' | 'done';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  due_date?: string;
  start_date?: string;
  estimated_hours?: number;
  assigned_to_id?: string;
  project_id?: string;
  parent_task_id?: string;
  tag_ids?: string[];
  category_ids?: string[];
}

export interface UpdateTaskRequest extends Partial<CreateTaskRequest> {
  position?: number;
}

export class TasksService {
  private static async fetchWithAuth(url: string, options: RequestInit = {}) {
    return ApiClient.fetchJSON(url, options);
  }

  static async getTasks(params?: {
    status?: string;
    priority?: string;
    assigned_to_id?: string;
    project_id?: string;
    category_ids?: string[];
    tag_ids?: string[];
    sort_by?: string;
    skip?: number;
    limit?: number;
  }): Promise<TasksResponse> {
    const queryParams = new URLSearchParams();

    if (params) {
      // Map frontend field names to backend field names
      const fieldMapping: Record<string, string> = {
        status: 'task_status',
        sort_by: 'sort_by',
      };

      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          const mappedKey = fieldMapping[key] || key;

          // Handle arrays for category_ids and tag_ids
          if ((key === 'category_ids' || key === 'tag_ids') && Array.isArray(value)) {
            value.forEach((id) => queryParams.append(mappedKey, id));
          } else {
            queryParams.append(mappedKey, value.toString());
          }
        }
      });
    }

    const url = ApiClient.buildUrl(
      `/tasks${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    );
    const data = await this.fetchWithAuth(url);

    // The backend returns an array directly for the list endpoint
    const tasks = Array.isArray(data) ? data : data.tasks || [];

    return {
      tasks: tasks,
      total: tasks.length,
      skip: params?.skip || 0,
      limit: params?.limit || 10,
    };
  }

  static async getTask(taskId: string): Promise<Task> {
    return this.fetchWithAuth(ApiClient.buildUrl(`/tasks/${taskId}`));
  }

  static async createTask(task: CreateTaskRequest): Promise<Task> {
    return this.fetchWithAuth(ApiClient.buildUrl('/tasks'), {
      method: 'POST',
      body: JSON.stringify(task),
    });
  }

  static async updateTask(taskId: string, updates: UpdateTaskRequest): Promise<Task> {
    return this.fetchWithAuth(ApiClient.buildUrl(`/tasks/${taskId}`), {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  static async deleteTask(taskId: string): Promise<void> {
    await ApiClient.fetchJSON(ApiClient.buildUrl(`/tasks/${taskId}`), {
      method: 'DELETE',
    });
  }

  static async getStatistics(params?: {
    start_date?: string;
    end_date?: string;
    project_id?: string;
  }): Promise<TaskStatistics> {
    const queryParams = new URLSearchParams();

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value);
        }
      });
    }

    const url = ApiClient.buildUrl(
      `/analytics/statistics${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    );
    return this.fetchWithAuth(url);
  }

  static async getRecentTasks(limit: number = 5): Promise<Task[]> {
    const response = await this.getTasks({
      limit,
      // Sort by updated_at desc would be ideal, but if not available, we'll get the latest
    });
    return response.tasks;
  }

  static async getUpcomingTasks(days: number = 7): Promise<Task[]> {
    const response = await this.getTasks({
      status: 'todo',
      limit: 20, // Get more to filter client-side
    });

    // Filter tasks with due dates in the next N days
    const now = new Date();
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + days);

    return response.tasks
      .filter((task) => {
        if (!task.due_date) return false;
        const dueDate = new Date(task.due_date);
        return dueDate >= now && dueDate <= futureDate;
      })
      .sort((a, b) => {
        const dateA = new Date(a.due_date!);
        const dateB = new Date(b.due_date!);
        return dateA.getTime() - dateB.getTime();
      });
  }

  static async bulkUpdateTasks(taskIds: string[], updates: UpdateTaskRequest): Promise<void> {
    return this.fetchWithAuth(ApiClient.buildUrl('/tasks/bulk/update'), {
      method: 'PUT',
      body: JSON.stringify({
        task_ids: taskIds,
        updates,
      }),
    });
  }

  static async bulkDeleteTasks(taskIds: string[]): Promise<void> {
    await ApiClient.fetchJSON(ApiClient.buildUrl('/tasks/bulk/delete'), {
      method: 'DELETE',
      body: JSON.stringify({
        task_ids: taskIds,
      }),
    });
  }
}
