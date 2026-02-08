'use client';

import { useCallback, useState } from 'react';

export interface Tenant {
  id: number;
  name: string;
  email: string;
  slug: string;
  subdomain: string;
  phone: string;
  created_at: string;
  shops?: Shop[];
  user_count?: number;
}

export interface Shop {
  id: number;
  name: string;
  subdomain: string;
  is_head_office: boolean;
}

export interface CreateTenantPayload {
  name: string;
  email: string;
  phone: string;
  password: string;
  subdomain?: string;
}

export interface ApiError {
  message: string;
  status: number;
  details?: Record<string, unknown>;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export function useTenantApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const createTenant = useCallback(
    async (payload: CreateTenantPayload): Promise<Tenant | null> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/tenants/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || `Failed to create tenant: ${response.status}`);
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

  const getTenant = useCallback(
    async (id: number, token: string): Promise<Tenant | null> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/tenants/${id}/`, {
          method: 'GET',
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch tenant: ${response.status}`);
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

  const listTenants = useCallback(
    async (token: string): Promise<Tenant[] | null> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/tenants/`, {
          method: 'GET',
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch tenants: ${response.status}`);
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

  const updateTenant = useCallback(
    async (id: number, payload: Partial<CreateTenantPayload>, token: string): Promise<Tenant | null> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/tenants/${id}/`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          throw new Error(`Failed to update tenant: ${response.status}`);
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

  const deleteTenant = useCallback(
    async (id: number, token: string): Promise<boolean> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/tenants/${id}/`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok && response.status !== 204) {
          throw new Error(`Failed to delete tenant: ${response.status}`);
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

  return {
    createTenant,
    getTenant,
    listTenants,
    updateTenant,
    deleteTenant,
    loading,
    error,
  };
}
