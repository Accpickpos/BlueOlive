/**
 * Creditors API Client
 * Handles all Creditors API interactions with proper authentication, error handling, and tenant isolation
 * 
 * Authentication: JWT Bearer token in Authorization header
 * Tenant Isolation: X-Tenant-ID header for multi-tenant support
 * 
 * Authentication Rules:
 * - All endpoints require IsAuthenticated permission
 * - User must be logged in and belong to a tenant
 * - JWT token must be valid and not expired
 * 
 * Required Headers:
 * - Authorization: Bearer <jwt_token>
 * - Content-Type: application/json
 * - X-Tenant-ID: <tenant_id>
 */

import { API_BASE_URL, ENDPOINTS, buildApiUrl } from '../api-config';
import {
  CreditorAccount,
  CreditorCreateData,
  CreditorEditData,
  ExpenseCategory,
  ExpenseCategoryCreateData,
  Transaction,
  TransactionCreateData,
  TransactionFilters,
  CreditorFilters,
  ExpenseCategoryFilters,
  CreditorsSummary,
  PaginatedResponse,
} from '../types/creditors';

// ===== TYPE DEFINITIONS =====
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
  page?: number;
  page_size?: number;
  is_active?: boolean;
  account_type?: string;
  [key: string]: any;
}

// ===== CREDITORS API CLIENT =====
export class CreditorsApiClient {
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
   * 
   * Required Headers:
   * - Authorization: Bearer <jwt_token>
   * - Content-Type: application/json
   * - X-Tenant-ID: <tenant_id>
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
   * 
   * Error codes:
   * 401 Unauthorized: Missing or invalid token
   * 400 Bad Request: Validation error (check error and details)
   * 404 Not Found: Resource not found
   * 500 Internal Server Error: Server error
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

  // ===== CREDITOR ACCOUNTS =====

  /**
   * Get all creditor accounts with optional filtering and pagination
   * 
   * Query Parameters:
   * - is_active: boolean
   * - account_type: 'BBF' | 'OI'
   * - search: supplier name or number
   * - ordering: field name for sorting (prefix with - for descending)
   * - page: page number
   * - page_size: items per page
   */
  async getCreditors(params: QueryParams = {}): Promise<PaginatedResponse<CreditorAccount>> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.ACCOUNTS) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<CreditorAccount>>(response);
  }

  /**
   * Get a specific creditor account by ID
   */
  async getCreditorById(id: string | number): Promise<CreditorAccount> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<CreditorAccount>(response);
  }

  /**
   * Create a new creditor account
   * 
   * Required fields:
   * - supplier_number: string (unique, max 20)
   * - name: string (required)
   * - credit_terms: integer (CreditTerms ID)
   * 
   * Optional fields:
   * - email: string (validated)
   * - telephone: string
   * - contact_person: string
   * - account_type: 'BBF' | 'OI'
   * - payment_discount_percent: 0-100
   * - bank_name, branch_code, account_number
   * - is_active: boolean
   * 
   * Validation Rules:
   * - supplier_number must be unique
   * - email must contain '@' if provided
   * - payment_discount_percent must be 0-100
   * - all amounts must be positive
   */
  async createCreditor(data: CreditorCreateData): Promise<CreditorAccount> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.ACCOUNTS);

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<CreditorAccount>(response);
  }

  /**
   * Update a creditor account
   */
  async updateCreditor(id: string | number, data: CreditorEditData): Promise<CreditorAccount> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`);

    const response = await fetch(url, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<CreditorAccount>(response);
  }

  /**
   * Delete a creditor account
   */
  async deleteCreditor(id: string | number): Promise<void> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`);

    const response = await fetch(url, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      await this.handleResponse<void>(response);
    }
  }

  // ===== GOODS RECEIVED NOTES (GRN) =====

  /**
   * Get all GRNs
   */
  async getGrns(params: QueryParams = {}): Promise<PaginatedResponse<any>> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.GRNS) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<any>>(response);
  }

  /**
   * Get a specific GRN by ID
   */
  async getGrnById(id: string | number): Promise<any> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.GRNS}${id}/`);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<any>(response);
  }

  /**
   * Create a new GRN
   */
  async createGrn(data: any): Promise<any> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.GRNS);

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<any>(response);
  }

  /**
   * Update a GRN
   */
  async updateGrn(id: string | number, data: any): Promise<any> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.GRNS}${id}/`);

    const response = await fetch(url, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<any>(response);
  }

  // ===== INVOICES =====

  /**
   * Get all creditor invoices
   */
  async getInvoices(params: QueryParams = {}): Promise<PaginatedResponse<Transaction>> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.INVOICES) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<Transaction>>(response);
  }

  /**
   * Get a specific invoice by ID
   */
  async getInvoiceById(id: string | number): Promise<Transaction> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.INVOICES}${id}/`);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Create a new invoice
   */
  async createInvoice(data: TransactionCreateData): Promise<Transaction> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.INVOICES);

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Update an invoice
   */
  async updateInvoice(id: string | number, data: Partial<TransactionCreateData>): Promise<Transaction> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.INVOICES}${id}/`);

    const response = await fetch(url, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<Transaction>(response);
  }

  // ===== PAYMENTS =====

  /**
   * Get all payments to creditors
   */
  async getPayments(params: QueryParams = {}): Promise<PaginatedResponse<Transaction>> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.PAYMENTS) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<Transaction>>(response);
  }

  /**
   * Get a specific payment by ID
   */
  async getPaymentById(id: string | number): Promise<Transaction> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.PAYMENTS}${id}/`);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Create a new payment
   */
  async createPayment(data: TransactionCreateData): Promise<Transaction> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.PAYMENTS);

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Update a payment
   */
  async updatePayment(id: string | number, data: Partial<TransactionCreateData>): Promise<Transaction> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.PAYMENTS}${id}/`);

    const response = await fetch(url, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<Transaction>(response);
  }

  // ===== JOURNALS =====

  /**
   * Get all journal entries
   */
  async getJournals(params: QueryParams = {}): Promise<PaginatedResponse<Transaction>> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.JOURNALS) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<Transaction>>(response);
  }

  /**
   * Get a specific journal entry by ID
   */
  async getJournalById(id: string | number): Promise<Transaction> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.JOURNALS}${id}/`);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Create a new journal entry
   */
  async createJournal(data: TransactionCreateData): Promise<Transaction> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.JOURNALS);

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<Transaction>(response);
  }

  // ===== OPEN ITEMS =====

  /**
   * Get open items (unpaid invoices) for all creditors
   */
  async getOpenItems(params: QueryParams = {}): Promise<PaginatedResponse<Transaction>> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.OPEN_ITEMS) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<Transaction>>(response);
  }

  // ===== RFC (REQUEST FOR CREDIT) =====

  /**
   * Get all RFC requests
   */
  async getRfcs(params: QueryParams = {}): Promise<PaginatedResponse<any>> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.RFC) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<any>>(response);
  }

  /**
   * Get a specific RFC request by ID
   */
  async getRfcById(id: string | number): Promise<any> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.RFC}${id}/`);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<any>(response);
  }

  /**
   * Create a new RFC request
   */
  async createRfc(data: any): Promise<any> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.RFC);

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<any>(response);
  }

  /**
   * Update an RFC request
   */
  async updateRfc(id: string | number, data: any): Promise<any> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.RFC}${id}/`);

    const response = await fetch(url, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<any>(response);
  }

  // ===== EXPENSE CATEGORIES =====

  /**
   * Get all expense categories
   */
  async getExpenseCategories(params: QueryParams = {}): Promise<PaginatedResponse<ExpenseCategory>> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.EXPENSE_CATEGORIES) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<ExpenseCategory>>(response);
  }

  /**
   * Get a specific expense category by ID
   */
  async getExpenseCategoryById(id: string | number): Promise<ExpenseCategory> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.EXPENSE_CATEGORIES}${id}/`);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<ExpenseCategory>(response);
  }

  /**
   * Create a new expense category
   */
  async createExpenseCategory(data: ExpenseCategoryCreateData): Promise<ExpenseCategory> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.EXPENSE_CATEGORIES);

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<ExpenseCategory>(response);
  }

  /**
   * Update an expense category
   */
  async updateExpenseCategory(
    id: string | number,
    data: Partial<ExpenseCategoryCreateData>
  ): Promise<ExpenseCategory> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.EXPENSE_CATEGORIES}${id}/`);

    const response = await fetch(url, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<ExpenseCategory>(response);
  }

  // ===== AGING ANALYSIS =====

  /**
   * Get aging analysis for a specific creditor
   * Returns balance aging breakdown by days
   */
  async getCreditorAgingAnalysis(id: string | number): Promise<any> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/aging-analysis/`);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<any>(response);
  }

  /**
   * Get outstanding items for a specific creditor
   * Returns overdue and outstanding items
   */
  async getCreditorOutstandingItems(id: string | number): Promise<PaginatedResponse<Transaction>> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/outstanding-items/`);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<Transaction>>(response);
  }

  /**
   * Get all outstanding items across creditors
   */
  async getOutstandingBalance(params: QueryParams = {}): Promise<PaginatedResponse<Transaction>> {
    const url = buildApiUrl(`${ENDPOINTS.CREDITORS.ACCOUNTS}outstanding-balance/`) + this.buildQueryString(params);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<PaginatedResponse<Transaction>>(response);
  }

  /**
   * Get summary of creditors (totals, counts, etc.)
   */
  async getSummary(): Promise<CreditorsSummary> {
    const url = buildApiUrl(ENDPOINTS.CREDITORS.SUMMARY);

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<CreditorsSummary>(response);
  }
}

// ===== SINGLETON INSTANCE =====
let creditorsApiClient: CreditorsApiClient | null = null;

/**
 * Get or create a singleton instance of the CreditorsApiClient
 */
export function getCreditorsApiClient(tenantId?: string, accessToken?: string): CreditorsApiClient {
  if (!creditorsApiClient) {
    creditorsApiClient = new CreditorsApiClient(tenantId, accessToken);
  } else {
    if (tenantId) creditorsApiClient.setTenantId(tenantId);
    if (accessToken) creditorsApiClient.setAccessToken(accessToken);
  }
  return creditorsApiClient;
}

/**
 * Reset the singleton instance (useful for testing or logout)
 */
export function resetCreditorsApiClient(): void {
  creditorsApiClient = null;
}
