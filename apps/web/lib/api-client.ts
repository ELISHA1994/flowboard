import { AuthService } from '@/lib/auth';

// Use relative URLs to go through Next.js proxy
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

export interface ApiError extends Error {
  status?: number;
  detail?: string;
}

/**
 * Global API client with authentication and error handling
 */
export class ApiClient {
  private static isRefreshing = false;
  private static refreshPromise: Promise<boolean> | null = null;

  /**
   * Perform an authenticated fetch request with automatic error handling and token refresh
   */
  static async fetchWithAuth(
    url: string,
    options: RequestInit = {},
    isRetry = false
  ): Promise<Response> {
    let token = AuthService.getToken();

    // If no token, try to refresh
    if (!token && !isRetry) {
      const refreshed = await this.refreshTokenIfNeeded();
      if (!refreshed) {
        // Don't redirect here - let the auth context handle redirects
        const error: ApiError = new Error('No authentication token found');
        error.status = 401;
        throw error;
      }
      token = AuthService.getToken();
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
      credentials: 'include', // Always include cookies
    });

    // Handle 401 Unauthorized errors
    if (response.status === 401 && !isRetry) {
      // Try to refresh token
      const refreshed = await this.refreshTokenIfNeeded();

      if (refreshed) {
        // Retry the request with new token
        return this.fetchWithAuth(url, options, true);
      } else {
        // Refresh failed - let auth context handle the redirect
        const error: ApiError = new Error('Authentication expired. Please login again.');
        error.status = 401;
        throw error;
      }
    }

    return response;
  }

  /**
   * Refresh token if needed (with deduplication)
   */
  private static async refreshTokenIfNeeded(): Promise<boolean> {
    // If already refreshing, wait for the existing promise
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = AuthService.refreshToken()
      .then((result) => !!result)
      .finally(() => {
        this.isRefreshing = false;
        this.refreshPromise = null;
      });

    return this.refreshPromise;
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
