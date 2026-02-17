/**
 * Credit Notes API Client
 * 
 * Handles all communication with Django backend for:
 * - Credit note creation (goods returned, pricing adjustments)
 * - Credit note management and tracking
 * - Credit note reversal/deletion
 * - Credit note line item management
 * 
 * Base URL: /api/v1/pos/credit-notes/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';

export interface CreditNoteLineItem {
  item_code: string;
  description: string;
  quantity: number;
  unit_price: number;
  discount_percentage?: number;
  tax_code: 'ZERO' | 'STANDARD' | 'REDUCED';
  reason: string; // e.g., "GOODS_RETURNED", "PRICE_ADJUSTMENT", "DAMAGED", "OVERPAID"
}

export interface CreditNoteCreateData {
  debtor_account_number: string;
  credit_note_date: string; // YYYY-MM-DD
  invoice_number?: string; // Reference to original invoice
  reference_number?: string; // PO or other reference
  reason: 'GOODS_RETURNED' | 'PRICE_ADJUSTMENT' | 'DAMAGED' | 'OVERPAID' | 'OTHER';
  line_items: CreditNoteLineItem[];
  notes?: string;
}

export interface CreditNoteUpdateData {
  reference_number?: string;
  reason?: string;
  notes?: string;
  line_items?: CreditNoteLineItem[];
}

export interface CreditNote {
  id: string | number;
  credit_note_number?: string;
  debtor_account_number: string;
  credit_note_date: string;
  invoice_number?: string;
  reference_number?: string;
  reason: string;
  total_amount?: number;
  status?: 'DRAFT' | 'POSTED' | 'REVERSED';
  notes?: string;
  created_at?: string;
  updated_at?: string;
  created_by?: string;
}

export interface CreditNoteFilters {
  debtor_account_number?: string;
  status?: string;
  reason?: string;
  credit_note_date_from?: string;
  credit_note_date_to?: string;
  search?: string;
  page?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

export const creditNotesApi = {
  /**
   * Get all credit notes with optional filtering
   */
  list: async (filters?: CreditNoteFilters) => {
    const response = await api.get<PaginatedResponse<CreditNote>>(
      ENDPOINTS.POS.CREDIT_NOTES,
      { params: filters }
    );
    return response.data;
  },

  /**
   * Get a single credit note by ID
   */
  get: async (id: string | number) => {
    const response = await api.get<CreditNote>(`${ENDPOINTS.POS.CREDIT_NOTES}${id}/`);
    return response.data;
  },

  /**
   * Create a new credit note
   */
  create: async (data: CreditNoteCreateData) => {
    const response = await api.post<CreditNote>(ENDPOINTS.POS.CREDIT_NOTES, data);
    return response.data;
  },

  /**
   * Update an existing credit note
   */
  update: async (id: string | number, data: CreditNoteUpdateData) => {
    const response = await api.patch<CreditNote>(
      `${ENDPOINTS.POS.CREDIT_NOTES}${id}/`,
      data
    );
    return response.data;
  },

  /**
   * Delete a credit note (only if in DRAFT status)
   */
  delete: async (id: string | number) => {
    await api.delete(`${ENDPOINTS.POS.CREDIT_NOTES}${id}/`);
  },

  /**
   * Post a credit note (move from DRAFT to POSTED)
   */
  post: async (id: string | number) => {
    const response = await api.post(
      `${ENDPOINTS.POS.CREDIT_NOTES}${id}/post/`,
      {}
    );
    return response.data;
  },

  /**
   * Reverse a credit note
   */
  reverse: async (id: string | number, reason?: string) => {
    const response = await api.post(
      `${ENDPOINTS.POS.CREDIT_NOTES}${id}/reverse/`,
      { reason }
    );
    return response.data;
  },

  /**
   * Get credit notes by debtor account
   */
  getByDebtor: async (debtorAccountNumber: string) => {
    const response = await api.get<PaginatedResponse<CreditNote>>(
      ENDPOINTS.POS.CREDIT_NOTES,
      { params: { debtor_account_number: debtorAccountNumber } }
    );
    return response.data;
  },

  /**
   * Get credit notes by status
   */
  getByStatus: async (status: 'DRAFT' | 'POSTED' | 'REVERSED') => {
    const response = await api.get<PaginatedResponse<CreditNote>>(
      ENDPOINTS.POS.CREDIT_NOTES,
      { params: { status } }
    );
    return response.data;
  },

  /**
   * Get credit notes by reason
   */
  getByReason: async (reason: string) => {
    const response = await api.get<PaginatedResponse<CreditNote>>(
      ENDPOINTS.POS.CREDIT_NOTES,
      { params: { reason } }
    );
    return response.data;
  },

  /**
   * Add line items to a credit note
   */
  addLineItems: async (id: string | number, items: CreditNoteLineItem[]) => {
    const response = await api.post(
      `${ENDPOINTS.POS.CREDIT_NOTES}${id}/line-items/`,
      items
    );
    return response.data;
  },

  /**
   * Get credit notes summary/statistics
   */
  getSummary: async () => {
    const response = await api.get<any>(
      `${ENDPOINTS.POS.CREDIT_NOTES}summary/`
    );
    return response.data;
  },

  /**
   * Search credit notes
   */
  search: async (searchTerm: string) => {
    const response = await api.get<PaginatedResponse<CreditNote>>(
      ENDPOINTS.POS.CREDIT_NOTES,
      { params: { search: searchTerm } }
    );
    return response.data;
  },

  /**
   * Get draft credit notes
   */
  getDrafts: async () => {
    const response = await api.get<PaginatedResponse<CreditNote>>(
      ENDPOINTS.POS.CREDIT_NOTES,
      { params: { status: 'DRAFT' } }
    );
    return response.data;
  },

  /**
   * Get posted credit notes
   */
  getPosted: async () => {
    const response = await api.get<PaginatedResponse<CreditNote>>(
      ENDPOINTS.POS.CREDIT_NOTES,
      { params: { status: 'POSTED' } }
    );
    return response.data;
  },

  /**
   * Bulk post credit notes
   */
  bulkPost: async (ids: (string | number)[]) => {
    const response = await api.post(
      `${ENDPOINTS.POS.CREDIT_NOTES}bulk-post/`,
      { ids }
    );
    return response.data;
  },

  /**
   * Get credits available for a debtor
   */
  getCreditsForDebtor: async (debtorAccountNumber: string) => {
    const response = await api.get<any>(
      `${ENDPOINTS.POS.CREDIT_NOTES}debtor-credits/`,
      { params: { debtor_account_number: debtorAccountNumber } }
    );
    return response.data;
  },
};

export default creditNotesApi;
