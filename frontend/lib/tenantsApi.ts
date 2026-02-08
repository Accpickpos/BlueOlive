/**
 * Tenants/Shops API Client
 * 
 * Handles multi-tenancy configuration:
 * - Tenant management
 * - Shop management
 * - Current tenant tracking
 * 
 * Base URL: /api/v1/tenants/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';

export interface Tenant {
  id: number;
  name: string;
  code: string;
  status: 'ACTIVE' | 'INACTIVE' | 'SUSPENDED';
  created_at: string;
  [key: string]: any;
}

export interface Shop {
  id: number;
  name: string;
  code: string;
  tenant_id?: number;
  address?: string;
  phone?: string;
  email?: string;
  status: 'ACTIVE' | 'INACTIVE';
  created_at: string;
  [key: string]: any;
}

export interface TenantShop {
  id: number;
  tenant_id: number;
  shop_id: number;
  tenant?: Tenant;
  shop?: Shop;
  created_at: string;
  [key: string]: any;
}

export interface CurrentTenant {
  tenant_id: number;
  shop_id: number;
  tenant_name: string;
  shop_name: string;
  [key: string]: any;
}

export const tenantsApi = {
  // ============ TENANTS ============
  tenants: {
    /**
     * List all tenants
     */
    list: async (filters?: any) => {
      const response = await api.get<{ results: Tenant[] }>(
        ENDPOINTS.TENANTS.BASE,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single tenant
     */
    get: async (id: number | string) => {
      const response = await api.get<Tenant>(
        `${ENDPOINTS.TENANTS.BASE}${id}/`
      );
      return response.data;
    },

    /**
     * Create new tenant
     */
    create: async (data: Partial<Tenant>) => {
      const response = await api.post<Tenant>(
        ENDPOINTS.TENANTS.BASE,
        data
      );
      return response.data;
    },

    /**
     * Update tenant
     */
    update: async (id: number | string, data: Partial<Tenant>) => {
      const response = await api.patch<Tenant>(
        `${ENDPOINTS.TENANTS.BASE}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete tenant
     */
    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.TENANTS.BASE}${id}/`);
    },
  },

  // ============ SHOPS ============
  shops: {
    /**
     * List all shops
     */
    list: async (filters?: any) => {
      const response = await api.get<{ results: Shop[] }>(
        ENDPOINTS.TENANTS.SHOPS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single shop
     */
    get: async (id: number | string) => {
      const response = await api.get<Shop>(
        `${ENDPOINTS.TENANTS.SHOPS}${id}/`
      );
      return response.data;
    },

    /**
     * Create new shop
     */
    create: async (data: Partial<Shop>) => {
      const response = await api.post<Shop>(
        ENDPOINTS.TENANTS.SHOPS,
        data
      );
      return response.data;
    },

    /**
     * Update shop
     */
    update: async (id: number | string, data: Partial<Shop>) => {
      const response = await api.patch<Shop>(
        `${ENDPOINTS.TENANTS.SHOPS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete shop
     */
    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.TENANTS.SHOPS}${id}/`);
    },
  },

  // ============ CURRENT TENANT ============
  currentTenant: {
    /**
     * Get current tenant and shop context
     */
    get: async (): Promise<CurrentTenant> => {
      const response = await api.get<CurrentTenant>(
        ENDPOINTS.TENANTS.CURRENT_TENANT
      );
      return response.data;
    },

    /**
     * Set current tenant context
     */
    set: async (data: { tenant_id: number; shop_id?: number }): Promise<CurrentTenant> => {
      const response = await api.post<CurrentTenant>(
        ENDPOINTS.TENANTS.CURRENT_TENANT,
        data
      );
      return response.data;
    },
  },

  // ============ TENANT SHOPS (Many-to-Many) ============
  tenantShops: {
    /**
     * List all tenant-shop relationships
     */
    list: async (filters?: any) => {
      const response = await api.get<{ results: TenantShop[] }>(
        ENDPOINTS.TENANTS.TENANT_SHOPS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single tenant-shop relationship
     */
    get: async (id: number | string) => {
      const response = await api.get<TenantShop>(
        `${ENDPOINTS.TENANTS.TENANT_SHOPS}${id}/`
      );
      return response.data;
    },

    /**
     * Create tenant-shop relationship
     */
    create: async (data: Partial<TenantShop>) => {
      const response = await api.post<TenantShop>(
        ENDPOINTS.TENANTS.TENANT_SHOPS,
        data
      );
      return response.data;
    },

    /**
     * Update tenant-shop relationship
     */
    update: async (id: number | string, data: Partial<TenantShop>) => {
      const response = await api.patch<TenantShop>(
        `${ENDPOINTS.TENANTS.TENANT_SHOPS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete tenant-shop relationship
     */
    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.TENANTS.TENANT_SHOPS}${id}/`);
    },
  },

  // ============ ALL SHOPS (Simplified view) ============
  allShops: {
    /**
     * Get list of all shops available in the system
     */
    list: async (filters?: any) => {
      const response = await api.get<{ results: Shop[] }>(
        ENDPOINTS.TENANTS.ALL_SHOPS,
        { params: filters }
      );
      return response.data;
    },
  },
};

export default tenantsApi;
