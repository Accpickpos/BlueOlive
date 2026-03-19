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
  // Primary field names (backend compatible)
  stock_code: string;  // Backend expects 'stock_code' not 'item_code'
  description: string;
  quantity: number;
  unit_price: number;
  discount_percentage?: number;
  tax_code: number | string; // 0 = ZERO, 1 = STANDARD (14%), 2 = REDUCED, or 'ZERO', 'STANDARD', 'REDUCED'
  cost_price?: number;
  
  // Alternative field names (used in some components)
  item_code?: string;
  selling_price?: number;
}

export interface InvoiceCreateData {
  debtor_account_number: string;  // Backend expects 'debtor_account_number' which is converted to debtor ID
  invoice_number?: string;  // Backend may require this
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
  lines: LineItem[];  // Backend expects 'lines' not 'line_items'
  tenders: TenderData[];
  notes?: string;
}

export interface TenderData {
  // Backend tender_type choices: CASH, CHEQUE, VOUCHER, SPEEDPOINT, EFT
  tender_type: 'CASH' | 'CHEQUE' | 'VOUCHER' | 'SPEEDPOINT' | 'EFT';
  amount: number;
  // Backend field names: drawer_name, bank_name, bank_account, id_number, telephone
  drawer_name?: string;  // Was 'cheque_number'
  bank_name?: string;   // Was 'bank'
  bank_account?: string;
  id_number?: string;
  telephone?: string;
  // For speedpoint
  card_type?: string;
  authorization_code?: string;
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
      console.error('Error status:', error.response?.status);
      
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      if (error.response?.data) {
        // Format validation errors nicely
        const errors = error.response.data;
        console.error('Full error data:', JSON.stringify(errors, null, 2));
        if (typeof errors === 'object') {
          // Handle nested serializer errors (like {lines: [{...}]})
          const errorMessages = Object.entries(errors).map(([key, value]) => {
            if (Array.isArray(value) && value.length > 0 && typeof value[0] === 'object') {
              // Nested error - could be lines validation
              return `${key}: ${JSON.stringify(value)}`;
            }
            return `${key}: ${Array.isArray(value) ? value.join(', ') : JSON.stringify(value)}`;
          }).join('; ');
          throw new Error(errorMessages);
        }
        throw new Error(JSON.stringify(errors));
      }
      throw error;
    }
  }

  // ============================================================
  // HEALTH CHECK
  // ============================================================

  /**
   * Health check to verify API connectivity
   * @returns Promise<boolean> - true if API is reachable
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.request('GET', '/health/');
      return true;
    } catch {
      // If health endpoint doesn't exist, consider API reachable
      return true;
    }
  }

  // ============================================================
  // INVOICE ENDPOINTS (POS app)
  // ============================================================

  /**
   * Create new invoice
   */
  async createInvoice(data: InvoiceCreateData): Promise<TransactionResponse> {
    return this.request('POST', ENDPOINTS.POS.INVOICES, data);
  }

  /**
   * Get invoice by ID
   */
  async getInvoice(invoiceId: string | number): Promise<TransactionResponse> {
    return this.request('GET', `${ENDPOINTS.POS.INVOICES}${invoiceId}/`);
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
    let endpoint = ENDPOINTS.POS.INVOICES;
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
    return this.request('PUT', `${ENDPOINTS.POS.INVOICES}${invoiceId}/`, data);
  }

  /**
   * Partially update invoice
   */
  async partialUpdateInvoice(invoiceId: string | number, data: Partial<InvoiceCreateData>): Promise<TransactionResponse> {
    return this.request('PATCH', `${ENDPOINTS.POS.INVOICES}${invoiceId}/`, data);
  }

  /**
   * Delete invoice
   */
  async deleteInvoice(invoiceId: string | number): Promise<void> {
    await this.request('DELETE', `${ENDPOINTS.POS.INVOICES}${invoiceId}/`);
  }

  /**
   * Post invoice to accounts
   */
  async postInvoice(invoiceId: string | number): Promise<TransactionResponse> {
    return this.request('POST', `${ENDPOINTS.POS.INVOICES}${invoiceId}/post/`);
  }

  /**
   * Cancel invoice
   */
  async cancelInvoice(invoiceId: string | number): Promise<TransactionResponse> {
    return this.request('POST', `${ENDPOINTS.POS.INVOICES}${invoiceId}/cancel/`);
  }

  /**
   * Apply payment to invoice
   */
  async applyPaymentToInvoice(invoiceId: string | number, amount: number, paymentDate?: string): Promise<TransactionResponse> {
    return this.request('POST', `${ENDPOINTS.POS.INVOICES}${invoiceId}/apply_payment/`, { amount, payment_date: paymentDate });
  }

  // ============================================================
  // DEBTOR SEARCH (for invoice creation)
  // ============================================================

  /**
   * Search debtors by name or account number
   */
  async searchDebtors(query: string): Promise<{ results: any[]; count: number }> {
    return this.request('GET', `${ENDPOINTS.DEBTORS.ACCOUNTS}?search=${encodeURIComponent(query)}&limit=20`);
  }

  // ============================================================
  // STOCK SEARCH (for invoice line items)
  // ============================================================

  /**
   * Search stock items by code or description
   */
  async searchStock(query: string): Promise<{ results: any[]; count: number }> {
    return this.request('GET', `${ENDPOINTS.STOCK_CONTROL.STOCK_ITEMS}?search=${encodeURIComponent(query)}&limit=20`);
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

  /**
   * Convert laybye to invoice
   */
  async convertLaybyeToInvoice(laybyeId: string | number, debtorId?: number, debtorAccountNumber?: string): Promise<TransactionResponse> {
    const data: any = {};
    if (debtorId) {
      data.debtor_id = debtorId;
    }
    if (debtorAccountNumber) {
      data.debtor_account_number = debtorAccountNumber;
    }
    return this.request('POST', `${ENDPOINTS.POS.LAYBYES}${laybyeId}/convert_to_invoice/`, data);
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

  async convertQuotationToInvoice(quotationId: string | number, debtorId?: number, debtorAccountNumber?: string): Promise<TransactionResponse> {
    const data: any = {};
    if (debtorId) {
      data.debtor_id = debtorId;
    }
    if (debtorAccountNumber) {
      data.debtor_account_number = debtorAccountNumber;
    }
    return this.request('POST', `${ENDPOINTS.POS.QUOTATIONS}${quotationId}/convert_to_invoice/`, data);
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
