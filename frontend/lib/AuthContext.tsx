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
  const [hasAttemptedInitialFetch, setHasAttemptedInitialFetch] = useState(false);

  const refetch = useCallback(async (isInitialLoad: boolean = false) => {
    try {
      setIsLoading(true);
      // Cookies are sent automatically with withCredentials: true
      // No need to check localStorage
      const response = await apiRequest('/api/v1/users/auth/profile/', {
        skipRateLimitRetry: isInitialLoad, // Don't retry on initial load, just accept the failure
      });
      setUser(response.data);
    } catch (error: any) {
      // 401 is expected when user hasn't logged in - don't log as error
      if (error?.response?.status === 401) {
        setUser(null);
      } else if (error?.response?.status === 429) {
        // Rate limited
        if (isInitialLoad) {
          // On initial load, just accept it as "not logged in" to avoid blocking login
          console.debug('Profile endpoint rate limited on initial load - skipping retry');
        } else {
          // On explicit refetch (e.g., after login), log the issue
          console.warn('Rate limited on auth profile fetch - likely due to stale tokens');
        }
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
    // Only fetch user once on initial mount
    if (!hasAttemptedInitialFetch) {
      setHasAttemptedInitialFetch(true);
      // Mark as initial load so we don't retry on 429
      refetch(true);
    }
  }, [hasAttemptedInitialFetch, refetch]);

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
