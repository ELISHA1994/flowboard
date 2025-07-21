/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock the AuthService before importing the context
jest.mock('@/lib/auth', () => ({
  AuthService: {
    login: jest.fn(),
    register: jest.fn(),
    getCurrentUser: jest.fn(),
    isAuthenticated: jest.fn(),
    logout: jest.fn(),
    setToken: jest.fn(),
    getToken: jest.fn(),
    clearToken: jest.fn(),
  },
}));

import { AuthProvider, useAuth } from '@/contexts/auth-context';
import { AuthService } from '@/lib/auth';

const mockAuthService = AuthService as jest.Mocked<typeof AuthService>;

// Test component to access the auth context
const TestComponent = () => {
  const { user, isLoading, login, register, logout, isAuthenticated } = useAuth();

  return (
    <div>
      <div data-testid="loading">{isLoading ? 'loading' : 'not-loading'}</div>
      <div data-testid="authenticated">
        {isAuthenticated ? 'authenticated' : 'not-authenticated'}
      </div>
      <div data-testid="user">{user ? user.username : 'no-user'}</div>
      <button data-testid="login-btn" onClick={() => login({ username: 'test', password: 'test' })}>
        Login
      </button>
      <button
        data-testid="register-btn"
        onClick={() => register({ username: 'test', email: 'test@example.com', password: 'test' })}
      >
        Register
      </button>
      <button data-testid="logout-btn" onClick={logout}>
        Logout
      </button>
    </div>
  );
};

const renderWithAuthProvider = (children: React.ReactNode) => {
  return render(<AuthProvider>{children}</AuthProvider>);
};

describe('AuthProvider', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should initialize with loading state', () => {
    mockAuthService.isAuthenticated.mockReturnValue(false);
    mockAuthService.getCurrentUser.mockResolvedValue(null);

    renderWithAuthProvider(<TestComponent />);

    expect(screen.getByTestId('loading')).toHaveTextContent('loading');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
    expect(screen.getByTestId('user')).toHaveTextContent('no-user');
  });

  it('should load authenticated user on mount', async () => {
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
    };

    mockAuthService.isAuthenticated.mockReturnValue(true);
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

    renderWithAuthProvider(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
    expect(screen.getByTestId('user')).toHaveTextContent('testuser');
  });

  it('should handle login successfully', async () => {
    const user = userEvent.setup();
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
    };
    const mockToken = { access_token: 'token', token_type: 'bearer' };

    mockAuthService.isAuthenticated.mockReturnValue(false);
    mockAuthService.getCurrentUser
      .mockResolvedValueOnce(null) // Initial load
      .mockResolvedValueOnce(mockUser); // After login
    mockAuthService.login.mockResolvedValue(mockToken);

    renderWithAuthProvider(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    await act(async () => {
      await user.click(screen.getByTestId('login-btn'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
    });

    expect(mockAuthService.login).toHaveBeenCalledWith({ username: 'test', password: 'test' });
    expect(screen.getByTestId('user')).toHaveTextContent('testuser');
  });

  it('should handle logout', async () => {
    const user = userEvent.setup();
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
    };

    mockAuthService.isAuthenticated.mockReturnValue(true);
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

    renderWithAuthProvider(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
    });

    await act(async () => {
      await user.click(screen.getByTestId('logout-btn'));
    });

    expect(mockAuthService.logout).toHaveBeenCalled();
    expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
    expect(screen.getByTestId('user')).toHaveTextContent('no-user');
  });

  it('should throw error when useAuth is used outside AuthProvider', () => {
    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useAuth must be used within an AuthProvider');

    consoleSpy.mockRestore();
  });
});
