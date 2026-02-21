import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { ENDPOINTS } from './api-config';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
const POS_API_BASE = process.env.NEXT_PUBLIC_POS_API_BASE || 'http://localhost:8001';

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
  timeout: 60000, // 60 second timeout
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
  } else {
    // Use default tenant if no tenant in localStorage
    config.headers['X-Tenant'] = 'dev';
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

export async function login(tenant_slug: string, username: string, password: string): Promise<AxiosResponse> {
  const response = await api.post('/api/v1/users/auth/login/', {
    username,
    password,
    tenant_slug,
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
}): Promise<AxiosResponse> {
  const response = await api.post('/api/v1/users/auth/signup/', signupData);
  
  // Backend returns user object, tokens are in httpOnly cookies set by the server
  // Reset CSRF token cache after successful signup
  csrfToken = null;
  
  return response;
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
  const url = tenantSlug ? `/api/v1/tenant_shops/?tenant=${tenantSlug}` : '/api/v1/tenant_shops/';
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
// Supplier/Creditors API
// ========================================

export async function getSuppliers(): Promise<any[]> {
  const res = await apiRequest('/api/v1/creditors/suppliers/');
  if (Array.isArray(res.data)) {
    return res.data;
  }
  return res.data.results || [];
}

export async function getSupplier(id: number): Promise<any> {
  const res = await apiRequest(`/api/v1/creditors/suppliers/${id}/`);
  return res.data;
}

export async function createSupplier(supplierData: any): Promise<any> {
  const res = await apiRequest('/api/v1/creditors/suppliers/', {
    method: 'POST',
    data: supplierData,
  });
  return res.data;
}

export async function updateSupplier(id: number, supplierData: any): Promise<any> {
  const res = await apiRequest(`/api/v1/creditors/suppliers/${id}/`, {
    method: 'PATCH',
    data: supplierData,
  });
  return res.data;
}

export async function deleteSupplier(id: number): Promise<void> {
  await apiRequest(`/api/v1/creditors/suppliers/${id}/`, {
    method: 'DELETE',
  });
}

// ========================================
// POS API Integration (FastAPI)
// ========================================

const posApi: AxiosInstance = axios.create({
  baseURL: POS_API_BASE,
  withCredentials: true,
});

// Cookies are sent automatically with withCredentials: true
// No need for Authorization header - httpOnly cookie handles authentication

// Add token refresh handling to POS API response errors
posApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Handle 401 Unauthorized on POS API (same as main API)
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Refresh token via httpOnly cookies
        await axios.post(`${API_BASE}/api/v1/users/auth/token/refresh/`, {}, {
          withCredentials: true,
        });
        return posApi(originalRequest);
      } catch (err) {
        return Promise.reject(err);
      }
    }
    
    return Promise.reject(error);
  }
);

// Invoice endpoints
export async function createInvoice(invoiceData: any): Promise<any> {
  const res = await posApi.post('/api/v1/invoices/', invoiceData);
  return res.data;
}

export async function getInvoice(invoiceId: number): Promise<any> {
  const res = await posApi.get(`/api/v1/invoices/${invoiceId}`);
  return res.data;
}

export async function listInvoices(params?: any): Promise<any[]> {
  const res = await posApi.get('/api/v1/invoices/', { params });
  return res.data;
}

export async function updateInvoice(invoiceId: number, data: any): Promise<any> {
  const res = await posApi.put(`/api/v1/invoices/${invoiceId}`, data);
  return res.data;
}

export async function postInvoice(invoiceId: number): Promise<any> {
  const res = await posApi.post(`/api/v1/invoices/${invoiceId}/post`);
  return res.data;
}

export async function deleteInvoice(invoiceId: number): Promise<void> {
  await posApi.delete(`/api/v1/invoices/${invoiceId}`);
}

// Cash Sales endpoints
export async function createCashSale(saleData: any): Promise<any> {
  const res = await posApi.post('/api/v1/cash-sales/', saleData);
  return res.data;
}

export async function getCashSale(saleId: number): Promise<any> {
  const res = await posApi.get(`/api/v1/cash-sales/${saleId}`);
  return res.data;
}

export async function listCashSales(params?: any): Promise<any[]> {
  const res = await posApi.get('/api/v1/cash-sales/', { params });
  return res.data;
}

export async function postCashSale(saleId: number): Promise<any> {
  const res = await posApi.post(`/api/v1/cash-sales/${saleId}/post`);
  return res.data;
}

export async function convertCashSaleToAccount(saleId: number, debtorAccount: string): Promise<any> {
  const res = await posApi.post(`/api/v1/cash-sales/${saleId}/convert-to-account`, null, {
    params: { debtor_account_number: debtorAccount }
  });
  return res.data;
}

export async function deleteCashSale(saleId: number): Promise<void> {
  await posApi.delete(`/api/v1/cash-sales/${saleId}`);
}

// Credit Notes endpoints
export async function createCreditNote(data: any): Promise<any> {
  const res = await posApi.post('/api/v1/credit-notes/', data);
  return res.data;
}

export async function getCreditNote(noteId: number): Promise<any> {
  const res = await posApi.get(`/api/v1/credit-notes/${noteId}`);
  return res.data;
}

export async function listCreditNotes(params?: any): Promise<any[]> {
  const res = await posApi.get('/api/v1/credit-notes/', { params });
  return res.data;
}

export async function postCreditNote(noteId: number): Promise<any> {
  const res = await posApi.post(`/api/v1/credit-notes/${noteId}/post`);
  return res.data;
}

// Receipts endpoints
export async function createReceipt(data: any): Promise<any> {
  const res = await posApi.post('/api/v1/receipts/', data);
  return res.data;
}

export async function getReceipt(receiptId: number): Promise<any> {
  const res = await posApi.get(`/api/v1/receipts/${receiptId}`);
  return res.data;
}

export async function listReceipts(params?: any): Promise<any[]> {
  const res = await posApi.get('/api/v1/receipts/', { params });
  return res.data;
}

export async function postReceipt(receiptId: number): Promise<any> {
  const res = await posApi.post(`/api/v1/receipts/${receiptId}/post`);
  return res.data;
}

// Laybyes endpoints
export async function createLaybye(data: any): Promise<any> {
  const res = await posApi.post('/api/v1/laybyes/', data);
  return res.data;
}

export async function getLaybye(laybieId: number): Promise<any> {
  const res = await posApi.get(`/api/v1/laybyes/${laybieId}`);
  return res.data;
}

export async function listLaybyes(params?: any): Promise<any[]> {
  const res = await posApi.get('/api/v1/laybyes/', { params });
  return res.data;
}

export async function addLaybyePayment(laybieId: number, paymentData: any): Promise<any> {
  const res = await posApi.post(`/api/v1/laybyes/${laybieId}/payments`, paymentData);
  return res.data;
}

// Quotations endpoints
export async function createQuotation(data: any): Promise<any> {
  const res = await posApi.post('/api/v1/quotations/', data);
  return res.data;
}

export async function getQuotation(quotationId: number): Promise<any> {
  const res = await posApi.get(`/api/v1/quotations/${quotationId}`);
  return res.data;
}

export async function listQuotations(params?: any): Promise<any[]> {
  const res = await posApi.get('/api/v1/quotations/', { params });
  return res.data;
}

export async function convertQuotationToInvoice(quotationId: number): Promise<any> {
  const res = await posApi.post(`/api/v1/quotations/${quotationId}/convert`);
  return res.data;
}

// Job Costing endpoints
export async function createJobCosting(data: any): Promise<any> {
  const res = await posApi.post('/api/v1/job-costing/', data);
  return res.data;
}

export async function getJobCosting(jobId: number): Promise<any> {
  const res = await posApi.get(`/api/v1/job-costing/${jobId}`);
  return res.data;
}

export async function listJobCostings(params?: any): Promise<any[]> {
  const res = await posApi.get('/api/v1/job-costing/', { params });
  return res.data;
}

// Repair Controls endpoints
export async function createRepairControl(data: any): Promise<any> {
  const res = await posApi.post('/api/v1/repair-controls/', data);
  return res.data;
}

export async function getRepairControl(repairId: number): Promise<any> {
  const res = await posApi.get(`/api/v1/repair-controls/${repairId}`);
  return res.data;
}

export async function listRepairControls(params?: any): Promise<any[]> {
  const res = await posApi.get('/api/v1/repair-controls/', { params });
  return res.data;
}

// Payouts endpoints
export async function createPayout(data: any): Promise<any> {
  const res = await posApi.post('/api/v1/payouts/', data);
  return res.data;
}

export async function getPayout(payoutId: number): Promise<any> {
  const res = await posApi.get(`/api/v1/payouts/${payoutId}`);
  return res.data;
}

export async function listPayouts(params?: any): Promise<any[]> {
  const res = await posApi.get('/api/v1/payouts/', { params });
  return res.data;
}

// Cash Control endpoints
export async function createCashControl(data: any): Promise<any> {
  const res = await posApi.post('/api/v1/cash-control/', data);
  return res.data;
}

export async function getCashControl(controlId: number): Promise<any> {
  const res = await posApi.get(`/api/v1/cash-control/${controlId}`);
  return res.data;
}

export async function listCashControls(params?: any): Promise<any[]> {
  const res = await posApi.get('/api/v1/cash-control/', { params });
  return res.data;
}

// Transaction Query endpoints
export async function searchTransactions(query: string, filters?: any): Promise<any[]> {
  const res = await posApi.get('/api/v1/transaction-query/search', {
    params: { q: query, ...filters }
  });
  return res.data;
}

export async function getTransactionForReprint(transactionNumber: string): Promise<any> {
  const res = await posApi.get(`/api/v1/transaction-query/reprint/${transactionNumber}`);
  return res.data;
}

// POS System Health Check
export async function checkPOSHealth(): Promise<boolean> {
  try {
    const res = await posApi.get('/health');
    return res.status === 200;
  } catch {
    return false;
  }
}