/**
 * Job Cards API Client
 * 
 * Handles all communication with Django backend for:
 * - Job card creation and management
 * - Service/repair tracking
 * - Labor and parts tracking
 * - Job card status updates
 * 
 * Base URL: /api/v1/pos/job-cards/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';

export interface JobCardLineItem {
  item_code: string;
  description: string;
  quantity: number;
  unit_price: number;
  discount_percentage?: number;
  tax_code: 'ZERO' | 'STANDARD' | 'REDUCED';
}

export interface JobCardCreateData {
  debtor_account_number?: string;  // Make optional - can be empty for manual entry
  customer_name: string;
  job_number?: string;
  job_date: string; // YYYY-MM-DD
  description: string;
  status: 'OPEN' | 'ACTIVE' | 'INVOICED' | 'CANCELLED';
  labor_hours?: number;
  line_items?: JobCardLineItem[];
  notes?: string;
  reg_make_names?: string;
  vin_number?: string;
  mileage?: number;
}

export interface JobCardUpdateData {
  description?: string;
  status?: 'OPEN' | 'IN_PROGRESS' | 'COMPLETED' | 'INVOICED';
  labor_hours?: number;
  notes?: string;
  line_items?: JobCardLineItem[];
}

export interface JobCard {
  id: string | number;
  job_number?: string;
  debtor_account_number: string;
  job_date: string;
  description: string;
  status: string;
  customer_name?: string;
  registration_number?: string;
  telephone?: string;
  subtotal?: number;
  total_amount?: number;
  vat_amount?: number;
  lines?: any[];
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface JobCardFilters {
  status?: string;
  debtor_account_number?: string;
  job_date_from?: string;
  job_date_to?: string;
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

export const jobCardsApi = {
  /**
   * Get all job cards with optional filtering
   */
  list: async (filters?: JobCardFilters) => {
    const response = await api.get<PaginatedResponse<JobCard>>(
      ENDPOINTS.POS.JOB_CARDS,
      { params: filters }
    );
    return response.data;
  },

  /**
   * Get a single job card by ID
   */
  get: async (id: string | number) => {
    const response = await api.get<JobCard>(`${ENDPOINTS.POS.JOB_CARDS}${id}/`);
    return response.data;
  },

  /**
   * Create a new job card
   */
  create: async (data: JobCardCreateData) => {
    const response = await api.post<JobCard>(ENDPOINTS.POS.JOB_CARDS, data);
    return response.data;
  },

  /**
   * Update an existing job card
   */
  update: async (id: string | number, data: JobCardUpdateData) => {
    const response = await api.patch<JobCard>(
      `${ENDPOINTS.POS.JOB_CARDS}${id}/`,
      data
    );
    return response.data;
  },

  /**
   * Delete a job card
   */
  delete: async (id: string | number) => {
    await api.delete(`${ENDPOINTS.POS.JOB_CARDS}${id}/`);
  },

  /**
   * Get job cards by debtor account
   */
  getByDebtor: async (debtorAccountNumber: string) => {
    const response = await api.get<PaginatedResponse<JobCard>>(
      ENDPOINTS.POS.JOB_CARDS,
      { params: { debtor_account_number: debtorAccountNumber } }
    );
    return response.data;
  },

  /**
   * Get job cards by status
   */
  getByStatus: async (status: 'OPEN' | 'IN_PROGRESS' | 'COMPLETED' | 'INVOICED') => {
    const response = await api.get<PaginatedResponse<JobCard>>(
      ENDPOINTS.POS.JOB_CARDS,
      { params: { status } }
    );
    return response.data;
  },

  /**
   * Add line items to a job card
   */
  addLineItems: async (id: string | number, items: JobCardLineItem[]) => {
    const response = await api.post(
      `${ENDPOINTS.POS.JOB_CARDS}${id}/line-items/`,
      items
    );
    return response.data;
  },

  /**
   * Update job card status
   */
  updateStatus: async (id: string | number, status: string) => {
    const response = await api.patch<JobCard>(
      `${ENDPOINTS.POS.JOB_CARDS}${id}/`,
      { status }
    );
    return response.data;
  },

  /**
   * Convert job card to invoice
   */
  convertToInvoice: async (id: string | number, debtorId?: number, debtorAccountNumber?: string) => {
    // If debtorAccountNumber is provided, send it instead of debtorId
    const payload = debtorAccountNumber 
      ? { debtor_account_number: debtorAccountNumber }
      : { debtor_id: debtorId };
    
    const response = await api.post(
      `${ENDPOINTS.POS.JOB_CARDS}${id}/convert_to_invoice/`,
      payload
    );
    return response.data;
  },

  /**
   * Get job cards summary/statistics
   */
  getSummary: async () => {
    const response = await api.get<any>(
      `${ENDPOINTS.POS.JOB_CARDS}summary/`
    );
    return response.data;
  },

  /**
   * Search job cards
   */
  search: async (searchTerm: string) => {
    const response = await api.get<PaginatedResponse<JobCard>>(
      ENDPOINTS.POS.JOB_CARDS,
      { params: { search: searchTerm } }
    );
    return response.data;
  },

  /**
   * Close/Complete a job card
   */
  complete: async (id: string | number) => {
    const response = await api.post(
      `${ENDPOINTS.POS.JOB_CARDS}${id}/complete/`,
      {}
    );
    return response.data;
  },

  /**
   * Get job cards due for invoicing
   */
  getDueForInvoicing: async () => {
    const response = await api.get<PaginatedResponse<JobCard>>(
      ENDPOINTS.POS.JOB_CARDS,
      { params: { status: 'COMPLETED' } }
    );
    return response.data;
  },

  /**
   * Bulk update job card statuses
   */
  bulkUpdateStatus: async (ids: (string | number)[], status: string) => {
    const response = await api.post(
      `${ENDPOINTS.POS.JOB_CARDS}bulk-update/`,
      { ids, status }
    );
    return response.data;
  },
};

export default jobCardsApi;
