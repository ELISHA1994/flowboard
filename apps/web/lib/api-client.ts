import { AuthService } from '@/lib/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ApiError extends Error {
  status?: number;
  detail?: string;
}

/**
 * Global API client with authentication and error handling
 */
export class ApiClient {
  /**
   * Perform an authenticated fetch request with automatic error handling
   */
  static async fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
    const token = AuthService.getToken();

    if (!token) {
      // Redirect to login if no token
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      throw new Error('No authentication token found');
    }

    const headers = {
      ...options.headers,
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    };

    // Remove Content-Type for FormData
    if (options.body instanceof FormData) {
      delete headers['Content-Type'];
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle 401 Unauthorized errors
    if (response.status === 401) {
      // Clear invalid token
      AuthService.clearToken();

      // Redirect to login
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }

      const error: ApiError = new Error('Authentication expired. Please login again.');
      error.status = 401;
      throw error;
    }

    return response;
  }

  /**
   * Perform an authenticated JSON request
   */
  static async fetchJSON<T>(url: string, options: RequestInit = {}): Promise<T> {
    const response = await this.fetchWithAuth(url, options);

    if (!response.ok) {
      const error: ApiError = new Error(`Request failed with status ${response.status}`);
      error.status = response.status;

      try {
        const errorData = await response.json();
        error.detail = errorData.detail || error.message;
      } catch {
        // Ignore JSON parse errors
      }

      throw error;
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  /**
   * Build full API URL
   */
  static buildUrl(path: string): string {
    return `${API_BASE_URL}${path}`;
  }
}
