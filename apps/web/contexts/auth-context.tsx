'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { AuthService, User, LoginRequest, RegisterRequest } from '@/lib/auth';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check if user is already authenticated on mount
  useEffect(() => {
    const initializeAuth = async () => {
      if (AuthService.isAuthenticated()) {
        try {
          const currentUser = await AuthService.getCurrentUser();
          setUser(currentUser);
        } catch (error) {
          // Token might be invalid, clear it
          AuthService.clearToken();
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  // Periodically validate token (every 5 minutes)
  useEffect(() => {
    if (!user) return;

    const validateToken = async () => {
      try {
        const currentUser = await AuthService.getCurrentUser();
        if (!currentUser) {
          // Token is invalid
          AuthService.clearToken();
          setUser(null);
          window.location.href = '/login';
        }
      } catch (error) {
        // Token validation failed
        AuthService.clearToken();
        setUser(null);
        window.location.href = '/login';
      }
    };

    // Validate immediately when user changes
    validateToken();

    // Then validate every 5 minutes
    const interval = setInterval(validateToken, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [user?.id]); // Only re-run if user ID changes

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      await AuthService.login(credentials);
      const currentUser = await AuthService.getCurrentUser();
      setUser(currentUser);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterRequest) => {
    setIsLoading(true);
    try {
      const newUser = await AuthService.register(userData);
      // After successful registration, log the user in
      await login({ username: userData.username, password: userData.password });
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    AuthService.logout();
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    isLoading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
