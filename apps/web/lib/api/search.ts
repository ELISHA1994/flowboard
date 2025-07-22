import { ApiClient } from '@/lib/api-client';
import { Task } from './tasks';

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
  static async searchTasks(params: TaskSearchRequest): Promise<TaskSearchResponse> {
    return ApiClient.fetchJSON(ApiClient.buildUrl('/search/tasks'), {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  static async getSearchSuggestions(): Promise<SearchSuggestions> {
    return ApiClient.fetchJSON(ApiClient.buildUrl('/search/suggestions'));
  }
}
