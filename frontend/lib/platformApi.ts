import axios, { AxiosInstance } from 'axios';
import { ENDPOINTS } from './api-config';
import { fetchCSRFToken } from './api';

/**
 * Platform-owner API client.
 *
 * Deliberately its own axios instance, separate from `lib/api.ts`'s `api`
 * export. The owner session lives in its own cookies (po_access_token /
 * po_refresh_token, set by the backend's saas-admin/auth/ views) and must
 * never be mixed with a tenant session's 401/refresh handling - reusing the
 * shared `api` instance would retry a platform-owner 401 against the
 * *tenant* token refresh endpoint, which has no idea about this session.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE
  || (process.env.NODE_ENV === 'production' ? 'http://blueolive-backend:8000' : 'http://localhost:8000');

export const platformApi: AxiosInstance = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  timeout: 60000,
});

let isRefreshing = false;
let failedQueue: Array<{ resolve: () => void; reject: (err: unknown) => void }> = [];

function processQueue(error: unknown) {
  failedQueue.forEach(({ resolve, reject }) => (error ? reject(error) : resolve()));
  failedQueue = [];
}

platformApi.interceptors.request.use(async (config) => {
  if (config.method && ['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())) {
    const token = await fetchCSRFToken();
    if (token) {
      config.headers['X-CSRFToken'] = token;
    }
  }
  return config;
});

platformApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const isProfileCheck = (originalRequest?.url || '').includes(ENDPOINTS.SAAS_ADMIN.AUTH_PROFILE);

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !isProfileCheck) {
      originalRequest._retry = true;

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve: () => resolve(platformApi(originalRequest)), reject });
        });
      }

      isRefreshing = true;
      try {
        await platformApi.post(ENDPOINTS.SAAS_ADMIN.AUTH_TOKEN_REFRESH);
        isRefreshing = false;
        processQueue(null);
        return platformApi(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        processQueue(refreshError);
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export interface PlatformOwner {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_superuser: true;
}

export interface Tenant {
  id: number;
  name: string;
  phone: string;
  email: string;
  slug: string;
  subdomain: string;
  company_name: string;
  company_address: string;
  vat_number: string;
  registration_number: string;
  currency_symbol: string;
  currency_code: string;
  setup_status: 'pending' | 'db_ready' | 'ready' | 'failed';
  is_active: boolean;
  enabled_addons: string[];
  created_at: string;
  shops?: { id: number; name: string; subdomain: string; is_head_office: boolean }[];
  user_count?: number;
}

export interface TenantStats {
  total_tenants: number;
  active_tenants: number;
  inactive_tenants: number;
  total_shops: number;
  active_shops: number;
}

export async function platformLogin(username: string, password: string) {
  const response = await platformApi.post(ENDPOINTS.SAAS_ADMIN.AUTH_LOGIN, { username, password });
  return response.data.user as PlatformOwner;
}

export async function platformLogout() {
  await platformApi.post(ENDPOINTS.SAAS_ADMIN.AUTH_LOGOUT);
}

export async function fetchPlatformProfile() {
  const response = await platformApi.get(ENDPOINTS.SAAS_ADMIN.AUTH_PROFILE);
  return response.data as PlatformOwner;
}

export async function fetchTenantStats() {
  const response = await platformApi.get(ENDPOINTS.SAAS_ADMIN.TENANT_STATS);
  return response.data as TenantStats;
}

export async function fetchTenants() {
  const response = await platformApi.get(ENDPOINTS.SAAS_ADMIN.TENANTS);
  const data = response.data;
  return (Array.isArray(data) ? data : data.results) as Tenant[];
}

export interface CreateTenantPayload {
  name: string;
  email: string;
  phone: string;
  password: string;
  company_name?: string;
}

export async function createTenant(payload: CreateTenantPayload) {
  const response = await platformApi.post(ENDPOINTS.SAAS_ADMIN.TENANTS, payload);
  return response.data as Tenant;
}

export async function fetchTenant(id: number) {
  const response = await platformApi.get(ENDPOINTS.SAAS_ADMIN.TENANT_DETAIL(id));
  return response.data as Tenant;
}

export async function updateTenantAddons(id: number, enabledAddons: string[]) {
  const response = await platformApi.patch(ENDPOINTS.SAAS_ADMIN.TENANT_DETAIL(id), {
    enabled_addons: enabledAddons,
  });
  return response.data as Tenant;
}

export async function activateTenant(id: number) {
  const response = await platformApi.post(ENDPOINTS.SAAS_ADMIN.TENANT_ACTIVATE(id));
  return response.data;
}

export async function deactivateTenant(id: number) {
  const response = await platformApi.post(ENDPOINTS.SAAS_ADMIN.TENANT_DEACTIVATE(id));
  return response.data;
}

// ===== Shops =====

export interface Shop {
  id: number;
  tenant: number;
  tenant_name: string;
  name: string;
  code: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  description: string | null;
  schema_name: string;
  subdomain: string;
  is_head_office: boolean;
  is_active: boolean;
  setup_status: 'pending' | 'ready' | 'failed';
  created_at: string;
}

export async function fetchShops(tenantId: number) {
  const response = await platformApi.get(ENDPOINTS.SAAS_ADMIN.SHOPS, {
    params: { tenant_id: tenantId },
  });
  const data = response.data;
  return (Array.isArray(data) ? data : data.results) as Shop[];
}

export interface CreateShopPayload {
  tenant_id: number;
  name: string;
  code?: string;
  address?: string;
  phone?: string;
  email?: string;
  description?: string;
  is_head_office?: boolean;
}

export async function createShop(payload: CreateShopPayload) {
  const response = await platformApi.post(ENDPOINTS.SAAS_ADMIN.SHOPS, payload);
  return response.data as Shop;
}

export async function activateShop(id: number) {
  const response = await platformApi.post(ENDPOINTS.SAAS_ADMIN.SHOP_ACTIVATE(id));
  return response.data;
}

export async function deactivateShop(id: number) {
  const response = await platformApi.post(ENDPOINTS.SAAS_ADMIN.SHOP_DEACTIVATE(id));
  return response.data;
}

// ===== Cross-tenant users =====

export interface TenantUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

export async function fetchTenantUsers(tenantId: number) {
  const response = await platformApi.get(ENDPOINTS.SAAS_ADMIN.USERS_LIST, {
    params: { tenant_id: tenantId },
  });
  return response.data.users as TenantUser[];
}

export interface CreateTenantAdminPayload {
  tenant_id: number;
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export async function createTenantAdmin(payload: CreateTenantAdminPayload) {
  const response = await platformApi.post(ENDPOINTS.SAAS_ADMIN.USERS_CREATE_ADMIN, payload);
  return response.data;
}

export async function toggleTenantUserStatus(userId: number) {
  const response = await platformApi.post(ENDPOINTS.SAAS_ADMIN.USERS_TOGGLE_STATUS, {
    user_id: userId,
  });
  return response.data;
}

export async function resetTenantUserPassword(userId: number, newPassword: string) {
  const response = await platformApi.post(ENDPOINTS.SAAS_ADMIN.USERS_RESET_PASSWORD, {
    user_id: userId,
    new_password: newPassword,
  });
  return response.data;
}

// ===== Platform superuser accounts (owner accounts, not tenant users) =====

export interface Superuser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_superuser: true;
  date_joined: string;
}

export async function fetchSuperusers() {
  const response = await platformApi.get(ENDPOINTS.USERS.SUPERUSERS);
  const data = response.data;
  return (Array.isArray(data) ? data : data.results) as Superuser[];
}

export interface CreateSuperuserPayload {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export async function createSuperuser(payload: CreateSuperuserPayload) {
  const response = await platformApi.post(ENDPOINTS.USERS.SUPERUSERS, {
    ...payload,
    is_superuser: true,
  });
  return response.data as Superuser;
}

export async function toggleSuperuserActive(id: number) {
  const response = await platformApi.post(ENDPOINTS.USERS.SUPERUSER_TOGGLE_ACTIVE(id));
  return response.data;
}

export async function setSuperuserPassword(id: number, password: string) {
  const response = await platformApi.post(ENDPOINTS.USERS.SUPERUSER_SET_PASSWORD(id), {
    password,
  });
  return response.data;
}
