/**
 * POS Transaction API Client
 * 
 * Handles all communication with Django REST Framework POS backend for:
 * - Cash Sales
 * - Receipts on Account
 * - Laybyes
 * - Quotations
 * - Repairs
 * - Job Cards
 * - Cash Control
 * - Credit Notes
 * - Returns
 * - Cheque operations
 * 
 * Base URL: /api/v1/pos/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';

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
  id: string | number;
  number?: string;
  status?: string;
  created_at?: string;
  [key: string]: any;
}

class POSTransactionAPI {
  /**
   * Make HTTP request using shared axios instance with error handling
   */
  private async request<T>(
    method: string,
    endpoint: string,
    data?: any
  ): Promise<T> {
    try {
      console.log(`\n=== POS API REQUEST ===`);
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
      console.error('=== POS API ERROR ===');
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
  // INVOICE ENDPOINTS (from debtors app)
  // ============================================================

  /**
   * Create new invoice
   */
  async createInvoice(data: InvoiceCreateData): Promise<TransactionResponse> {
    return this.request('POST', ENDPOINTS.DEBTORS.TRANSACTIONS, data);
  }

  /**
   * Get invoice by ID
   */
  async getInvoice(invoiceId: string | number): Promise<TransactionResponse> {
    return this.request('GET', `${ENDPOINTS.DEBTORS.TRANSACTIONS}${invoiceId}/`);
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
  }): Promise<{ results: TransactionResponse[]; count: number; next?: string; previous?: string }> {
    let endpoint = ENDPOINTS.DEBTORS.TRANSACTIONS;
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
  async updateInvoice(invoiceId: string | number, data: Partial<InvoiceCreateData>): Promise<TransactionResponse> {
    return this.request('PUT', `${ENDPOINTS.DEBTORS.TRANSACTIONS}${invoiceId}/`, data);
  }

  /**
   * Partially update invoice
   */
  async partialUpdateInvoice(invoiceId: string | number, data: Partial<InvoiceCreateData>): Promise<TransactionResponse> {
    return this.request('PATCH', `${ENDPOINTS.DEBTORS.TRANSACTIONS}${invoiceId}/`, data);
  }

  /**
   * Delete invoice
   */
  async deleteInvoice(invoiceId: string | number): Promise<void> {
    await this.request('DELETE', `${ENDPOINTS.DEBTORS.TRANSACTIONS}${invoiceId}/`);
  }

  // ============================================================
  // CASH SALE ENDPOINTS
  // ============================================================

  /**
   * Create new cash sale
   */
  async createCashSale(data: CashSaleCreateData): Promise<TransactionResponse> {
    return this.request('POST', ENDPOINTS.POS.CASH_SALES, data);
  }

  /**
   * Get cash sale by ID
   */
  async getCashSale(saleId: string | number): Promise<TransactionResponse> {
    return this.request('GET', `${ENDPOINTS.POS.CASH_SALES}${saleId}/`);
  }

  /**
   * List all cash sales
   */
  async listCashSales(filters?: {
    status?: string;
    from_date?: string;
    to_date?: string;
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number; next?: string; previous?: string }> {
    let endpoint = ENDPOINTS.POS.CASH_SALES;
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
   * Update cash sale
   */
  async updateCashSale(saleId: string | number, data: Partial<CashSaleCreateData>): Promise<TransactionResponse> {
    return this.request('PUT', `${ENDPOINTS.POS.CASH_SALES}${saleId}/`, data);
  }

  /**
   * Partially update cash sale
   */
  async partialUpdateCashSale(saleId: string | number, data: Partial<CashSaleCreateData>): Promise<TransactionResponse> {
    return this.request('PATCH', `${ENDPOINTS.POS.CASH_SALES}${saleId}/`, data);
  }

  /**
   * Delete cash sale
   */
  async deleteCashSale(saleId: string | number): Promise<void> {
    await this.request('DELETE', `${ENDPOINTS.POS.CASH_SALES}${saleId}/`);
  }

  // ============================================================
  // RECEIPT ENDPOINTS
  // ============================================================

  /**
   * Create new receipt
   */
  async createReceipt(data: ReceiptCreateData): Promise<TransactionResponse> {
    return this.request('POST', ENDPOINTS.POS.RECEIPTS_ON_ACCOUNT, data);
  }

  /**
   * Get receipt by ID
   */
  async getReceipt(receiptId: string | number): Promise<TransactionResponse> {
    return this.request('GET', `${ENDPOINTS.POS.RECEIPTS_ON_ACCOUNT}${receiptId}/`);
  }

  /**
   * List all receipts
   */
  async listReceipts(filters?: {
    debtor_account_number?: string;
    from_date?: string;
    to_date?: string;
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number; next?: string; previous?: string }> {
    let endpoint = ENDPOINTS.POS.RECEIPTS_ON_ACCOUNT;
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
   * Update receipt
   */
  async updateReceipt(receiptId: string | number, data: Partial<ReceiptCreateData>): Promise<TransactionResponse> {
    return this.request('PUT', `${ENDPOINTS.POS.RECEIPTS_ON_ACCOUNT}${receiptId}/`, data);
  }

  /**
   * Partially update receipt
   */
  async partialUpdateReceipt(receiptId: string | number, data: Partial<ReceiptCreateData>): Promise<TransactionResponse> {
    return this.request('PATCH', `${ENDPOINTS.POS.RECEIPTS_ON_ACCOUNT}${receiptId}/`, data);
  }

  /**
   * Delete receipt
   */
  async deleteReceipt(receiptId: string | number): Promise<void> {
    await this.request('DELETE', `${ENDPOINTS.POS.RECEIPTS_ON_ACCOUNT}${receiptId}/`);
  }

  // ============================================================
  // LAYBYE ENDPOINTS
  // ============================================================

  /**
   * Create new laybye
   */
  async createLaybye(data: LaybeyCreateData): Promise<TransactionResponse> {
    return this.request('POST', ENDPOINTS.POS.LAYBYES, data);
  }

  /**
   * Get laybye by ID
   */
  async getLaybye(laybeyId: string | number): Promise<TransactionResponse> {
    return this.request('GET', `${ENDPOINTS.POS.LAYBYES}${laybeyId}/`);
  }

  /**
   * List all laybyes
   */
  async listLaybyes(filters?: {
    debtor_account_number?: string;
    status?: string;
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number; next?: string; previous?: string }> {
    let endpoint = ENDPOINTS.POS.LAYBYES;
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
   * Update laybye
   */
  async updateLaybye(laybeyId: string | number, data: Partial<LaybeyCreateData>): Promise<TransactionResponse> {
    return this.request('PUT', `${ENDPOINTS.POS.LAYBYES}${laybeyId}/`, data);
  }

  /**
   * Partially update laybye
   */
  async partialUpdateLaybye(laybeyId: string | number, data: Partial<LaybeyCreateData>): Promise<TransactionResponse> {
    return this.request('PATCH', `${ENDPOINTS.POS.LAYBYES}${laybeyId}/`, data);
  }

  /**
   * Delete laybye
   */
  async deleteLaybye(laybeyId: string | number): Promise<void> {
    await this.request('DELETE', `${ENDPOINTS.POS.LAYBYES}${laybeyId}/`);
  }

  // ============================================================
  // QUOTATION ENDPOINTS
  // ============================================================

  /**
   * Create new quotation
   */
  async createQuotation(data: QuotationCreateData): Promise<TransactionResponse> {
    return this.request('POST', ENDPOINTS.POS.QUOTATIONS, data);
  }

  /**
   * Get quotation by ID
   */
  async getQuotation(quotationId: string | number): Promise<TransactionResponse> {
    return this.request('GET', `${ENDPOINTS.POS.QUOTATIONS}${quotationId}/`);
  }

  /**
   * List all quotations
   */
  async listQuotations(filters?: {
    debtor_account_number?: string;
    from_date?: string;
    to_date?: string;
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number; next?: string; previous?: string }> {
    let endpoint = ENDPOINTS.POS.QUOTATIONS;
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
   * Update quotation
   */
  async updateQuotation(quotationId: string | number, data: Partial<QuotationCreateData>): Promise<TransactionResponse> {
    return this.request('PUT', `${ENDPOINTS.POS.QUOTATIONS}${quotationId}/`, data);
  }

  /**
   * Partially update quotation
   */
  async partialUpdateQuotation(quotationId: string | number, data: Partial<QuotationCreateData>): Promise<TransactionResponse> {
    return this.request('PATCH', `${ENDPOINTS.POS.QUOTATIONS}${quotationId}/`, data);
  }

  /**
   * Delete quotation
   */
  async deleteQuotation(quotationId: string | number): Promise<void> {
    await this.request('DELETE', `${ENDPOINTS.POS.QUOTATIONS}${quotationId}/`);
  }

  // ============================================================
  // SEARCH & UTILITY ENDPOINTS (if available)
  // ============================================================

  /**
   * Get transaction summary/dashboard
   */
  async getTransactionSummary(filters?: {
    from_date?: string;
    to_date?: string;
  }): Promise<any> {
    let endpoint = ENDPOINTS.POS.TRANSACTION_QUERIES;
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
}

// Singleton instance
let posAPIInstance: POSTransactionAPI | null = null;

/**
 * Hook to get POS API instance with tenant context
 * Creates singleton on first call
 * 
 * @param tenantSlug - Optional tenant slug to set context
 * @returns POSTransactionAPI instance
 */
export const usePOSAPI = (tenantSlug?: string): POSTransactionAPI => {
  if (!posAPIInstance) {
    posAPIInstance = new POSTransactionAPI();
  }
  return posAPIInstance;
};

// Export singleton instance for backward compatibility
export const posAPI = new POSTransactionAPI();
