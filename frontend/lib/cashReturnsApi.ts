/**
 * Cash Returns API Client
 * 
 * Handles all communication with Django backend for:
 * - Cash return transactions (goods returned for cash refund)
 * - Return tracking and authorization
 * - Return status management
 * 
 * Base URL: /api/v1/pos/cash-returns/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';

export interface CashReturnLineItem {
  item_code: string;
  description: string;
  quantity: number;
  unit_price: number;
  discount_percentage?: number;
  reason: string; // e.g., "DAMAGED", "WRONG_ITEM", "CUSTOMER_RETURN", "OVERSTOCKED"
}

export interface CashReturnCreateData {
  return_date: string; // YYYY-MM-DD
  original_transaction_number?: string;
  line_items: CashReturnLineItem[];
  refund_amount: number;
  refund_method: 'CASH' | 'CHEQUE' | 'CREDIT_CARD' | 'EFT';
  notes?: string;
  authorization_code?: string;
}

export interface CashReturnUpdateData {
  status?: 'DRAFT' | 'APPROVED' | 'COMPLETED' | 'REJECTED';
  authorization_code?: string;
  notes?: string;
  line_items?: CashReturnLineItem[];
}

export interface CashReturn {
  id: string | number;
  return_number?: string;
  return_date: string;
  original_transaction_number?: string;
  refund_amount: number;
  refund_method: string;
  status?: 'DRAFT' | 'APPROVED' | 'COMPLETED' | 'REJECTED';
  authorization_code?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
  created_by?: string;
}

export interface CashReturnFilters {
  status?: string;
  refund_method?: string;
  return_date_from?: string;
  return_date_to?: string;
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

export const cashReturnsApi = {
  /**
   * Get all cash returns with optional filtering
   */
  list: async (filters?: CashReturnFilters) => {
    const response = await api.get<PaginatedResponse<CashReturn>>(
      ENDPOINTS.POS.CASH_RETURNS,
      { params: filters }
    );
    return response.data;
  },

  /**
   * Get a single cash return by ID
   */
  get: async (id: string | number) => {
    const response = await api.get<CashReturn>(`${ENDPOINTS.POS.CASH_RETURNS}${id}/`);
    return response.data;
  },

  /**
   * Create a new cash return
   */
  create: async (data: CashReturnCreateData) => {
    const response = await api.post<CashReturn>(ENDPOINTS.POS.CASH_RETURNS, data);
    return response.data;
  },

  /**
   * Update a cash return
   */
  update: async (id: string | number, data: CashReturnUpdateData) => {
    const response = await api.patch<CashReturn>(
      `${ENDPOINTS.POS.CASH_RETURNS}${id}/`,
      data
    );
    return response.data;
  },

  /**
   * Delete a cash return (only if in DRAFT status)
   */
  delete: async (id: string | number) => {
    await api.delete(`${ENDPOINTS.POS.CASH_RETURNS}${id}/`);
  },

  /**
   * Approve a cash return
   */
  approve: async (id: string | number, authorizationCode?: string) => {
    const response = await api.post(
      `${ENDPOINTS.POS.CASH_RETURNS}${id}/approve/`,
      { authorization_code: authorizationCode }
    );
    return response.data;
  },

  /**
   * Complete a cash return
   */
  complete: async (id: string | number) => {
    const response = await api.post(
      `${ENDPOINTS.POS.CASH_RETURNS}${id}/complete/`,
      {}
    );
    return response.data;
  },

  /**
   * Reject a cash return
   */
  reject: async (id: string | number, reason?: string) => {
    const response = await api.post(
      `${ENDPOINTS.POS.CASH_RETURNS}${id}/reject/`,
      { reason }
    );
    return response.data;
  },

  /**
   * Get pending cash returns
   */
  getPending: async () => {
    const response = await api.get<PaginatedResponse<CashReturn>>(
      ENDPOINTS.POS.CASH_RETURNS,
      { params: { status: 'DRAFT' } }
    );
    return response.data;
  },

  /**
   * Get cash returns summary
   */
  getSummary: async () => {
    const response = await api.get<any>(
      `${ENDPOINTS.POS.CASH_RETURNS}summary/`
    );
    return response.data;
  },

  /**
   * Search cash returns
   */
  search: async (searchTerm: string) => {
    const response = await api.get<PaginatedResponse<CashReturn>>(
      ENDPOINTS.POS.CASH_RETURNS,
      { params: { search: searchTerm } }
    );
    return response.data;
  },
};

export default cashReturnsApi;
