/**
 * Cash Control API Client
 * 
 * Handles all communication with Django backend for:
 * - Cash register opening and closing
 * - Cash floats and balancing
 * - Cash reconciliation
 * - Daily till management
 * 
 * Base URL: /api/v1/pos/cash-control/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';

export interface CashControlOpenData {
  opening_date: string; // YYYY-MM-DD
  opening_time?: string; // HH:MM:SS
  opening_float: number;
  operator_id?: string;
  till_number?: string;
  notes?: string;
}

export interface CashControlCloseData {
  closing_date: string; // YYYY-MM-DD
  closing_time?: string; // HH:MM:SS
  closing_float: number;
  cash_in_till: number;
  over_short?: number;
  notes?: string;
}

export interface CashControl {
  id: string | number;
  opening_date: string;
  closing_date?: string;
  opening_float: number;
  closing_float?: number;
  cash_in_till?: number;
  over_short?: number;
  status: 'OPEN' | 'CLOSED';
  created_at?: string;
  updated_at?: string;
}

export interface CashControlFilters {
  status?: string;
  opening_date_from?: string;
  opening_date_to?: string;
  page?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

export const cashControlApi = {
  /**
   * Get all cash controls with optional filtering
   */
  list: async (filters?: CashControlFilters) => {
    const response = await api.get<PaginatedResponse<CashControl>>(
      ENDPOINTS.POS.CASH_CONTROL,
      { params: filters }
    );
    return response.data;
  },

  /**
   * Get current open cash control
   */
  getCurrent: async () => {
    const response = await api.get<CashControl>(
      `${ENDPOINTS.POS.CASH_CONTROL}current/`
    );
    return response.data;
  },

  /**
   * Get a single cash control by ID
   */
  get: async (id: string | number) => {
    const response = await api.get<CashControl>(`${ENDPOINTS.POS.CASH_CONTROL}${id}/`);
    return response.data;
  },

  /**
   * Open a new cash control
   */
  open: async (data: CashControlOpenData) => {
    const response = await api.post<CashControl>(ENDPOINTS.POS.CASH_CONTROL, data);
    return response.data;
  },

  /**
   * Close an open cash control
   */
  close: async (id: string | number, data: CashControlCloseData) => {
    const response = await api.post(
      `${ENDPOINTS.POS.CASH_CONTROL}${id}/close/`,
      data
    );
    return response.data;
  },

  /**
   * Get cash control summary
   */
  getSummary: async () => {
    const response = await api.get<any>(
      `${ENDPOINTS.POS.CASH_CONTROL}summary/`
    );
    return response.data;
  },

  /**
   * Get today's cash control
   */
  getToday: async () => {
    const response = await api.get<CashControl>(
      `${ENDPOINTS.POS.CASH_CONTROL}today/`
    );
    return response.data;
  },
};

export default cashControlApi;
