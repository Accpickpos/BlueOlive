/**
 * Cheque Cashing API Client
 * 
 * Handles all communication with Django backend for:
 * - Cheque cashing transactions
 * - Cheque processing
 * - Cheque banking records
 * - Cheque status tracking
 * 
 * Base URL: /api/v1/pos/cash-a-cheque/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';

export interface ChequeCreateData {
  cheque_date: string; // YYYY-MM-DD
  bank: string;
  branch: string;
  account_number: string;
  cheque_number: string;
  cheque_amount: number;
  drawer_name: string;
  drawer_account?: string;
  id_number?: string;
  phone_number?: string;
  received_date?: string; // YYYY-MM-DD
  notes?: string;
}

export interface ChequeUpdateData {
  status?: 'RECEIVED' | 'DEPOSITED' | 'CLEARED' | 'REJECTED' | 'CANCELLED';
  bank?: string;
  branch?: string;
  notes?: string;
}

export interface Cheque {
  id: string | number;
  cheque_number: string;
  cheque_date: string;
  bank: string;
  branch: string;
  account_number: string;
  cheque_amount: number;
  drawer_name: string;
  status?: 'RECEIVED' | 'DEPOSITED' | 'CLEARED' | 'REJECTED' | 'CANCELLED';
  received_date?: string;
  deposited_date?: string;
  cleared_date?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ChequeFilters {
  status?: string;
  bank?: string;
  branch?: string;
  cheque_date_from?: string;
  cheque_date_to?: string;
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

export const chequeApi = {
  /**
   * Get all cheques with optional filtering
   */
  list: async (filters?: ChequeFilters) => {
    const response = await api.get<PaginatedResponse<Cheque>>(
      ENDPOINTS.POS.CASH_A_CHEQUE,
      { params: filters }
    );
    return response.data;
  },

  /**
   * Get a single cheque by ID
   */
  get: async (id: string | number) => {
    const response = await api.get<Cheque>(`${ENDPOINTS.POS.CASH_A_CHEQUE}${id}/`);
    return response.data;
  },

  /**
   * Create a new cheque record
   */
  create: async (data: ChequeCreateData) => {
    const response = await api.post<Cheque>(ENDPOINTS.POS.CASH_A_CHEQUE, data);
    return response.data;
  },

  /**
   * Update a cheque record
   */
  update: async (id: string | number, data: ChequeUpdateData) => {
    const response = await api.patch<Cheque>(
      `${ENDPOINTS.POS.CASH_A_CHEQUE}${id}/`,
      data
    );
    return response.data;
  },

  /**
   * Delete a cheque record
   */
  delete: async (id: string | number) => {
    await api.delete(`${ENDPOINTS.POS.CASH_A_CHEQUE}${id}/`);
  },

  /**
   * Deposit cheques
   */
  deposit: async (ids: (string | number)[]) => {
    const response = await api.post(
      `${ENDPOINTS.POS.CASH_A_CHEQUE}deposit/`,
      { ids }
    );
    return response.data;
  },

  /**
   * Mark cheques as cleared
   */
  markCleared: async (ids: (string | number)[]) => {
    const response = await api.post(
      `${ENDPOINTS.POS.CASH_A_CHEQUE}mark-cleared/`,
      { ids }
    );
    return response.data;
  },

  /**
   * Reject a cheque
   */
  reject: async (id: string | number, reason?: string) => {
    const response = await api.post(
      `${ENDPOINTS.POS.CASH_A_CHEQUE}${id}/reject/`,
      { reason }
    );
    return response.data;
  },

  /**
   * Get pending/uncleared cheques
   */
  getPending: async () => {
    const response = await api.get<PaginatedResponse<Cheque>>(
      ENDPOINTS.POS.CASH_A_CHEQUE,
      { params: { status: 'RECEIVED' } }
    );
    return response.data;
  },

  /**
   * Get cheques by bank
   */
  getByBank: async (bank: string) => {
    const response = await api.get<PaginatedResponse<Cheque>>(
      ENDPOINTS.POS.CASH_A_CHEQUE,
      { params: { bank } }
    );
    return response.data;
  },

  /**
   * Get cheques summary
   */
  getSummary: async () => {
    const response = await api.get<any>(
      `${ENDPOINTS.POS.CASH_A_CHEQUE}summary/`
    );
    return response.data;
  },

  /**
   * Search cheques
   */
  search: async (searchTerm: string) => {
    const response = await api.get<PaginatedResponse<Cheque>>(
      ENDPOINTS.POS.CASH_A_CHEQUE,
      { params: { search: searchTerm } }
    );
    return response.data;
  },

  /**
   * Validate cheque number uniqueness
   */
  validateChequeNumber: async (chequeNumber: string) => {
    const response = await api.get<{ valid: boolean }>(
      `${ENDPOINTS.POS.CASH_A_CHEQUE}validate/`,
      { params: { cheque_number: chequeNumber } }
    );
    return response.data;
  },
};

export default chequeApi;
