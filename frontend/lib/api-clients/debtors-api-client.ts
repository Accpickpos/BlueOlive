/**
 * Debtors API Client
 * Handles all Debtors API interactions with proper authentication, error handling, and tenant isolation
 * 
 * Authentication: JWT Bearer token in Authorization header
 * Tenant Isolation: X-Tenant-ID header for multi-tenant support
 */

import { API_BASE_URL, ENDPOINTS, buildApiUrl } from '../api-config';

// ===== TYPE DEFINITIONS =====
export interface DebtorAccount {
  dno: string;
  dname: string;
  dcrnt: number;
  dtype: 'IN' | 'CN' | 'CS' | 'CR' | 'RCP' | 'INT' | 'JD' | 'JC';
  created_at: string;
  [key: string]: any;
}

export interface DebtorTransaction {
  id: string;
  dno: string;
  dtype: 'IN' | 'CN' | 'CS' | 'CR' | 'RCP' | 'INT' | 'JD' | 'JC';
  amount: number;
  date: string;
  [key: string]: any;
}

export interface OpenItem {
  id: string;
  dno: string;
  amount: number;
  due_date: string;
  [key: string]: any;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  status: number;
  message: string;
  errors?: Record<string, string[]>;
}

export interface QueryParams {
  search?: string;
  ordering?: string;
  limit?: number;
  offset?: number;
  dtype?: string;
  [key: string]: any;
}

// ===== DEBTORS API CLIENT =====
export class DebtorsApiClient {
  private baseUrl: string;
  private tenantId: string | null = null;
  private accessToken: string | null = null;

  constructor(tenantId?: string, accessToken?: string) {
    this.baseUrl = API_BASE_URL;
    this.tenantId = tenantId || null;
    this.accessToken = accessToken || null;
  }

  /**
   * Set the tenant ID for subsequent requests
   */
  setTenantId(tenantId: string): void {
    this.tenantId = tenantId;
  }

  /**
   * Set the JWT access token for authentication
   */
  setAccessToken(accessToken: string): void {
    this.accessToken = accessToken;
  }

  /**
   * Build common headers with authentication and tenant info
   */
  private getHeaders(contentType: string = 'application/json'): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': contentType,
      'Accept': 'application/json',
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    if (this.tenantId) {
      headers['X-Tenant-ID'] = this.tenantId;
    }

    // Add X-Shop-ID header for shop identification (critical for pre-authentication)
    if (typeof window !== 'undefined') {
      const shopId = localStorage.getItem('currentShopId');
      if (shopId) {
        headers['X-Shop-ID'] = shopId;
      }
    }

    return headers;
  }

  /**
   * Build query string from parameters
   */
  private buildQueryString(params: QueryParams): string {
    const queryParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, String(value));
      }
    });

    const queryString = queryParams.toString();
    return queryString ? `?${queryString}` : '';
  }

  /**
   * Handle API response and errors
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status} ${response.statusText}`;
      let errors: Record<string, string[]> | undefined;

      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
        errors = errorData.errors || errorData;
      } catch {
        // Continue with default error message
      }

      const error: ApiError = {
        status: response.status,
        message: errorMessage,
        errors,
      };

      throw error;
    }

    try {
      return await response.json();
    } catch {
      return {} as T;
    }
  }

  // ===== DEBTOR ACCOUNTS =====

  /**
   * Get all debtor accounts with optional filtering and pagination
   */
  async getDebtors(params: QueryParams = {}): Promise<PaginatedResponse<DebtorAccount>> {
    const url = buildApiUrl(ENDPOINTS.DEBTORS.ACCOUNTS) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<DebtorAccount>>(response);
  }

  /**
   * Get a specific debtor account by debtor number
   */
  async getDebtorById(dno: string): Promise<DebtorAccount> {
    const url = buildApiUrl(`${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/`);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<DebtorAccount>(response);
  }

  /**
   * Create a new debtor account
   */
  async createDebtor(data: Partial<DebtorAccount>): Promise<DebtorAccount> {
    const url = buildApiUrl(ENDPOINTS.DEBTORS.ACCOUNTS);

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<DebtorAccount>(response);
  }

  /**
   * Update a debtor account
   */
  async updateDebtor(dno: string, data: Partial<DebtorAccount>): Promise<DebtorAccount> {
    const url = buildApiUrl(`${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/`);

    const response = await fetch(url, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<DebtorAccount>(response);
  }

  /**
   * Delete a debtor account
   */
  async deleteDebtor(dno: string): Promise<void> {
    const url = buildApiUrl(`${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/`);

    const response = await fetch(url, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      await this.handleResponse<void>(response);
    }
  }

  // ===== DEBTOR TRANSACTIONS =====

  /**
   * Get transactions for all debtors
   */
  async getTransactions(params: QueryParams = {}): Promise<PaginatedResponse<DebtorTransaction>> {
    const url = buildApiUrl(ENDPOINTS.DEBTORS.TRANSACTIONS) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<DebtorTransaction>>(response);
  }

  /**
   * Get transactions for a specific debtor
   */
  async getDebtorTransactions(dno: string, params: QueryParams = {}): Promise<PaginatedResponse<DebtorTransaction>> {
    const url = buildApiUrl(ENDPOINTS.DEBTORS.DEBTOR_TRANSACTIONS(dno)) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<DebtorTransaction>>(response);
  }

  // ===== OPEN ITEMS =====

  /**
   * Get open items (unpaid invoices) for all debtors
   */
  async getOpenItems(params: QueryParams = {}): Promise<PaginatedResponse<OpenItem>> {
    const url = buildApiUrl(ENDPOINTS.DEBTORS.OPEN_ITEMS) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<OpenItem>>(response);
  }

  // ===== POST DATED CHEQUES =====

  /**
   * Get post-dated cheques (PDC)
   */
  async getPostDatedCheques(params: QueryParams = {}): Promise<PaginatedResponse<any>> {
    const url = buildApiUrl(ENDPOINTS.DEBTORS.POST_DATED_CHEQUES) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<any>>(response);
  }

  // ===== AUDIT TRAIL =====

  /**
   * Get audit trail for debtors
   */
  async getAuditTrail(params: QueryParams = {}): Promise<PaginatedResponse<any>> {
    const url = buildApiUrl(ENDPOINTS.DEBTORS.AUDIT) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<any>>(response);
  }

  // ===== SALES AREAS =====

  /**
   * Get sales areas for debtors
   */
  async getSalesAreas(): Promise<any[]> {
    const url = buildApiUrl(ENDPOINTS.DEBTORS.SALES_AREAS);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<any[]>(response);
  }

  // ===== SPECIAL ACTIONS =====

  /**
   * Get age analysis for a debtor (aging of outstanding amounts)
   */
  async getAgeAnalysis(dno: string): Promise<any> {
    const url = buildApiUrl(ENDPOINTS.DEBTORS.AGE_ANALYSIS(dno));

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<any>(response);
  }

  /**
   * Get balance details for a debtor
   */
  async getBalanceDetails(dno: string): Promise<any> {
    const url = buildApiUrl(ENDPOINTS.DEBTORS.BALANCE_DETAILS(dno));

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<any>(response);
  }

  /**
   * Block a debtor account (prevent further transactions)
   */
  async blockDebtor(dno: string, reason?: string): Promise<any> {
    const url = buildApiUrl(ENDPOINTS.DEBTORS.BLOCK_ACCOUNT(dno));

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ reason }),
    });

    return this.handleResponse<any>(response);
  }

  /**
   * Unblock a debtor account
   */
  async unblockDebtor(dno: string, reason?: string): Promise<any> {
    const url = buildApiUrl(ENDPOINTS.DEBTORS.UNBLOCK_ACCOUNT(dno));

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ reason }),
    });

    return this.handleResponse<any>(response);
  }

  /**
   * Get summary of debtors (totals, counts, etc.)
   */
  async getSummary(): Promise<any> {
    const url = buildApiUrl(ENDPOINTS.DEBTORS.SUMMARY);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<any>(response);
  }
}

// ===== SINGLETON INSTANCE =====
let debtorsApiClient: DebtorsApiClient | null = null;

/**
 * Get or create a singleton instance of the DebtorsApiClient
 */
export function getDebtorsApiClient(tenantId?: string, accessToken?: string): DebtorsApiClient {
  if (!debtorsApiClient) {
    debtorsApiClient = new DebtorsApiClient(tenantId, accessToken);
  } else {
    if (tenantId) debtorsApiClient.setTenantId(tenantId);
    if (accessToken) debtorsApiClient.setAccessToken(accessToken);
  }
  return debtorsApiClient;
}

/**
 * Reset the singleton instance (useful for testing or logout)
 */
export function resetDebtorsApiClient(): void {
  debtorsApiClient = null;
}
