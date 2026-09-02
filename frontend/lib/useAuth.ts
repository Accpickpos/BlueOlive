'use client';
import { useEffect, useState, useCallback } from 'react';
import { apiRequest } from './api';

export interface Tenant {
  id: number;
  slug: string;
  name: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  is_superuser: boolean;
  is_admin: boolean;
  tenant_id: number | null;
  tenant?: Tenant;
  shop_ids?: number[];
  current_shop_id?: number | null;
}

interface UseAuthReturn {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isAccountant: boolean;
  refetch: () => Promise<void>;
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await apiRequest('/api/v1/users/auth/profile/');
      setUser(response.data);
    } catch (error: any) {
      // 401 is expected when user hasn't logged in - don't log as error
      if (error?.response?.status === 401) {
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
    fetchUser();
  }, [fetchUser]);

  return {
    user,
    isLoading,
    isAuthenticated: user !== null,
    isAdmin: user?.is_admin || false,
    isAccountant: user?.role === 'ACCOUNTANT',
    refetch: fetchUser,
  };
}
