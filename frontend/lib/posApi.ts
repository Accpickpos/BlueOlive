/**
 * POS Transaction API Client
 * 
 * Handles all communication with FastAPI POS backend for:
 * - Invoices
 * - Cash Sales
 * - Receipts
 * - Laybyes
 * - Quotations
 * - Other transactions
 * 
 * Uses tenant context from headers
 */

import { useAuth } from './useAuth';

export interface TenantContext {
  tenantSlug: string;
  tenantName: string;
}

export interface LineItem {
  item_code: string;
  description: string;
  quantity: number;
  selling_price: number;
  discount_percentage?: number;
  tax_code: 'ZERO' | 'STANDARD' | 'REDUCED';
  cost_price?: number;
}

export interface InvoiceCreateData {
  debtor_account_number: string;
  invoice_date: string; // YYYY-MM-DD
  delivery_date?: string; // YYYY-MM-DD
  delivery_details?: string;
  reg_make_names?: string;
  credit_card?: string;
  order_number?: string;
  customer_ref?: string;
  sman_area?: string;
  line_items: LineItem[];
  notes?: string;
}

export interface CashSaleCreateData {
  sale_date: string; // YYYY-MM-DD
  line_items: LineItem[];
  tenders: TenderData[];
  notes?: string;
}

export interface TenderData {
  tender_type: 'CASH' | 'CHEQUE' | 'CREDIT_CARD' | 'EFT';
  amount: number;
  cheque_number?: string;
  bank?: string;
}

export interface ReceiptCreateData {
  debtor_account_number: string;
  receipt_type: 'BALANCE_FORWARD' | 'OPEN_ITEM' | 'POST_DATED_CHEQUE';
  receipt_date: string; // YYYY-MM-DD
  tenders: TenderData[];
  amount: number;
  notes?: string;
}

export interface LaybeyCreateData {
  debtor_account_number: string;
  description: string;
  deposit_amount: number;
  line_items: LineItem[];
  notes?: string;
}

export interface QuotationCreateData {
  debtor_account_number: string;
  quote_date: string; // YYYY-MM-DD
  expiry_date: string; // YYYY-MM-DD
  line_items: LineItem[];
  notes?: string;
}

// Type for API responses
export interface TransactionResponse {
  id: string;
  number: string;
  status: string;
  created_at: string;
  [key: string]: any;
}

class POSTransactionAPI {
  private baseUrl: string;
  private tenantSlug: string;
  private authToken: string | null;

  constructor(baseUrl: string = 'http://localhost:8001', tenantSlug: string = '', authToken: string | null = null) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.tenantSlug = tenantSlug;
    this.authToken = authToken;
  }

  /**
   * Update tenant context
   */
  setTenantContext(tenantSlug: string, authToken: string | null = null) {
    this.tenantSlug = tenantSlug;
    if (authToken) {
      this.authToken = authToken;
    }
  }

  /**
   * Get headers with tenant and auth context
   */
  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Tenant-Slug': this.tenantSlug,
    };

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    return headers;
  }

  /**
   * Make HTTP request with error handling
   */
  private async request<T>(
    method: string,
    endpoint: string,
    data?: any
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const options: RequestInit = {
      method,
      headers: this.getHeaders(),
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // ============================================================
  // INVOICE ENDPOINTS
  // ============================================================

  /**
   * Create new invoice
   */
  async createInvoice(data: InvoiceCreateData): Promise<TransactionResponse> {
    return this.request('POST', '/api/v1/invoices/', data);
  }

  /**
   * Get invoice by ID
   */
  async getInvoice(invoiceId: string): Promise<TransactionResponse> {
    return this.request('GET', `/api/v1/invoices/${invoiceId}/`);
  }

  /**
   * List all invoices with optional filters
   */
  async listInvoices(filters?: {
    debtor_account_number?: string;
    status?: string;
    from_date?: string;
    to_date?: string;
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number }> {
    let endpoint = '/api/v1/invoices/';
    if (filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, String(value));
      });
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Update invoice
   */
  async updateInvoice(invoiceId: string, data: Partial<InvoiceCreateData>): Promise<TransactionResponse> {
    return this.request('PUT', `/api/v1/invoices/${invoiceId}/`, data);
  }

  /**
   * Post (finalize) invoice
   */
  async postInvoice(invoiceId: string): Promise<TransactionResponse> {
    return this.request('POST', `/api/v1/invoices/${invoiceId}/post/`);
  }

  /**
   * Delete invoice
   */
  async deleteInvoice(invoiceId: string): Promise<void> {
    await this.request('DELETE', `/api/v1/invoices/${invoiceId}/`);
  }

  // ============================================================
  // CASH SALE ENDPOINTS
  // ============================================================

  /**
   * Create new cash sale
   */
  async createCashSale(data: CashSaleCreateData): Promise<TransactionResponse> {
    return this.request('POST', '/api/v1/cash-sales/', data);
  }

  /**
   * Get cash sale by ID
   */
  async getCashSale(saleId: string): Promise<TransactionResponse> {
    return this.request('GET', `/api/v1/cash-sales/${saleId}/`);
  }

  /**
   * List all cash sales
   */
  async listCashSales(filters?: {
    status?: string;
    from_date?: string;
    to_date?: string;
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number }> {
    let endpoint = '/api/v1/cash-sales/';
    if (filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, String(value));
      });
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Post (finalize) cash sale
   */
  async postCashSale(saleId: string): Promise<TransactionResponse> {
    return this.request('POST', `/api/v1/cash-sales/${saleId}/post/`);
  }

  // ============================================================
  // RECEIPT ENDPOINTS
  // ============================================================

  /**
   * Create new receipt
   */
  async createReceipt(data: ReceiptCreateData): Promise<TransactionResponse> {
    return this.request('POST', '/api/v1/receipts/', data);
  }

  /**
   * Get receipt by ID
   */
  async getReceipt(receiptId: string): Promise<TransactionResponse> {
    return this.request('GET', `/api/v1/receipts/${receiptId}/`);
  }

  /**
   * List all receipts
   */
  async listReceipts(filters?: {
    debtor_account_number?: string;
    from_date?: string;
    to_date?: string;
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number }> {
    let endpoint = '/api/v1/receipts/';
    if (filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, String(value));
      });
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Post (finalize) receipt
   */
  async postReceipt(receiptId: string): Promise<TransactionResponse> {
    return this.request('POST', `/api/v1/receipts/${receiptId}/post/`);
  }

  // ============================================================
  // LAYBYE ENDPOINTS
  // ============================================================

  /**
   * Create new laybye
   */
  async createLaybye(data: LaybeyCreateData): Promise<TransactionResponse> {
    return this.request('POST', '/api/v1/laybyes/', data);
  }

  /**
   * Get laybye by ID
   */
  async getLaybye(laybeyId: string): Promise<TransactionResponse> {
    return this.request('GET', `/api/v1/laybyes/${laybeyId}/`);
  }

  /**
   * List all laybyes
   */
  async listLaybyes(filters?: {
    debtor_account_number?: string;
    status?: string;
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number }> {
    let endpoint = '/api/v1/laybyes/';
    if (filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, String(value));
      });
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  // ============================================================
  // QUOTATION ENDPOINTS
  // ============================================================

  /**
   * Create new quotation
   */
  async createQuotation(data: QuotationCreateData): Promise<TransactionResponse> {
    return this.request('POST', '/api/v1/quotations/', data);
  }

  /**
   * Get quotation by ID
   */
  async getQuotation(quotationId: string): Promise<TransactionResponse> {
    return this.request('GET', `/api/v1/quotations/${quotationId}/`);
  }

  /**
   * List all quotations
   */
  async listQuotations(filters?: {
    debtor_account_number?: string;
    from_date?: string;
    to_date?: string;
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number }> {
    let endpoint = '/api/v1/quotations/';
    if (filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, String(value));
      });
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Convert quotation to invoice
   */
  async convertQuotationToInvoice(quotationId: string): Promise<TransactionResponse> {
    return this.request('POST', `/api/v1/quotations/${quotationId}/convert-to-invoice/`);
  }

  // ============================================================
  // SEARCH ENDPOINTS
  // ============================================================

  /**
   * Search debtors by account number or name
   */
  async searchDebtors(query: string, limit: number = 20): Promise<any> {
    const params = new URLSearchParams({
      query,
      limit: String(limit),
    });
    return this.request('GET', `/api/v1/invoices/search/debtors?${params}`);
  }

  /**
   * Search stock items by code or description
   */
  async searchStock(query: string, limit: number = 20): Promise<any> {
    const params = new URLSearchParams({
      query,
      limit: String(limit),
    });
    return this.request('GET', `/api/v1/invoices/search/stock?${params}`);
  }

  /**
   * Search creditors by account number or name
   */
  async searchCreditors(query: string, limit: number = 20): Promise<any> {
    const params = new URLSearchParams({
      query,
      limit: String(limit),
    });
    return this.request('GET', `/api/v1/invoices/search/creditors?${params}`);
  }

  // ============================================================
  // UTILITY ENDPOINTS
  // ============================================================

  /**
   * Get transaction summary/dashboard
   */
  async getTransactionSummary(filters?: {
    from_date?: string;
    to_date?: string;
  }): Promise<any> {
    let endpoint = '/api/v1/transactions/summary/';
    if (filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, String(value));
      });
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Get health check
   */
  async healthCheck(): Promise<any> {
    return this.request('GET', '/health');
  }
}

// Export singleton with creation hook
let posAPI: POSTransactionAPI | null = null;

export const usePOSAPI = (tenantSlug?: string, authToken?: string | null) => {
  if (!posAPI) {
    const slug = tenantSlug || localStorage.getItem('tenantSlug') || '';
    const token = authToken || localStorage.getItem('authToken');
    posAPI = new POSTransactionAPI(process.env.NEXT_PUBLIC_POS_API_URL, slug, token);
  }

  if (tenantSlug || authToken) {
    posAPI.setTenantContext(tenantSlug || '', authToken || null);
  }

  return posAPI;
};

export default POSTransactionAPI;
