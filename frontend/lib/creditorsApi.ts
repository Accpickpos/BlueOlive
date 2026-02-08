/**
 * Creditors API Client
 * 
 * Handles all communication with Django backend for:
 * - Supplier/Creditor management
 * - Expense categories
 * - Creditor transactions
 */

import { api } from './api';

export interface SupplierCreateData {
  supplier_number: string | number; // Unique supplier account number
  account_number: string | number; // Account number (same as supplier_number)
  name: string;
  short_name?: string;
  physical_address_line1?: string;
  physical_address_line2?: string;
  physical_address_line3?: string;
  physical_city?: string;
  physical_postal_code?: string;
  postal_address_line1?: string;
  postal_address_line2?: string;
  postal_address_line3?: string;
  postal_city?: string;
  postal_postal_code?: string;
  telephone1?: string;
  telephone2?: string;
  fax?: string;
  email?: string;
  contact_person?: string;
  account_type?: string;
  our_account_number?: string;
  update_selling_price_on_receipt?: boolean;
  credit_terms?: number | null;
  prompt_payment_discount_percent?: number;
  bank_name?: string;
  bank_branch_code?: string;
  bank_account_number?: string;
  vat_number?: string;
  is_active?: boolean;
}

export interface Supplier extends SupplierCreateData {
  id?: number;
  total_balance?: number;
  total_balance_with_rfc?: number;
  balance_current?: number;
  balance_30_days?: number;
  balance_60_days?: number;
  balance_90_days?: number;
  balance_120_days?: number;
  balance_150_days?: number;
  balance_180_days?: number;
  amount_last_paid?: number;
  date_last_paid?: string;
  purchases_mtd?: number;
  purchases_ytd?: number;
  rfc_outstanding_amount?: number;
  account_type_display?: string;
  credit_terms_display?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CreditTermsOption {
  id: number;
  days?: number;
  description?: string;
  name?: string; // For compatibility with form
  is_active?: boolean;
}

export interface ExpenseCategory {
  id?: number;
  number: number;
  name: string;
  category_type?: 'BOTH' | 'CASHBOOK' | 'CREDITORS';
  is_active?: boolean;
  total_mtd?: number;
  total_ytd?: number;
  created_at?: string;
  updated_at?: string;
  created_by_username?: string;
}

export interface ExpenseCategoryCreateData {
  number: number;
  name: string;
  category_type?: 'BOTH' | 'CASHBOOK' | 'CREDITORS';
  is_active?: boolean;
}

export interface OutstandingBalance {
  id: number;
  creditor: number; // Supplier/Creditor ID
  creditor_name: string; // Supplier name
  transaction_date: string; // Transaction date
  transaction_number: string; // Invoice number, etc.
  original_amount: string | number; // Original transaction amount
  balance_due: string | number; // Current balance owed
  age_period: number; // Days overdue (0 = current, 1 = 30 days, etc.)
  // Legacy fields for backward compatibility
  supplier_id?: number;
  supplier?: Supplier;
  capture_date?: string;
  balance_current?: number;
  balance_30_days?: number;
  balance_60_days?: number;
  balance_90_days?: number;
  balance_120_days?: number;
  balance_150_days?: number;
  balance_180_days?: number;
  total_balance?: number;
  created_at?: string;
  updated_at?: string;
}

export interface OutstandingBalanceCaptureData {
  supplier_account_number: number;
  capture_date: string;
  balance_current: number;
  balance_30_days: number;
  balance_60_days: number;
  balance_90_days: number;
  balance_120_days: number;
  balance_150_days: number;
  balance_180_days: number;
}

class CreditorsAPI {
  /**
   * Make HTTP request using axios with error handling
   */
  private async request<T>(
    method: string,
    endpoint: string,
    data?: any
  ): Promise<T> {
    try {
      console.log(`\n=== CREDITORS API REQUEST ===`);
      console.log(`Method: ${method}`);
      console.log(`Endpoint: ${endpoint}`);
      console.log(`Has data: ${!!data}`);
      
      let response;
      switch (method.toUpperCase()) {
        case 'GET':
          console.log('Making GET request...');
          response = await api.get(endpoint);
          break;
        case 'POST':
          console.log('Making POST request...');
          console.log('Data:', data);
          response = await api.post(endpoint, data);
          break;
        case 'PUT':
          console.log('Making PUT request...');
          response = await api.put(endpoint, data);
          break;
        case 'PATCH':
          console.log('Making PATCH request...');
          response = await api.patch(endpoint, data);
          break;
        case 'DELETE':
          console.log('Making DELETE request...');
          response = await api.delete(endpoint);
          break;
        default:
          throw new Error(`Unsupported HTTP method: ${method}`);
      }
      console.log('Response status:', response.status);
      console.log('Response data:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('=== CREDITORS API ERROR ===');
      console.error('Error:', error);
      console.error('Error response:', error.response?.data);
      
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      if (error.response?.data) {
        throw new Error(JSON.stringify(error.response.data));
      }
      throw error;
    }
  }

  // ============================================================
  // SUPPLIER/CREDITOR ENDPOINTS
  // ============================================================

  /**
   * List all suppliers
   */
  async listSuppliers(filters?: {
    is_active?: boolean;
    account_type?: string;
    search?: string;
    page?: number;
  }): Promise<{ results: Supplier[]; count: number; next?: string; previous?: string }> {
    let endpoint = '/api/creditors/suppliers/';
    if (filters) {
      const params = new URLSearchParams();
      if (filters.is_active !== undefined) params.append('is_active', String(filters.is_active));
      if (filters.account_type) params.append('account_type', filters.account_type);
      if (filters.search) params.append('search', filters.search);
      if (filters.page) params.append('page', String(filters.page));
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    const data = await this.request('GET', endpoint);
    
    // Handle both paginated response { results: [...], count: ... } and direct array response
    if (Array.isArray(data)) {
      console.log('Handle array response from backend');
      return { results: data, count: data.length };
    }
    
    if (data.results) {
      return data;
    }
    
    // If data is an object but not the expected format, log warning
    console.warn('Unexpected response format from listSuppliers:', data);
    return { results: [], count: 0 };
  }

  /**
   * Get supplier by account number
   */
  async getSupplier(accountNumber: number): Promise<Supplier> {
    return this.request('GET', `/api/creditors/suppliers/${accountNumber}/`);
  }

  /**
   * Create new supplier
   */
  async createSupplier(data: SupplierCreateData): Promise<Supplier> {
    return this.request('POST', '/api/creditors/suppliers/', data);
  }

  /**
   * Update supplier
   */
  async updateSupplier(accountNumber: number, data: Partial<SupplierCreateData>): Promise<Supplier> {
    return this.request('PUT', `/api/creditors/suppliers/${accountNumber}/`, data);
  }

  /**
   * Partially update supplier
   */
  async partialUpdateSupplier(accountNumber: number, data: Partial<SupplierCreateData>): Promise<Supplier> {
    return this.request('PATCH', `/api/creditors/suppliers/${accountNumber}/`, data);
  }

  /**
   * Delete supplier
   */
  async deleteSupplier(accountNumber: number): Promise<void> {
    await this.request('DELETE', `/api/creditors/suppliers/${accountNumber}/`);
  }

  // ============================================================
  // EXPENSE CATEGORY ENDPOINTS
  // ============================================================

  /**
   * List all credit terms from settings app
   * Falls back to default terms if endpoint fails
   */
  async listCreditTerms(): Promise<CreditTermsOption[]> {
    try {
      const data = await this.request<CreditTermsOption[]>('GET', '/api/settings/credit-terms/');
      // Map backend fields to frontend format for compatibility
      return data.map((term: any) => ({
        id: term.id,
        name: term.days ? `Net ${term.days} Days` : term.description,
        description: term.description,
        days: term.days,
        is_active: term.is_active,
      }));
    } catch (error) {
      console.warn('Failed to fetch credit terms from settings, using defaults:', error);
      // Return default credit terms
      return [
        { id: 1, name: 'Net 30 Days', description: '30 days', days: 30 },
        { id: 2, name: 'Net 60 Days', description: '60 days', days: 60 },
        { id: 3, name: 'Net 90 Days', description: '90 days', days: 90 },
        { id: 4, name: 'Cash on Delivery', description: 'COD', days: 0 },
      ];
    }
  }

  // ============================================================
  // SEARCH ENDPOINTS
  // ============================================================

  /**
   * Search suppliers by name or account number
   */
  async searchSuppliers(query: string, limit: number = 20): Promise<Supplier[]> {
    const params = new URLSearchParams({
      search: query,
      limit: String(limit),
    });
    const data = await this.request('GET', `/api/creditors/suppliers/?${params}`);
    
    // Handle both paginated response and direct array response
    if (Array.isArray(data)) {
      return data;
    }
    
    if (data.results && Array.isArray(data.results)) {
      return data.results;
    }
    
    return [];
  }

  // ============================================================
  // EXPENSE CATEGORY ENDPOINTS (Settings App)
  // ============================================================

  /**
   * List all expense categories
   */
  async listExpenseCategories(): Promise<ExpenseCategory[]> {
    try {
      return await this.request('GET', '/api/settings/expense-categories/');
    } catch (error) {
      console.error('Failed to fetch expense categories:', error);
      return [];
    }
  }

  /**
   * Get expense category by ID
   */
  async getExpenseCategory(id: number): Promise<ExpenseCategory> {
    return this.request('GET', `/api/settings/expense-categories/${id}/`);
  }

  /**
   * Create new expense category
   */
  async createExpenseCategory(data: ExpenseCategoryCreateData): Promise<ExpenseCategory> {
    return this.request('POST', '/api/settings/expense-categories/', data);
  }

  /**
   * Update expense category
   */
  async updateExpenseCategory(id: number, data: Partial<ExpenseCategoryCreateData>): Promise<ExpenseCategory> {
    return this.request('PUT', `/api/settings/expense-categories/${id}/`, data);
  }

  /**
   * Partially update expense category
   */
  async partialUpdateExpenseCategory(id: number, data: Partial<ExpenseCategoryCreateData>): Promise<ExpenseCategory> {
    return this.request('PATCH', `/api/settings/expense-categories/${id}/`, data);
  }

  /**
   * Delete expense category
   */
  async deleteExpenseCategory(id: number): Promise<void> {
    await this.request('DELETE', `/api/settings/expense-categories/${id}/`);
  }

  /**
   * Search expense categories
   */
  async searchExpenseCategories(query: string, limit: number = 20): Promise<ExpenseCategory[]> {
    const params = new URLSearchParams({
      search: query,
      limit: String(limit),
    });
    return this.request('GET', `/api/settings/expense-categories/?${params}`);
  }

  // ============================================================
  // OUTSTANDING BALANCE CAPTURE ENDPOINTS
  // ============================================================

  /**
   * Capture outstanding balance for a supplier
   */
  async captureOutstandingBalance(data: OutstandingBalanceCaptureData): Promise<OutstandingBalance> {
    return this.request('POST', '/api/creditors/outstanding-balance/', data);
  }

  /**
   * Get outstanding balance history for a supplier
   */
  async getOutstandingBalanceHistory(supplierAccountNumber: number): Promise<OutstandingBalance[]> {
    return this.request('GET', `/api/creditors/outstanding-balance/?supplier_account_number=${supplierAccountNumber}`);
  }

  /**
   * List all outstanding balance captures with pagination
   * Response format: { count, total_outstanding, items: [...] }
   */
  async listOutstandingBalances(filters?: {
    supplier_account_number?: number;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<{ items: OutstandingBalance[]; count: number; total_outstanding: string | number }> {
    const params = new URLSearchParams();
    if (filters?.supplier_account_number) {
      params.append('supplier_account_number', String(filters.supplier_account_number));
    }
    if (filters?.start_date) {
      params.append('capture_date__gte', filters.start_date);
    }
    if (filters?.end_date) {
      params.append('capture_date__lte', filters.end_date);
    }
    if (filters?.limit) {
      params.append('limit', String(filters.limit));
    }
    
    const endpoint = `/api/creditors/outstanding-balance/${params.toString() ? '?' + params.toString() : ''}`;
    
    try {
      const data = await this.request('GET', endpoint);
      
      // Handle backend response format: { count, total_outstanding, items: [...] }
      if (data.items !== undefined) {
        return {
          items: data.items,
          count: data.count || data.items.length,
          total_outstanding: data.total_outstanding || '0.00'
        };
      }
      
      // Fallback for legacy response formats
      if (Array.isArray(data)) {
        return { items: data, count: data.length, total_outstanding: '0.00' };
      }
      
      if (data.results !== undefined) {
        return { items: data.results, count: data.count || data.results.length, total_outstanding: '0.00' };
      }
      
      return { items: [], count: 0, total_outstanding: '0.00' };
    } catch (error: any) {
      // Handle 404 gracefully - endpoint may not be implemented yet
      if (error.response?.status === 404) {
        console.warn('Outstanding Balance endpoint not yet available on backend');
        return { items: [], count: 0, total_outstanding: '0.00' };
      }
      throw error;
    }
  }

  /**
   * Get specific outstanding balance record
   */
  async getOutstandingBalance(id: number): Promise<OutstandingBalance> {
    return this.request('GET', `/api/creditors/outstanding-balance/${id}/`);
  }

  /**
   * Update outstanding balance record
   */
  async updateOutstandingBalance(id: number, data: Partial<OutstandingBalanceCaptureData>): Promise<OutstandingBalance> {
    return this.request('PUT', `/api/creditors/outstanding-balance/${id}/`, data);
  }

  /**
   * Delete outstanding balance record
   */
  async deleteOutstandingBalance(id: number): Promise<void> {
    await this.request('DELETE', `/api/creditors/outstanding-balance/${id}/`);
  }
}

// Export singleton with simpler initialization
const creditorsAPI = new CreditorsAPI();

export const useCreditorsAPI = () => {
  return creditorsAPI;
};

export default CreditorsAPI;
