/**
 * Repairs/Job Repairs API Client
 * 
 * Handles all communication with Django backend for:
 * - Repair control and tracking
 * - Service records
 * - Repair quotes and invoicing
 * - Warranty and service history
 * 
 * Base URL: /api/v1/pos/repairs/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';

export interface RepairLineItem {
  item_code: string;
  description: string;
  quantity: number;
  unit_price: number;
  discount_percentage?: number;
  tax_code: 'ZERO' | 'STANDARD' | 'REDUCED';
}

export interface RepairCreateData {
  debtor_account_number?: string;
  repair_date: string; // YYYY-MM-DD
  status: 'RECEIVED' | 'IN_PROGRESS' | 'COMPLETED' | 'INVOICED' | 'COLLECTED';
  description: string;
  item_description: string;
  serial_number?: string;
  warranty_status?: 'IN_WARRANTY' | 'OUT_OF_WARRANTY';
  estimated_completion?: string; // YYYY-MM-DD
  line_items?: RepairLineItem[];
  notes?: string;
}

export interface RepairUpdateData {
  status?: string;
  estimated_completion?: string;
  description?: string;
  line_items?: RepairLineItem[];
  notes?: string;
}

export interface Repair {
  id: string | number;
  repair_number?: string;
  debtor_account_number?: string;
  repair_date: string;
  status: string;
  description: string;
  item_description: string;
  serial_number?: string;
  warranty_status?: string;
  estimated_completion?: string;
  total_amount?: number;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RepairFilters {
  status?: string;
  warrant_status?: string;
  repair_date_from?: string;
  repair_date_to?: string;
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

export const repairsApi = {
  /**
   * Get all repairs with optional filtering
   */
  list: async (filters?: RepairFilters) => {
    const response = await api.get<PaginatedResponse<Repair>>(
      ENDPOINTS.POS.REPAIRS,
      { params: filters }
    );
    return response.data;
  },

  /**
   * Get a single repair by ID
   */
  get: async (id: string | number) => {
    const response = await api.get<Repair>(`${ENDPOINTS.POS.REPAIRS}${id}/`);
    return response.data;
  },

  /**
   * Create a new repair
   */
  create: async (data: RepairCreateData) => {
    const response = await api.post<Repair>(ENDPOINTS.POS.REPAIRS, data);
    return response.data;
  },

  /**
   * Update a repair
   */
  update: async (id: string | number, data: RepairUpdateData) => {
    const response = await api.patch<Repair>(
      `${ENDPOINTS.POS.REPAIRS}${id}/`,
      data
    );
    return response.data;
  },

  /**
   * Delete a repair
   */
  delete: async (id: string | number) => {
    await api.delete(`${ENDPOINTS.POS.REPAIRS}${id}/`);
  },

  /**
   * Begin repair (change status to IN_PROGRESS)
   */
  begin: async (id: string | number) => {
    const response = await api.post(
      `${ENDPOINTS.POS.REPAIRS}${id}/begin/`,
      {}
    );
    return response.data;
  },

  /**
   * Complete repair
   */
  complete: async (id: string | number) => {
    const response = await api.post(
      `${ENDPOINTS.POS.REPAIRS}${id}/complete/`,
      {}
    );
    return response.data;
  },

  /**
   * Mark as collected
   */
  collect: async (id: string | number) => {
    const response = await api.post(
      `${ENDPOINTS.POS.REPAIRS}${id}/collect/`,
      {}
    );
    return response.data;
  },

  /**
   * Get repairs by customer/debtor
   */
  getByDebtor: async (debtorAccountNumber: string) => {
    const response = await api.get<PaginatedResponse<Repair>>(
      ENDPOINTS.POS.REPAIRS,
      { params: { debtor_account_number: debtorAccountNumber } }
    );
    return response.data;
  },

  /**
   * Get active repairs (in progress)
   */
  getActive: async () => {
    const response = await api.get<PaginatedResponse<Repair>>(
      ENDPOINTS.POS.REPAIRS,
      { params: { status: 'IN_PROGRESS' } }
    );
    return response.data;
  },

  /**
   * Get completed repairs awaiting collection
   */
  getReadyForCollection: async () => {
    const response = await api.get<PaginatedResponse<Repair>>(
      ENDPOINTS.POS.REPAIRS,
      { params: { status: 'COMPLETED' } }
    );
    return response.data;
  },

  /**
   * Get repairs summary
   */
  getSummary: async () => {
    const response = await api.get<any>(
      `${ENDPOINTS.POS.REPAIRS}summary/`
    );
    return response.data;
  },

  /**
   * Search repairs
   */
  search: async (searchTerm: string) => {
    const response = await api.get<PaginatedResponse<Repair>>(
      ENDPOINTS.POS.REPAIRS,
      { params: { search: searchTerm } }
    );
    return response.data;
  },

  /**
   * Add line items to a repair
   */
  addLineItems: async (id: string | number, items: RepairLineItem[]) => {
    const response = await api.post(
      `${ENDPOINTS.POS.REPAIRS}${id}/line-items/`,
      items
    );
    return response.data;
  },

  /**
   * Get overdue repairs
   */
  getOverdue: async () => {
    const response = await api.get<PaginatedResponse<Repair>>(
      `${ENDPOINTS.POS.REPAIRS}overdue/`
    );
    return response.data;
  },
};

export default repairsApi;
