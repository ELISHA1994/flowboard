import { ApiClient } from '@/lib/api-client';

export interface Tag {
  id: string;
  name: string;
  color: string;
  user_id: string;
  task_count?: number;
  created_at: string;
}

export interface CreateTagRequest {
  name: string;
  color?: string;
}

export interface UpdateTagRequest {
  name?: string;
  color?: string;
}

export interface TagWithTasks extends Tag {
  tasks: any[]; // You can define Task interface if needed
}

export interface BulkTagCreate {
  tag_names: string[];
}

export interface PopularTag extends Tag {
  usage_count: number;
}

export class TagsService {
  private static async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    return ApiClient.fetchJSON(ApiClient.buildUrl(endpoint), options);
  }

  // Get all tags
  static async getTags(): Promise<Tag[]> {
    return this.makeRequest<Tag[]>('/tags');
  }

  // Get popular tags
  static async getPopularTags(limit: number = 10): Promise<PopularTag[]> {
    return this.makeRequest<PopularTag[]>(`/tags/popular?limit=${limit}`);
  }

  // Get single tag
  static async getTag(tagId: string, includeTasks: boolean = false): Promise<Tag | TagWithTasks> {
    const params = includeTasks ? '?include_tasks=true' : '';
    return this.makeRequest<Tag | TagWithTasks>(`/tags/${tagId}${params}`);
  }

  // Create tag
  static async createTag(data: CreateTagRequest): Promise<Tag> {
    return this.makeRequest<Tag>('/tags', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Create multiple tags
  static async createBulkTags(data: BulkTagCreate): Promise<Tag[]> {
    return this.makeRequest<Tag[]>('/tags/bulk', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Update tag
  static async updateTag(tagId: string, data: UpdateTagRequest): Promise<Tag> {
    return this.makeRequest<Tag>(`/tags/${tagId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Delete tag
  static async deleteTag(tagId: string): Promise<void> {
    await this.makeRequest<void>(`/tags/${tagId}`, {
      method: 'DELETE',
    });
  }

  // Format tag name (lowercase, replace spaces with hyphens)
  static formatTagName(name: string): string {
    return name.toLowerCase().replace(/\s+/g, '-');
  }

  // Validate tag name
  static validateTagName(name: string): boolean {
    const regex = /^[a-z0-9\-_]+$/;
    return regex.test(name.toLowerCase());
  }

  // Get tag color or default
  static formatTagColor(color?: string): string {
    return color || '#808080'; // Default gray color
  }
}
