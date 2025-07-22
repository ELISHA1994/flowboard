export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface SessionInfo {
  id: string;
  device_name?: string | null;
  device_type?: string | null;
  browser?: string | null;
  ip_address?: string | null;
  last_active?: string | null;
  created_at: string;
  is_current?: boolean;
}

import { tokenStorage } from './token-storage';

// Use relative URLs to go through Next.js proxy
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

export class AuthService {
  private static refreshPromise: Promise<AuthToken | null> | null = null;

  static async login(credentials: LoginRequest): Promise<AuthToken> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      body: formData,
      credentials: 'include', // Include cookies
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const authData = await response.json();

    // Store access token in memory
    tokenStorage.setAccessToken(authData.access_token, authData.expires_in);

    // Test cookies after login silently
    try {
      await fetch(`${API_BASE_URL}/test-cookies`, {
        credentials: 'include',
      });
    } catch (e) {
      // Ignore cookie test errors
    }

    return authData;
  }

  static async register(userData: RegisterRequest): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    return response.json();
  }

  static async refreshToken(): Promise<AuthToken | null> {
    // If already refreshing, return the existing promise
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    // Create new refresh promise
    this.refreshPromise = this._doRefresh();

    try {
      const result = await this.refreshPromise;
      return result;
    } finally {
      // Clear the promise after it completes
      this.refreshPromise = null;
    }
  }

  private static async _doRefresh(): Promise<AuthToken | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/refresh`, {
        method: 'POST',
        credentials: 'include', // Include cookies
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // Don't log error for 401s - this is expected when refresh token is invalid/expired
        if (response.status !== 401) {
          console.error('Refresh token failed with status:', response.status);
        }
        tokenStorage.clearAccessToken();
        return null;
      }

      const authData = await response.json();

      // Store new access token in memory
      tokenStorage.setAccessToken(authData.access_token, authData.expires_in);

      return authData;
    } catch (error) {
      // Silently handle refresh errors - these are expected when not logged in
      tokenStorage.clearAccessToken();
      return null;
    }
  }

  static async getCurrentUser(): Promise<User | null> {
    let token = tokenStorage.getAccessToken();

    // Always try to refresh if no token (happens on page reload)
    if (!token) {
      const refreshed = await this.refreshToken();
      if (!refreshed) return null;
      token = tokenStorage.getAccessToken();
    }

    try {
      const response = await fetch(`${API_BASE_URL}/users/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Try to refresh token
          const refreshed = await this.refreshToken();
          if (!refreshed) return null;

          // Retry with new token
          const retryResponse = await fetch(`${API_BASE_URL}/users/me`, {
            headers: {
              Authorization: `Bearer ${tokenStorage.getAccessToken()}`,
            },
            credentials: 'include',
          });

          if (!retryResponse.ok) return null;
          return retryResponse.json();
        }
        return null;
      }

      return response.json();
    } catch (error) {
      // Silently handle errors - user is simply not authenticated
      return null;
    }
  }

  static getToken(): string | null {
    return tokenStorage.getAccessToken();
  }

  static isAuthenticated(): boolean {
    return !!tokenStorage.getAccessToken();
  }

  static async logout(): Promise<void> {
    try {
      await fetch(`${API_BASE_URL}/logout`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${tokenStorage.getAccessToken()}`,
        },
        credentials: 'include',
      });
    } catch (error) {
      // Logout anyway even if request fails
    } finally {
      tokenStorage.clearAccessToken();
    }
  }

  static async logoutAll(): Promise<void> {
    try {
      await fetch(`${API_BASE_URL}/logout-all`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${tokenStorage.getAccessToken()}`,
        },
        credentials: 'include',
      });
    } catch (error) {
      // Logout anyway even if request fails
    } finally {
      tokenStorage.clearAccessToken();
    }
  }

  static async getSessions(): Promise<SessionInfo[]> {
    const token = tokenStorage.getAccessToken();
    if (!token) return [];

    try {
      const response = await fetch(`${API_BASE_URL}/sessions`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        credentials: 'include',
      });

      if (!response.ok) return [];
      return response.json();
    } catch (error) {
      return [];
    }
  }

  static async revokeSession(sessionId: string): Promise<boolean> {
    const token = tokenStorage.getAccessToken();
    if (!token) return false;

    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        credentials: 'include',
      });

      return response.ok;
    } catch (error) {
      return false;
    }
  }
}
