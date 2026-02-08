'use client';

import { useCallback, useState } from 'react';

export type UserRole = 'ADMIN' | 'MANAGER' | 'USER';

export interface ShopUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: UserRole;
  tenant_id: number;
  tenant_name?: string;
  shop_ids: number[];
  shops?: Shop[];
  is_active: boolean;
  is_staff: boolean;
  date_joined: string;
}

export interface Shop {
  id: number;
  name: string;
  subdomain: string;
}

export interface CreateUserPayload {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  password: string;
  role: UserRole;
  shop_ids?: number[];
}

export interface UpdateUserPayload {
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  password?: string;
  role?: UserRole;
  shop_ids?: number[];
  is_active?: boolean;
}

export interface ApiError {
  message: string;
  status: number;
  details?: Record<string, unknown>;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export function useShopUserApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const createUser = useCallback(
    async (payload: CreateUserPayload, token: string): Promise<ShopUser | null> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/users/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || `Failed to create user: ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError({ message, status: 500 });
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const listUsers = useCallback(
    async (token: string): Promise<ShopUser[] | null> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/users/`, {
          method: 'GET',
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch users: ${response.status}`);
        }

        const data = await response.json();
        // Handle both paginated and non-paginated responses
        return Array.isArray(data) ? data : data.results || [];
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError({ message, status: 500 });
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const getUser = useCallback(
    async (id: number, token: string): Promise<ShopUser | null> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/users/${id}/`, {
          method: 'GET',
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch user: ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError({ message, status: 500 });
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const updateUser = useCallback(
    async (id: number, payload: UpdateUserPayload, token: string): Promise<ShopUser | null> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/users/${id}/`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || `Failed to update user: ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError({ message, status: 500 });
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const deleteUser = useCallback(
    async (id: number, token: string): Promise<boolean> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/users/${id}/`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok && response.status !== 204) {
          throw new Error(`Failed to delete user: ${response.status}`);
        }

        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError({ message, status: 500 });
        return false;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const getCurrentProfile = useCallback(
    async (token: string): Promise<ShopUser | null> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/profile/`, {
          method: 'GET',
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch profile: ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError({ message, status: 500 });
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    createUser,
    listUsers,
    getUser,
    updateUser,
    deleteUser,
    getCurrentProfile,
    loading,
    error,
  };
}
