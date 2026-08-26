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

// Matches LaybyeDetailSerializer's writable fields (backend/core/apps/pos).
// `lines`/`payments` are read_only on that serializer — there is currently
// no API endpoint to attach stock line items to a laybye, so creation is
// header-only (total_amount/deposit_amount entered directly).
export interface LaybeyCreateData {
  laybye_number: string;
  customer_name: string;
  telephone?: string;
  laybye_date: string; // YYYY-MM-DD
  expiry_date: string; // YYYY-MM-DD
  total_amount: number;
  deposit_amount: number;
  comment1?: string;
  comment2?: string;
  debtor_account_number?: number;
  sales_area?: number;
}

// Matches QuotationCreateSerializer's writable fields. `lines` requires a
// sequential line_number per item (the backend recomputes it anyway, but
// still validates it as required on input, matching the CreditNote/CashReturn
// nested-create convention).
export interface QuotationLineData {
  line_number: number;
  stock_code?: string;
  description: string;
  quantity: number;
  unit_price: number;
  discount_percentage?: number;
  cost_price?: number;
  tax_code?: number;
}

export interface QuotationCreateData {
  quotation_number: string;
  quotation_date: string; // YYYY-MM-DD
  expiry_date: string; // YYYY-MM-DD
  customer_name: string;
  address_line1?: string;
  address_line2?: string;
  address_line3?: string;
  telephone?: string;
  debtor_account?: number; // Debtor FK id
  sales_area?: number;
  station_number?: number;
  comment1?: string;
  comment2?: string;
  price_level?: 1 | 2 | 3 | 'COST' | 'MARKUP' | 'GP';
  lines: QuotationLineData[];
}

// Matches CreditNoteCreateSerializer's writable fields.
// line_number is required by the backend's CreditNoteLineSerializer (it's
// recomputed sequentially server-side, but is still validated as required
// input - same nested-create convention as CashReturn).
export interface CreditNoteLineData {
  line_number: number;
  stock_code?: string;
  description: string;
  quantity: number;
  unit_price: number;
  tax_code?: number;
}

export interface CreditNoteCreateData {
  credit_number: string;
  credit_date: string; // YYYY-MM-DD
  customer_name?: string;
  debtor_account?: string;
  original_sale_number?: string;
  reason?: string;
  sales_area?: number;
  refund_type?: 'CASH' | 'ACCOUNT' | 'REPLACEMENT';
  cashier?: number;
  station_number?: number;
  lines: CreditNoteLineData[];
}

// Matches the Payout model (fields = '__all__'). `cashier` is optional -
// PayoutViewSet.perform_create falls back to request.user if omitted.
export interface PayoutCreateData {
  payout_date: string; // YYYY-MM-DD
  amount: number;
  payee: string;
  description: string;
  reference?: string;
  cashier?: number;
  station_number?: number;
}

// Matches the Repair model (fields = '__all__'). No server-side auto-numbering
// exists for repair_number - the caller must supply a unique value.
// supplier/repair-cost/selling-price fields are set later via the
// issue_to_supplier / receive_from_supplier actions, not at create time.
export interface RepairCreateData {
  repair_number: string;
  customer_name: string;
  address_line1?: string;
  address_line2?: string;
  telephone?: string;
  contact_person?: string;
  customer_reference?: string;
  order_number?: string;
  date_required: string; // YYYY-MM-DD
  quoted_value?: number;
  repair_details?: string;
  comment1?: string;
  comment2?: string;
  comment3?: string;
  comment4?: string;
  status?: 'C' | 'I' | 'R' | 'V' | 'X';
}

// Matches the CashACheque model (fields = '__all__' minus is_processed/
// created_at/updated_at). `cashier` is NOT auto-assigned server-side, unlike
// most other POS transactions - it must be submitted explicitly.
// `cash_paid` is always recomputed server-side (cheque_amount - commission)
// regardless of what's submitted, so there's no point sending it.
export interface CashAChequeCreateData {
  transaction_number: string;
  transaction_date: string; // YYYY-MM-DD
  drawer_name: string;
  id_number: string;
  telephone?: string;
  address?: string;
  cheque_number: string;
  bank_name: string;
  branch_code?: string;
  account_number?: string;
  cheque_amount: number;
  commission?: number;
  cashier: number;
  station_number?: number;
  notes?: string;
}

// Matches the TransactionQuery model (fields = '__all__' minus created_at/
// updated_at). query_number is NOT auto-generated - the caller must supply it.
export type TransactionQueryType =
  | 'CASH_SALE' | 'INVOICE' | 'RECEIPT' | 'CREDIT_NOTE' | 'LAYBYE'
  | 'QUOTATION' | 'JOB_CARD' | 'REPAIR' | 'PAYOUT';

export interface TransactionQueryCreateData {
  query_number: string;
  query_date: string; // YYYY-MM-DD
  transaction_type: TransactionQueryType;
  transaction_number: string;
  customer_name?: string;
  contact_number?: string;
  query_description: string;
  query_status?: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';
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
  // CREDIT NOTES
  // ============================================================

  /**
   * Create a credit note (header + lines in one request).
   * Matches CreditNoteCreateSerializer on the backend.
   */
  async createCreditNote(data: CreditNoteCreateData): Promise<TransactionResponse> {
    return this.request('POST', ENDPOINTS.POS.CREDIT_NOTES, data);
  }

  /**
   * List all credit notes with optional filters.
   */
  async listCreditNotes(filters?: {
    debtor_account?: string;
    is_posted?: boolean;
    from_date?: string;
    to_date?: string;
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number; next?: string; previous?: string }> {
    let endpoint = ENDPOINTS.POS.CREDIT_NOTES;
    if (filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') params.append(key, String(value));
      });
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Post a credit note - updates stock and the daily cash control totals.
   */
  async postCreditNote(creditNoteId: string | number): Promise<TransactionResponse> {
    return this.request('POST', `${ENDPOINTS.POS.CREDIT_NOTES}${creditNoteId}/post_credit/`);
  }

  // ============================================================
  // PAYOUTS
  // ============================================================

  /**
   * Create a till payout.
   */
  async createPayout(data: PayoutCreateData): Promise<TransactionResponse> {
    return this.request('POST', ENDPOINTS.POS.PAYOUTS, data);
  }

  /**
   * List all payouts with optional filters.
   */
  async listPayouts(filters?: {
    cashier?: string | number;
    station_number?: string | number;
    from_date?: string;
    to_date?: string;
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number; next?: string; previous?: string }> {
    let endpoint = ENDPOINTS.POS.PAYOUTS;
    if (filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') params.append(key, String(value));
      });
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  // ============================================================
  // REPAIR CONTROLS
  // ============================================================

  /**
   * Create a repair voucher.
   */
  async createRepairControl(data: RepairCreateData): Promise<TransactionResponse> {
    return this.request('POST', ENDPOINTS.POS.REPAIRS, data);
  }

  /**
   * List all repair vouchers with optional filters.
   */
  async listRepairControls(filters?: {
    status?: 'C' | 'I' | 'R' | 'V' | 'X';
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number; next?: string; previous?: string }> {
    let endpoint = ENDPOINTS.POS.REPAIRS;
    if (filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) params.append(key, String(value));
      });
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Issue a repair voucher to a supplier.
   */
  async issueRepairToSupplier(repairId: string | number, supplierAccount: string, transportMode?: string): Promise<TransactionResponse> {
    return this.request('POST', `${ENDPOINTS.POS.REPAIRS}${repairId}/issue_to_supplier/`, {
      supplier_account: supplierAccount,
      transport_mode: transportMode,
    });
  }

  /**
   * Receive a repaired item back from the supplier.
   */
  async receiveRepairFromSupplier(repairId: string | number, repairCost: number, supplierInvoice?: string): Promise<TransactionResponse> {
    return this.request('POST', `${ENDPOINTS.POS.REPAIRS}${repairId}/receive_from_supplier/`, {
      repair_cost: repairCost,
      supplier_invoice: supplierInvoice,
    });
  }

  /**
   * Invoice the customer for a completed repair.
   */
  async invoiceRepairCustomer(repairId: string | number): Promise<TransactionResponse> {
    return this.request('POST', `${ENDPOINTS.POS.REPAIRS}${repairId}/invoice_customer/`);
  }

  // ============================================================
  // CASH-A-CHEQUE
  // ============================================================

  /**
   * Record a cash-a-cheque transaction.
   */
  async createCashACheque(data: CashAChequeCreateData): Promise<TransactionResponse> {
    return this.request('POST', ENDPOINTS.POS.CASH_A_CHEQUE, data);
  }

  /**
   * List all cash-a-cheque transactions with optional filters.
   */
  async listCashACheque(filters?: {
    is_processed?: boolean;
    from_date?: string;
    to_date?: string;
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number; next?: string; previous?: string }> {
    let endpoint = ENDPOINTS.POS.CASH_A_CHEQUE;
    if (filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') params.append(key, String(value));
      });
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Mark a cashed cheque as processed (updates the daily cash control totals).
   */
  async processCashACheque(chequeId: string | number): Promise<TransactionResponse> {
    return this.request('POST', `${ENDPOINTS.POS.CASH_A_CHEQUE}${chequeId}/process/`);
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

  /**
   * List transaction queries with optional filters.
   */
  async listTransactionQueries(filters?: {
    query_date?: string;
    transaction_type?: TransactionQueryType;
    query_status?: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';
    assigned_to?: string | number;
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number; next?: string; previous?: string }> {
    let endpoint = ENDPOINTS.POS.TRANSACTION_QUERIES;
    if (filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') params.append(key, String(value));
      });
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Log a new transaction query.
   */
  async createTransactionQuery(data: TransactionQueryCreateData): Promise<TransactionResponse> {
    return this.request('POST', ENDPOINTS.POS.TRANSACTION_QUERIES, data);
  }

  /**
   * Search across transaction types (matches TransactionQueryViewSet.search;
   * only CASH_SALE, LAYBYE and QUOTATION are implemented server-side today).
   */
  async searchTransactionQueries(params: {
    query_type: 'CASH_SALE' | 'LAYBYE' | 'QUOTATION';
    transaction_number?: string;
    customer_name?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<{ query_type: string; results_count: number; results: any[] }> {
    return this.request('POST', `${ENDPOINTS.POS.TRANSACTION_QUERIES}search/`, params);
  }

  /**
   * Mark a transaction query as resolved.
   */
  async resolveTransactionQuery(queryId: string | number, resolutionNotes: string): Promise<TransactionResponse> {
    return this.request('POST', `${ENDPOINTS.POS.TRANSACTION_QUERIES}${queryId}/resolve/`, {
      resolution_notes: resolutionNotes,
    });
  }

  /**
   * Assign a transaction query to a user.
   */
  async assignTransactionQuery(queryId: string | number, assignedTo: number): Promise<TransactionResponse> {
    return this.request('POST', `${ENDPOINTS.POS.TRANSACTION_QUERIES}${queryId}/assign/`, {
      assigned_to: assignedTo,
    });
  }

  // ============================================================
  // CASH RETURNS
  // ============================================================

  /**
   * Create a cash return (refund against a prior sale).
   * Matches CashReturnCreateSerializer on the backend.
   */
  async createCashReturn(data: {
    return_number: string;
    return_date: string;
    original_sale_number: string;
    customer_name?: string;
    reason: string;
    station_number?: number;
    lines: Array<{ line_number: number; stock_code: string; description: string; quantity: number; unit_price: number; tax_code: number }>;
  }): Promise<TransactionResponse> {
    return this.request('POST', ENDPOINTS.POS.CASH_RETURNS, data);
  }

  /**
   * Post a cash return — updates stock and the daily cash control totals.
   */
  async postCashReturn(returnId: string | number): Promise<TransactionResponse> {
    return this.request('POST', `${ENDPOINTS.POS.CASH_RETURNS}${returnId}/post_return/`);
  }

  /**
   * List all cash returns with optional filters.
   */
  async listCashReturns(filters?: {
    is_posted?: boolean;
    from_date?: string;
    to_date?: string;
    page?: number;
  }): Promise<{ results: TransactionResponse[]; count: number; next?: string; previous?: string }> {
    let endpoint = ENDPOINTS.POS.CASH_RETURNS;
    if (filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') params.append(key, String(value));
      });
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  // ============================================================
  // CASH CONTROL
  // ============================================================

  /**
   * Get the daily cash control summary (till reconciliation) for a cashier.
   * Matches CashControlViewSet.daily_summary on the backend.
   */
  async getCashControlDailySummary(filters?: {
    date?: string;
    cashier?: string | number;
    station_number?: string | number;
  }): Promise<any> {
    let endpoint = `${ENDPOINTS.POS.CASH_CONTROL}daily_summary/`;
    if (filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') params.append(key, String(value));
      });
      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }
    }
    return this.request('GET', endpoint);
  }

  /**
   * Get the hourly sales breakdown (transaction count + value per hour) for a
   * given date, per the legacy spec's "Hourly Analysis" cash control facility.
   * Matches CashControlViewSet.hourly_analysis on the backend.
   */
  async getCashControlHourlyAnalysis(filters?: {
    date?: string;
    cashier?: string | number;
    station_number?: string | number;
  }): Promise<{ date: string; hours: Array<{ hour: number; transaction_count: number; total_value: number }> }> {
    let endpoint = `${ENDPOINTS.POS.CASH_CONTROL}hourly_analysis/`;
    if (filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') params.append(key, String(value));
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
