/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen } from '@testing-library/react';

// Mock Next.js router
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock auth context
jest.mock('@/contexts/auth-context', () => ({
  useAuth: jest.fn(),
}));

import { ProtectedRoute } from '@/components/auth/protected-route';
import { useAuth } from '@/contexts/auth-context';

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const TestChildren = () => <div data-testid="protected-content">Protected Content</div>;

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should show loading state when auth is loading', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      user: null,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <ProtectedRoute>
        <TestChildren />
      </ProtectedRoute>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('should redirect to login when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <ProtectedRoute>
        <TestChildren />
      </ProtectedRoute>
    );

    expect(mockPush).toHaveBeenCalledWith('/login');
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('should render children when authenticated', () => {
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
    };

    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: mockUser,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <ProtectedRoute>
        <TestChildren />
      </ProtectedRoute>
    );

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('should not redirect during loading state', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      user: null,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <ProtectedRoute>
        <TestChildren />
      </ProtectedRoute>
    );

    expect(mockPush).not.toHaveBeenCalled();
  });
});
