/**
 * Debtors API Client
 * 
 * Handles all communication with Django backend for:
 * - Debtor/Customer management
 * - Debtor transactions
 * - Debtor invoices
 * - Debtor enquiries and reporting
 */

import { api } from './api';

export interface DebtorCreateData {
  account_number?: number;
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
  credit_limit?: number;
  credit_terms?: number | null;
  is_active?: boolean;
}

export interface Debtor extends DebtorCreateData {
  id?: number;
  total_balance?: number;
  total_receivable?: number;
  balance_current?: number;
  balance_30_days?: number;
  balance_60_days?: number;
  balance_90_days?: number;
  balance_120_days?: number;
  balance_150_days?: number;
  balance_180_days?: number;
  days_sales_outstanding?: number;
  last_transaction_date?: string;
  sales_mtd?: number;
  sales_ytd?: number;
  created_at?: string;
  updated_at?: string;
}

export interface DebtorBalanceDetails {
  debtor_id: number;
  account_number?: number;
  debtor_name?: string;
  balance_current: number;
  balance_30_days: number;
  balance_60_days: number;
  balance_90_days: number;
  balance_120_days: number;
  balance_150_days: number;
  balance_180_days: number;
  total_balance: number;
  credit_limit?: number;
  days_sales_outstanding?: number;
}

export interface DebtorTransaction {
  id?: number;
  debtor_id: number;
  transaction_date: string;
  transaction_type: 'INVOICE' | 'PAYMENT' | 'CREDIT_NOTE' | 'DEBIT_NOTE' | 'INTEREST';
  reference_number?: string;
  description?: string;
  amount: number;
  balance?: number;
  created_at?: string;
  updated_at?: string;
}

export interface DebtorInvoice {
  id?: number;
  debtor_id: number;
  invoice_number: string;
  invoice_date: string;
  due_date?: string;
  amount: number;
  paid_amount?: number;
  outstanding_amount?: number;
  status?: 'DRAFT' | 'ISSUED' | 'PAID' | 'OVERDUE' | 'CANCELLED';
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface PostDatedCheque {
  id?: number;
  debtor_id: number;
  cheque_number: string;
  bank_name?: string;
  cheque_date: string;
  amount: number;
  status?: 'PENDING' | 'CLEARED' | 'BOUNCED' | 'CANCELLED';
  created_at?: string;
  updated_at?: string;
}

export interface TopAccount {
  debtor_id: number;
  account_number?: number;
  debtor_name: string;
  total_balance: number;
  rank?: number;
}

class DebtorsAPI {
  /**
   * Make HTTP request using axios with error handling
   */
  private async request<T>(
    method: string,
    endpoint: string,
    data?: any
  ): Promise<T> {
    try {
      console.log(`\n=== DEBTORS API REQUEST ===`);
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
      console.error('=== DEBTORS API ERROR ===');
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
  // DEBTOR ENDPOINTS
  // ============================================================

  /**
   * List all debtors
   */
  async listDebtors(filters?: {
    is_active?: boolean;
    search?: string;
    page?: number;
  }): Promise<{ results: Debtor[]; count: number; next?: string; previous?: string }> {
    let endpoint = '/api/debtors/';
    if (filters) {
      const params = new URLSearchParams();
      if (filters.is_active !== undefined) params.append('is_active', String(filters.is_active));
      if (filters.search) params.append('search', filters.search);
      if (filters.page) params.append('page', String(filters.page));
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Get debtor by ID
   */
  async getDebtor(debtorId: number): Promise<Debtor> {
    return this.request('GET', `/api/debtors/${debtorId}/`);
  }

  /**
   * Create new debtor
   */
  async createDebtor(data: DebtorCreateData): Promise<Debtor> {
    return this.request('POST', '/api/debtors/', data);
  }

  /**
   * Update debtor
   */
  async updateDebtor(debtorId: number, data: Partial<DebtorCreateData>): Promise<Debtor> {
    return this.request('PUT', `/api/debtors/${debtorId}/`, data);
  }

  /**
   * Partially update debtor
   */
  async partialUpdateDebtor(debtorId: number, data: Partial<DebtorCreateData>): Promise<Debtor> {
    return this.request('PATCH', `/api/debtors/${debtorId}/`, data);
  }

  /**
   * Delete debtor
   */
  async deleteDebtor(debtorId: number): Promise<void> {
    await this.request('DELETE', `/api/debtors/${debtorId}/`);
  }

  // ============================================================
  // DEBTOR BALANCE ENDPOINTS
  // ============================================================

  /**
   * Get balance details for a debtor
   */
  async getDebtorBalanceDetails(debtorId: number): Promise<DebtorBalanceDetails> {
    return this.request('GET', `/api/debtors/${debtorId}/balance-details/`);
  }

  // ============================================================
  // DEBTOR TRANSACTION ENDPOINTS
  // ============================================================

  /**
   * List transactions for a debtor
   */
  async listTransactions(filters?: {
    debtor?: number;
    transaction_type?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
  }): Promise<{ results: DebtorTransaction[]; count: number }> {
    let endpoint = '/api/debtors/transactions/';
    if (filters) {
      const params = new URLSearchParams();
      if (filters.debtor) params.append('debtor', String(filters.debtor));
      if (filters.transaction_type) params.append('transaction_type', filters.transaction_type);
      if (filters.start_date) params.append('transaction_date__gte', filters.start_date);
      if (filters.end_date) params.append('transaction_date__lte', filters.end_date);
      if (filters.page) params.append('page', String(filters.page));
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Get transaction by ID
   */
  async getTransaction(transactionId: number): Promise<DebtorTransaction> {
    return this.request('GET', `/api/debtors/transactions/${transactionId}/`);
  }

  /**
   * Create new transaction
   */
  async createTransaction(data: DebtorTransaction): Promise<DebtorTransaction> {
    return this.request('POST', '/api/debtors/transactions/', data);
  }

  /**
   * Update transaction
   */
  async updateTransaction(transactionId: number, data: Partial<DebtorTransaction>): Promise<DebtorTransaction> {
    return this.request('PUT', `/api/debtors/transactions/${transactionId}/`, data);
  }

  /**
   * Delete transaction
   */
  async deleteTransaction(transactionId: number): Promise<void> {
    await this.request('DELETE', `/api/debtors/transactions/${transactionId}/`);
  }

  // ============================================================
  // DEBTOR INVOICE ENDPOINTS
  // ============================================================

  /**
   * List invoices
   */
  async listInvoices(filters?: {
    debtor_id?: number;
    status?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
  }): Promise<{ results: DebtorInvoice[]; count: number }> {
    let endpoint = '/api/debtors/invoices/';
    if (filters) {
      const params = new URLSearchParams();
      if (filters.debtor_id) params.append('debtor', String(filters.debtor_id));
      if (filters.status) params.append('status', filters.status);
      if (filters.start_date) params.append('invoice_date__gte', filters.start_date);
      if (filters.end_date) params.append('invoice_date__lte', filters.end_date);
      if (filters.page) params.append('page', String(filters.page));
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Get invoice by ID
   */
  async getInvoice(invoiceId: number): Promise<DebtorInvoice> {
    return this.request('GET', `/api/debtors/invoices/${invoiceId}/`);
  }

  /**
   * Create new invoice
   */
  async createInvoice(data: DebtorInvoice): Promise<DebtorInvoice> {
    return this.request('POST', '/api/debtors/invoices/', data);
  }

  /**
   * Update invoice
   */
  async updateInvoice(invoiceId: number, data: Partial<DebtorInvoice>): Promise<DebtorInvoice> {
    return this.request('PUT', `/api/debtors/invoices/${invoiceId}/`, data);
  }

  /**
   * Partially update invoice
   */
  async partialUpdateInvoice(invoiceId: number, data: Partial<DebtorInvoice>): Promise<DebtorInvoice> {
    return this.request('PATCH', `/api/debtors/invoices/${invoiceId}/`, data);
  }

  /**
   * Delete invoice
   */
  async deleteInvoice(invoiceId: number): Promise<void> {
    await this.request('DELETE', `/api/debtors/invoices/${invoiceId}/`);
  }

  // ============================================================
  // POST-DATED CHEQUE ENDPOINTS
  // ============================================================

  /**
   * List post-dated cheques
   */
  async listPostDatedCheques(filters?: {
    debtor?: number;
    status?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
  }): Promise<{ results: PostDatedCheque[]; count: number }> {
    let endpoint = '/api/debtors/post-dated-cheques/';
    if (filters) {
      const params = new URLSearchParams();
      if (filters.debtor) params.append('debtor', String(filters.debtor));
      if (filters.status) params.append('status', filters.status);
      if (filters.start_date) params.append('cheque_date__gte', filters.start_date);
      if (filters.end_date) params.append('cheque_date__lte', filters.end_date);
      if (filters.page) params.append('page', String(filters.page));
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Get post-dated cheque by ID
   */
  async getPostDatedCheque(chequeId: number): Promise<PostDatedCheque> {
    return this.request('GET', `/api/debtors/post-dated-cheques/${chequeId}/`);
  }

  /**
   * Create new post-dated cheque
   */
  async createPostDatedCheque(data: PostDatedCheque): Promise<PostDatedCheque> {
    return this.request('POST', '/api/debtors/post-dated-cheques/', data);
  }

  /**
   * Update post-dated cheque
   */
  async updatePostDatedCheque(chequeId: number, data: Partial<PostDatedCheque>): Promise<PostDatedCheque> {
    return this.request('PUT', `/api/debtors/post-dated-cheques/${chequeId}/`, data);
  }

  /**
   * Delete post-dated cheque
   */
  async deletePostDatedCheque(chequeId: number): Promise<void> {
    await this.request('DELETE', `/api/debtors/post-dated-cheques/${chequeId}/`);
  }

  // ============================================================
  // REPORTING/ENQUIRY ENDPOINTS
  // ============================================================

  /**
   * Get top accounts by outstanding balance
   */
  async getTopAccounts(filters?: {
    limit?: number;
    start_date?: string;
    end_date?: string;
  }): Promise<TopAccount[]> {
    let endpoint = '/api/debtors/top-accounts/';
    if (filters) {
      const params = new URLSearchParams();
      if (filters.limit) params.append('limit', String(filters.limit));
      if (filters.start_date) params.append('date__gte', filters.start_date);
      if (filters.end_date) params.append('date__lte', filters.end_date);
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Search debtors by name or account number
   */
  async searchDebtors(query: string, limit: number = 20): Promise<Debtor[]> {
    const params = new URLSearchParams({
      search: query,
      limit: String(limit),
    });
    return this.request('GET', `/api/debtors/?${params}`);
  }
}

// Export singleton with simpler initialization
const debtorsAPI = new DebtorsAPI();

export const useDebtorsAPI = () => {
  return debtorsAPI;
};

export default DebtorsAPI;
