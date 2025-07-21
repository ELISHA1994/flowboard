import { AuthService } from '@/lib/auth';
import { Task } from './tasks';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface TaskSearchFilter {
  field: string;
  operator:
    | 'eq'
    | 'ne'
    | 'gt'
    | 'gte'
    | 'lt'
    | 'lte'
    | 'in'
    | 'contains'
    | 'starts_with'
    | 'ends_with';
  value: any;
}

export interface TaskSearchRequest {
  text?: string;
  filters?: TaskSearchFilter[];
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
  include_shared?: boolean;
  include_assigned?: boolean;
}

export interface TaskSearchResponse {
  tasks: Task[];
  total: number;
  offset: number;
  limit: number;
}

export interface SearchSuggestions {
  statuses: string[];
  priorities: string[];
  categories: Array<{ id: string; name: string }>;
  tags: Array<{ id: string; name: string }>;
  assigned_users: Array<{ id: string; username: string }>;
  projects: Array<{ id: string; name: string }>;
}

export class SearchService {
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

  static async searchTasks(params: TaskSearchRequest): Promise<TaskSearchResponse> {
    return this.fetchWithAuth(`${API_BASE_URL}/search/tasks`, {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  static async getSearchSuggestions(): Promise<SearchSuggestions> {
    return this.fetchWithAuth(`${API_BASE_URL}/search/suggestions`);
  }
}
