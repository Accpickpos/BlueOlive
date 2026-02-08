import axios, { AxiosInstance, AxiosResponse } from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
const POS_API_BASE = process.env.NEXT_PUBLIC_POS_API_BASE || 'http://localhost:8001';

/**
 * Security Note: Tokens are stored in httpOnly cookies (set by backend)
 * and are NOT accessible to JavaScript. The browser automatically includes
 * them in requests, providing protection against XSS attacks.
 * 
 * To check if user is authenticated, make a request to /api/auth/profile/
 * or similar endpoint that returns 401 if not authenticated.
 */

export async function isAuthenticated(): Promise<boolean> {
  try {
    const response = await api.get('/api/auth/profile/');
    return response.status === 200;
  } catch {
    return false;
  }
}

export function clearAuthData(): void {
  // Cookies are automatically cleared by the server via logout endpoint
  // No need to manually clear localStorage
}

// Store CSRF token globally
let csrfToken: string | null = null;

// Function to get CSRF token from backend
export async function fetchCSRFToken(): Promise<string> {
  if (csrfToken) {
    return csrfToken;
  }
  
  try {
    // GET request to CSRF endpoint to get token in cookie
    const response = await axios.get(`${API_BASE}/api/auth/csrf/`, {
      withCredentials: true,
    });
    
    // CSRF token should be in cookie after this call
    const cookieToken = getCsrfTokenFromCookie();
    if (cookieToken) {
      csrfToken = cookieToken;
      return cookieToken;
    }
  } catch (error) {
    // Try to get from cookies even on error
    const cookieToken = getCsrfTokenFromCookie();
    if (cookieToken) {
      csrfToken = cookieToken;
      return cookieToken;
    }
  }
  
  return '';
}

// Helper to extract CSRF token from cookies
function getCsrfTokenFromCookie(): string | null {
  const name = 'csrftoken';
  let cookieValue = null;
  
  if (document.cookie && document.cookie !== '') {
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

const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  withCredentials: true, // Include cookies in cross-origin requests
});

// Add CSRF token to headers for all requests
api.interceptors.request.use(async (config) => {
  // Only add CSRF token for non-GET requests
  if (config.method && ['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())) {
    // Try to get CSRF token from cookie first
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

export async function apiRequest(endpoint: string, options: any = {}): Promise<AxiosResponse> {
  const { method = 'GET', headers, body, ...rest } = options;
  return api({
    url: endpoint,
    method,
    headers,
    data: body,
    ...rest,
  });
}

export async function login(tenant_slug: string, username: string, password: string): Promise<AxiosResponse> {
  const response = await api.post('/api/auth/login/', {
    username,
    password,
    tenant_slug,
  });

  // Tokens are set in httpOnly cookies by the backend
  // Frontend just stores user info if needed
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
  const response = await api.post('/api/auth/signup/', signupData);
  // Tokens are set in httpOnly cookies by the backend
  return response;
}

export async function logout(): Promise<AxiosResponse> {
  try {
    console.log('Calling logout endpoint...');
    const response = await api.post('/api/auth/logout/');
    console.log('Logout successful:', response.data);
    // Cookies are automatically cleared by the server
    return response;
  } catch (error) {
    console.error('Logout error:', error);
    // Still consider it a success if we get a 4xx or 5xx response
    // since the important thing is clearing cookies
    throw error;
  }
}

export async function refreshToken(): Promise<AxiosResponse> {
  // Refresh token is sent via httpOnly cookie automatically
  const response = await api.post('/api/auth/token/refresh/');
  return response;
}

export async function getCurrentUser(): Promise<any> {
  const res = await apiRequest('/api/auth/profile/');
  return res.data;
}

export async function getCurrentTenant(): Promise<any> {
  const res = await apiRequest('/api/current_tenant/');
  return res.data;
}

export async function getUsers(): Promise<any[]> {
  const res = await apiRequest('/api/users/');
  return res.data;
}

export async function getShops(): Promise<any[]> {
  const res = await apiRequest('/api/shops/');
  return res.data;
}

export async function createUser(userData: any): Promise<any> {
  const res = await apiRequest('/api/users/', {
    method: 'POST',
    data: userData,
  });
  return res.data;
}

export async function updateUser(id: number, userData: any): Promise<any> {
  const res = await apiRequest(`/api/users/${id}/`, {
    method: 'PATCH',
    data: userData,
  });
  return res.data;
}

export async function deleteUser(id: number): Promise<void> {
  await apiRequest(`/api/users/${id}/`, {
    method: 'DELETE',
  });
}

export async function createShop(shopData: any): Promise<any> {
  const res = await apiRequest('/api/shops/', {
    method: 'POST',
    data: shopData,
  });
  return res.data;
}

export async function updateShop(id: number, shopData: any): Promise<any> {
  const res = await apiRequest(`/api/shops/${id}/`, {
    method: 'PUT',
    data: shopData,
  });
  return res.data;
}

export async function deleteShop(id: number): Promise<void> {
  await apiRequest(`/api/shops/${id}/`, {
    method: 'DELETE',
  });
}

export async function getTenants(): Promise<any[]> {
  const res = await apiRequest('/api/tenants/');
  return res.data;
}

export async function getTenantShops(tenantSlug?: string): Promise<any[]> {
  const url = tenantSlug ? `/api/tenant_shops/?tenant=${tenantSlug}` : '/api/tenant_shops/';
  const res = await apiRequest(url);
  return res.data;
}

export async function createTenant(tenantData: any): Promise<AxiosResponse> {
  return apiRequest('/api/tenants/', {
    method: 'POST',
    data: tenantData,
  });
}

// ========================================
// POS API Integration (FastAPI)
// ========================================

const posApi: AxiosInstance = axios.create({
  baseURL: POS_API_BASE,
  withCredentials: true,
});

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