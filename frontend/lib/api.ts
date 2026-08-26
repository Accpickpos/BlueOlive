import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { ENDPOINTS } from './api-config';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE
  || (process.env.NODE_ENV === 'production' ? 'http://blueolive-backend:8000' : 'http://localhost:8000');

/**
 * Security Note: Cookie-based JWT Authentication
 * Access tokens are stored in secure httpOnly cookies (set by backend on login)
 * No Authorization header needed - cookies are sent automatically with withCredentials: true
 * CSRF tokens are fetched from backend for mutating requests (POST, PUT, PATCH, DELETE)
 * 
 * To check if user is authenticated, make a request to /api/v1/users/auth/profile/ that returns 401 if not authenticated.
 */

export async function isAuthenticated(): Promise<boolean> {
  try {
    const response = await api.get(ENDPOINTS.AUTH.PROFILE);
    return response.status === 200;
  } catch {
    return false;
  }
}

// Track if we're currently logging out to suppress unnecessary token refresh attempts
let isLoggingOut = false;

export function clearAuthData(): void {
  // Reset all auth-related state on logout
  // Cookies are cleared by backend on logout endpoint
  csrfToken = null;
  
  // Clear shop context from localStorage
  if (typeof window !== 'undefined') {
    localStorage.removeItem('currentShopId');
    localStorage.removeItem('currentShop');
    localStorage.removeItem('shops');
    localStorage.removeItem('tenant');
  }
  
  // Note: do not set isLoggingOut here - only set it in logout() function
  // Setting it here blocks token refresh from retrying on subsequent 401 errors
}

// Store CSRF token globally
let csrfToken: string | null = null;

// Track rate limits per endpoint to avoid global blocking
const rateLimitedEndpoints = new Map<string, number>();

function isEndpointRateLimited(endpoint: string): boolean {
  const resetTime = rateLimitedEndpoints.get(endpoint);
  if (!resetTime) return false;
  
  if (Date.now() < resetTime) {
    return true;
  }
  
  // Reset time has passed, clear the entry
  rateLimitedEndpoints.delete(endpoint);
  return false;
}

function markEndpointRateLimited(endpoint: string, resetSeconds: number = 60): void {
  const resetTime = Date.now() + (resetSeconds * 1000);
  rateLimitedEndpoints.set(endpoint, resetTime);
}

// Helper to extract CSRF token from cookies
function getCsrfTokenFromCookie(): string | null {
  const name = 'csrftoken';
  let cookieValue = null;
  
  if (typeof document !== 'undefined' && document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  
  return cookieValue;
}

// Function to get CSRF token from backend
export async function fetchCSRFToken(): Promise<string> {
  if (csrfToken) {
    return csrfToken;
  }
  
  const csrfEndpoint = ENDPOINTS.AUTH.CSRF;
  
  // Check if this endpoint is rate-limited
  if (isEndpointRateLimited(csrfEndpoint)) {
    const resetTime = rateLimitedEndpoints.get(csrfEndpoint) || Date.now();
    const waitTime = Math.ceil((resetTime - Date.now()) / 1000);
    console.warn(`CSRF endpoint rate limited, will retry in ${waitTime}s`);
    // Return empty string - don't make the request
    return '';
  }
  
  try {
    // GET request to CSRF endpoint to get token in cookie
    const response = await axios.get(`${API_BASE}${csrfEndpoint}`, {
      withCredentials: true,
    });
    
    // CSRF token should be in cookie after this call
    const cookieToken = getCsrfTokenFromCookie();
    if (cookieToken) {
      csrfToken = cookieToken;
      return cookieToken;
    }
  } catch (error: any) {
    // Check for rate limiting
    if (error?.response?.status === 429) {
      markEndpointRateLimited(csrfEndpoint, 30); // Wait 30 seconds before retrying CSRF
      console.warn('CSRF endpoint rate limited (429) - stale tokens detected');
      return '';
    }
    
    // Try to get from cookies even on error
    const cookieToken = getCsrfTokenFromCookie();
    if (cookieToken) {
      csrfToken = cookieToken;
      return cookieToken;
    }
  }
  
  return '';
}

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  withCredentials: true, // Include cookies in cross-origin requests
  timeout: 180000, // 3 minute timeout for tenant creation migrations
});

// Track if we're currently refreshing token to avoid infinite loops
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  isRefreshing = false;
  failedQueue = [];
};

// Endpoints that don't require JWT authentication (public endpoints)
const PUBLIC_ENDPOINTS = [
  '/api/v1/users/auth/login/',
  '/api/v1/users/auth/signup/',
  '/api/v1/users/auth/csrf/',
  '/api/v1/users/auth/token/refresh/',
];

function isPublicEndpoint(url: string | undefined): boolean {
  if (!url) return false;
  return PUBLIC_ENDPOINTS.some(endpoint => url.includes(endpoint));
}

// Add CSRF token for mutating requests and tenant header
api.interceptors.request.use(async (config) => {
  // Cookies are sent automatically with withCredentials: true
  // No need for Authorization header - httpOnly cookie handles authentication
  
  // Add tenant header if available
  const tenant = typeof window !== 'undefined' ? localStorage.getItem('tenant') : null;
  if (tenant) {
    config.headers['X-Tenant'] = tenant;
  }
  // Note: Removed hardcoded 'dev' fallback - let backend return 404 if no tenant
  
  // Add shop ID header if available
  const shopId = typeof window !== 'undefined' ? localStorage.getItem('currentShopId') : null;
  if (shopId) {
    config.headers['X-Shop-ID'] = shopId;
  }
  
  // Add CSRF token for mutating requests (POST, PUT, PATCH, DELETE)
  if (config.method && ['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())) {
    let token = getCsrfTokenFromCookie();
    
    // If not found in cookie, fetch it
    if (!token) {
      token = await fetchCSRFToken();
    }
    
    if (token) {
      config.headers['X-CSRFToken'] = token;
    }
  }
  
  return config;
});

// Handle response errors and token refresh
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    const requestUrl = originalRequest?.url || '';
    const endpoint = requestUrl.replace(API_BASE, '').split('?')[0];
    
    // Handle 429 Too Many Requests
    if (error.response?.status === 429) {
      // If skipRateLimitRetry is set (e.g., on initial load), don't retry - just reject
      if (originalRequest?.skipRateLimitRetry) {
        console.debug(`Skipping retry on ${endpoint} due to initial load flag`);
        return Promise.reject(error);
      }
      
      // For auth endpoints, retry once after a short delay to handle rate limiting from stale sessions
      if (endpoint.includes('/auth/') && (!originalRequest._rateLimitRetry)) {
        originalRequest._rateLimitRetry = true;
        
        // Wait 2 seconds before retrying (allows backend to reset)
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        try {
          console.log(`Retrying rate-limited auth endpoint: ${endpoint}`);
          return api(originalRequest);
        } catch (retryError) {
          // If retry still fails with 429, mark endpoint as rate limited and give up
          markEndpointRateLimited(endpoint, 15);
          console.warn(`Auth endpoint ${endpoint} still rate limited after retry`);
          return Promise.reject(retryError);
        }
      }
      
      // Mark endpoint as rate limited for non-auth endpoints or if we already retried
      markEndpointRateLimited(endpoint, 15); // Wait 15 seconds before retrying
      
      console.warn(`Rate limited (429) on ${endpoint}`);
      return Promise.reject(error);
    }
    
    // These endpoints return 401 as valid state (checking auth status)
    // Don't attempt token refresh for these
    const statusCheckEndpoints = ['/api/v1/users/auth/profile/'];
    const isStatusCheck = statusCheckEndpoints.some(ep => requestUrl.includes(ep));
    
    // Handle 401 Unauthorized - attempt to refresh token via httpOnly cookies
    // Skip refresh if:
    // 1. We're in the middle of logout (expected 401)
    // 2. We're just checking authentication status (expected 401)
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !isLoggingOut && !isStatusCheck) {
      originalRequest._retry = true;
      
      if (isRefreshing) {
        // Queue the request while token is being refreshed
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => {
          // Retry with refreshed cookies
          return api(originalRequest);
        });
      }
      
      isRefreshing = true;
      
      try {
        // Call refresh endpoint to refresh httpOnly cookies
        await axios.post(`${API_BASE}/api/v1/users/auth/token/refresh/`, {}, {
          withCredentials: true,
        });
        
        processQueue(null);
        return api(originalRequest);
      } catch (err) {
        processQueue(err);
        clearAuthData();
        return Promise.reject(err);
      }
    }
    
    // Suppress error logging for expected auth status check 401s
    if (error.response?.status === 401 && isStatusCheck) {
      // Mark error to suppress console output
      error.silent = true;
    }
    
    return Promise.reject(error);
  }
);

/**
 * Normalizes an API error into a display string.
 *
 * Backend errors come in two shapes: manually-built views return
 * { error: "some string" }, while anything that flows through DRF's
 * exception dispatch (validation errors, permission denials, 404s, 500s)
 * is wrapped by core.exception_handler into { error: { code, message, ... } }.
 * Rendering the object directly crashes React ("Objects are not valid as a
 * React child"), so always unwrap through this instead of reading
 * err.response.data.error straight into JSX.
 */
export function getApiErrorMessage(err: any, fallback: string): string {
  const errorField = err?.response?.data?.error ?? err?.data?.error ?? err?.error;

  if (typeof errorField === 'string') {
    return errorField;
  }
  if (errorField && typeof errorField === 'object' && typeof errorField.message === 'string') {
    return errorField.message;
  }

  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') {
    return detail;
  }

  if (err instanceof Error && err.message) {
    return err.message;
  }

  return fallback;
}

export async function apiRequest(endpoint: string, options: any = {}): Promise<AxiosResponse> {
  const { method = 'GET', headers = {}, body, skipRateLimitRetry, ...rest } = options;
  
  return api({
    url: endpoint,
    method,
    data: body || undefined,
    skipRateLimitRetry, // Pass through to request config for interceptor
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    ...rest,
  });
}

export async function login(tenant_slug: string, username: string, password: string, shop_id?: number): Promise<AxiosResponse> {
  const response = await api.post('/api/v1/users/auth/login/', {
    username,
    password,
    tenant_slug,
    shop_id,  // Send selected shop_id to backend
  });

  // Backend returns user object, tokens are in httpOnly cookies set by the server
  // Reset CSRF token cache after successful login
  csrfToken = null;
  // Clear rate limiting for auth endpoints since we have fresh tokens
  rateLimitedEndpoints.delete('/api/v1/users/auth/csrf/');
  rateLimitedEndpoints.delete('/api/v1/users/auth/profile/');
  
  return response;
}

export async function signup(signupData: {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
  first_name: string;
  last_name: string;
  company_name: string;
  subdomain: string;
  subscription_plan_id?: number;
}): Promise<AxiosResponse> {
  // Signup no longer logs the user in inline - creating the tenant's
  // database + admin user happens in the background (Celery), since it
  // can take several seconds to tens of seconds. The response only
  // confirms the tenant row was created and returns its id/slug plus
  // setup_status: 'pending'. Callers must poll checkTenantSetupStatus()
  // until is_ready, then call login() with the same username/password.
  const response = await api.post('/api/v1/users/auth/signup/', signupData);
  return response;
}

export interface TenantSetupStatusResponse {
  id: number;
  name: string;
  setup_status: 'pending' | 'db_ready' | 'ready' | 'failed';
  is_ready: boolean;
  message: string;
}

// Poll this after signup() until is_ready is true (or setup_status is
// 'failed'). Unauthenticated on purpose - no admin user exists to log in
// with until provisioning finishes.
export async function checkTenantSetupStatus(tenantId: number): Promise<TenantSetupStatusResponse> {
  const response = await api.get(`/api/v1/tenants/${tenantId}/check_setup_status/`);
  return response.data;
}

// Subdomain validation for real-time availability checking
export interface SubdomainValidationResponse {
  subdomain: string;
  available: boolean;
  suggestions: string[];
}

export async function validateSubdomain(subdomain: string): Promise<SubdomainValidationResponse> {
  const response = await api.get('/api/v1/users/auth/signup/validate-subdomain/', {
    params: { subdomain },
  });
  return response.data;
}

export async function logout(): Promise<AxiosResponse> {
  try {
    // Mark logout in progress to suppress token refresh attempts
    isLoggingOut = true;
    const response = await api.post('/api/v1/users/auth/logout/');
    // Clear CSRF token cache and other auth data
    clearAuthData();
    return response;
  } catch (error) {
    // Still clear auth data even if logout endpoint fails
    clearAuthData();
    throw error;
  } finally {
    // Reset logout flag after a brief delay to allow pending 401 responses to complete
    setTimeout(() => {
      isLoggingOut = false;
    }, 100);
  }
}

export async function refreshToken(): Promise<AxiosResponse> {
  // With httpOnly cookies, token refresh is handled automatically by the interceptor
  // This function is kept for API compatibility but is rarely needed
  try {
    const response = await axios.post(`${API_BASE}/api/v1/users/auth/token/refresh/`, {}, {
      withCredentials: true,
    });
    return response;
  } catch (error) {
    clearAuthData();
    throw error;
  }
}

export async function getCurrentUser(): Promise<any> {
  const res = await apiRequest('/api/v1/users/auth/profile/');
  return res.data;
}

export async function getCurrentTenant(): Promise<any> {
  const res = await apiRequest('/api/v1/tenants/current/');
  return res.data;
}

export async function getUsers(): Promise<any[]> {
  const res = await apiRequest('/api/v1/users/');
  // Handle both array and paginated responses
  if (Array.isArray(res.data)) {
    return res.data;
  }
  return res.data.results || [];
}

export async function getShops(): Promise<any[]> {
  const res = await apiRequest('/api/v1/shops/');
  // Handle both array and paginated responses
  if (Array.isArray(res.data)) {
    return res.data;
  }
  return res.data.results || [];
}

export async function createUser(userData: any): Promise<any> {
  const res = await apiRequest('/api/v1/users/', {
    method: 'POST',
    data: userData,
  });
  return res.data;
}

export async function updateUser(id: number, userData: any): Promise<any> {
  const res = await apiRequest(`/api/v1/users/${id}/`, {
    method: 'PATCH',
    data: userData,
  });
  return res.data;
}

export async function deleteUser(id: number): Promise<void> {
  await apiRequest(`/api/v1/users/${id}/`, {
    method: 'DELETE',
  });
}

export async function createShop(shopData: any): Promise<any> {
  const res = await apiRequest('/api/v1/shops/', {
    method: 'POST',
    data: shopData,
  });
  return res.data;
}

export async function updateShop(id: number, shopData: any): Promise<any> {
  const res = await apiRequest(`/api/v1/shops/${id}/`, {
    method: 'PUT',
    data: shopData,
  });
  return res.data;
}

export async function deleteShop(id: number): Promise<void> {
  await apiRequest(`/api/v1/shops/${id}/`, {
    method: 'DELETE',
  });
}

export async function getTenants(): Promise<any[]> {
  const res = await apiRequest('/api/v1/tenants/');
  return res.data;
}

export async function getTenantShops(tenantSlug?: string): Promise<any[]> {
  const url = tenantSlug ? `/api/v1/tenants/tenant_shops/?tenant=${tenantSlug}` : '/api/v1/tenants/tenant_shops/';
  const res = await apiRequest(url);
  return res.data;
}

export async function createTenant(tenantData: any): Promise<AxiosResponse> {
  return apiRequest('/api/v1/tenants/', {
    method: 'POST',
    data: tenantData,
  });
}

// ========================================
// Subscription/SaaS Plans API
// ========================================

export async function getSubscriptionPlans(): Promise<any[]> {
  const res = await api.get('/api/v1/subscription/plans/');
  return res.data;
}

export async function getActiveSubscriptionPlans(): Promise<any> {
  const res = await api.get('/api/v1/subscription/plans/?is_active=true');
  // Handle both array and paginated response
  if (Array.isArray(res.data)) {
    return res.data;
  }
  return res.data.results || [];
}

// ========================================
// Supplier/Creditors API
// ========================================

export async function getSuppliers(): Promise<any[]> {
  const res = await apiRequest('/api/v1/creditors/creditors/');
  if (Array.isArray(res.data)) {
    return res.data;
  }
  return res.data.results || [];
}

export async function getSupplier(id: number): Promise<any> {
  const res = await apiRequest(`/api/v1/creditors/creditors/${id}/`);
  return res.data;
}

export async function createSupplier(supplierData: any): Promise<any> {
  const res = await apiRequest('/api/v1/creditors/creditors/', {
    method: 'POST',
    data: supplierData,
  });
  return res.data;
}

export async function updateSupplier(id: number, supplierData: any): Promise<any> {
  const res = await apiRequest(`/api/v1/creditors/creditors/${id}/`, {
    method: 'PATCH',
    data: supplierData,
  });
  return res.data;
}

export async function deleteSupplier(id: number): Promise<void> {
  await apiRequest(`/api/v1/creditors/creditors/${id}/`, {
    method: 'DELETE',
  });
}