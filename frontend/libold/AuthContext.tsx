'use client';
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { apiRequest } from './api';

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  is_superuser: boolean;
  is_admin: boolean;
  tenant_id: number | null;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  refetch: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refetch = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await apiRequest('/api/auth/profile/');
      setUser(response.data);
      console.log('Auth profile refetched successfully:', response.data);
    } catch (error: any) {
      // 401 is expected when user hasn't logged in - don't log as error
      if (error?.response?.status === 401) {
        console.log('User not authenticated (401), clearing user data');
        setUser(null);
      } else if (error?.message === 'Network Error' || !error?.response) {
        // Network error - backend might not be running
        console.warn('Network error connecting to API. Backend may not be running at:', process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000');
        setUser(null);
      } else {
        console.error('Failed to fetch user profile:', error);
        setUser(null);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Only fetch user on initial mount
    refetch();
  }, [refetch]);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: user !== null,
    isAdmin: user?.is_admin || false,
    refetch,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to use authentication context
 * Must be used within AuthProvider
 */
export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within AuthProvider');
  }
  return context;
}
