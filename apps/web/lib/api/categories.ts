import { ApiClient } from '@/lib/api-client';

export interface Category {
  id: string;
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  user_id: string;
  is_active: boolean;
  task_count?: number;
  created_at: string;
  updated_at?: string;
}

export interface CreateCategoryRequest {
  name: string;
  description?: string;
  color?: string;
  icon?: string;
}

export interface UpdateCategoryRequest {
  name?: string;
  description?: string;
  color?: string;
  icon?: string;
  is_active?: boolean;
}

export interface CategoryWithTasks extends Category {
  tasks: any[]; // You can define Task interface if needed
}

export class CategoriesService {
  private static API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  private static async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    return ApiClient.fetchJSON(`${this.API_URL}${endpoint}`, options);
  }

  // Get all categories
  static async getCategories(includeInactive: boolean = false): Promise<Category[]> {
    const params = includeInactive ? '?include_inactive=true' : '';
    return this.makeRequest<Category[]>(`/categories${params}`);
  }

  // Get single category
  static async getCategory(
    categoryId: string,
    includeTasks: boolean = false
  ): Promise<Category | CategoryWithTasks> {
    const params = includeTasks ? '?include_tasks=true' : '';
    return this.makeRequest<Category | CategoryWithTasks>(`/categories/${categoryId}${params}`);
  }

  // Create category
  static async createCategory(data: CreateCategoryRequest): Promise<Category> {
    return this.makeRequest<Category>('/categories', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Update category
  static async updateCategory(categoryId: string, data: UpdateCategoryRequest): Promise<Category> {
    return this.makeRequest<Category>(`/categories/${categoryId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Delete category (soft delete)
  static async deleteCategory(categoryId: string): Promise<void> {
    await this.makeRequest<void>(`/categories/${categoryId}`, {
      method: 'DELETE',
    });
  }

  // Get category color or default
  static formatCategoryColor(color?: string): string {
    return color || '#6b7280'; // Default gray color
  }

  // Get category icon or default
  static formatCategoryIcon(icon?: string): string {
    return icon || '📁'; // Default folder icon
  }
}
