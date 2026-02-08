/**
 * General Ledger API Client
 * 
 * Handles all general ledger management endpoints:
 * - Master accounts
 * - GL transactions
 * - Standing journals
 * - Spread sheets
 * 
 * Base URL: /api/v1/general-ledger/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';

export interface MasterAccount {
  id?: number;
  account_code: string;
  account_name: string;
  account_type: string;
  sub_account_type?: string;
  balance: number;
  is_active: boolean;
  created_at?: string;
  [key: string]: any;
}

export interface GLTransaction {
  id?: number;
  transaction_date: string;
  description: string;
  reference?: string;
  debit_account_id: number;
  credit_account_id: number;
  amount: number;
  created_at?: string;
  [key: string]: any;
}

export interface StandingJournal {
  id?: number;
  name: string;
  description?: string;
  frequency: 'MONTHLY' | 'QUARTERLY' | 'YEARLY';
  next_date: string;
  debit_account_id: number;
  credit_account_id: number;
  amount: number;
  is_active: boolean;
  created_at?: string;
  [key: string]: any;
}

export interface Spreadsheet {
  id?: number;
  name: string;
  description?: string;
  data: any;
  created_at?: string;
  [key: string]: any;
}

export const generalLedgerApi = {
  // ============ MASTER ACCOUNTS ============
  masterAccounts: {
    /**
     * List all master accounts
     */
    list: async (filters?: any) => {
      const response = await api.get<{ results: MasterAccount[] }>(
        ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNTS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single master account
     */
    get: async (id: number | string) => {
      const response = await api.get<MasterAccount>(
        `${ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNTS}${id}/`
      );
      return response.data;
    },

    /**
     * Create new master account
     */
    create: async (data: Partial<MasterAccount>) => {
      const response = await api.post<MasterAccount>(
        ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNTS,
        data
      );
      return response.data;
    },

    /**
     * Update master account
     */
    update: async (id: number | string, data: Partial<MasterAccount>) => {
      const response = await api.patch<MasterAccount>(
        `${ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNTS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete master account
     */
    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNTS}${id}/`);
    },

    /**
     * Get account balance
     */
    getBalance: async (id: number | string) => {
      const response = await api.get(
        `${ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNTS}${id}/balance/`
      );
      return response.data;
    },
  },

  // ============ GL TRANSACTIONS ============
  transactions: {
    /**
     * List all GL transactions
     */
    list: async (filters?: any) => {
      const response = await api.get<{ results: GLTransaction[] }>(
        ENDPOINTS.GENERAL_LEDGER.TRANSACTIONS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single GL transaction
     */
    get: async (id: number | string) => {
      const response = await api.get<GLTransaction>(
        `${ENDPOINTS.GENERAL_LEDGER.TRANSACTIONS}${id}/`
      );
      return response.data;
    },

    /**
     * Create new GL transaction
     */
    create: async (data: Partial<GLTransaction>) => {
      const response = await api.post<GLTransaction>(
        ENDPOINTS.GENERAL_LEDGER.TRANSACTIONS,
        data
      );
      return response.data;
    },

    /**
     * Update GL transaction
     */
    update: async (id: number | string, data: Partial<GLTransaction>) => {
      const response = await api.patch<GLTransaction>(
        `${ENDPOINTS.GENERAL_LEDGER.TRANSACTIONS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete GL transaction
     */
    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.GENERAL_LEDGER.TRANSACTIONS}${id}/`);
    },

    /**
     * Post journal entry
     */
    postJournal: async (data: any) => {
      const response = await api.post(
        `${ENDPOINTS.GENERAL_LEDGER.TRANSACTIONS}post_journal/`,
        data
      );
      return response.data;
    },
  },

  // ============ STANDING JOURNALS ============
  standingJournals: {
    /**
     * List all standing journals
     */
    list: async (filters?: any) => {
      const response = await api.get<{ results: StandingJournal[] }>(
        ENDPOINTS.GENERAL_LEDGER.STANDING_JOURNALS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single standing journal
     */
    get: async (id: number | string) => {
      const response = await api.get<StandingJournal>(
        `${ENDPOINTS.GENERAL_LEDGER.STANDING_JOURNALS}${id}/`
      );
      return response.data;
    },

    /**
     * Create new standing journal
     */
    create: async (data: Partial<StandingJournal>) => {
      const response = await api.post<StandingJournal>(
        ENDPOINTS.GENERAL_LEDGER.STANDING_JOURNALS,
        data
      );
      return response.data;
    },

    /**
     * Update standing journal
     */
    update: async (id: number | string, data: Partial<StandingJournal>) => {
      const response = await api.patch<StandingJournal>(
        `${ENDPOINTS.GENERAL_LEDGER.STANDING_JOURNALS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete standing journal
     */
    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.GENERAL_LEDGER.STANDING_JOURNALS}${id}/`);
    },

    /**
     * Execute standing journal (post due entries)
     */
    execute: async (id: number | string) => {
      const response = await api.post(
        `${ENDPOINTS.GENERAL_LEDGER.STANDING_JOURNALS}${id}/execute/`
      );
      return response.data;
    },
  },

  // ============ SPREAD SHEETS ============
  spreadsheets: {
    /**
     * List all spread sheets
     */
    list: async (filters?: any) => {
      const response = await api.get<{ results: Spreadsheet[] }>(
        ENDPOINTS.GENERAL_LEDGER.SPREAD_SHEETS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single spread sheet
     */
    get: async (id: number | string) => {
      const response = await api.get<Spreadsheet>(
        `${ENDPOINTS.GENERAL_LEDGER.SPREAD_SHEETS}${id}/`
      );
      return response.data;
    },

    /**
     * Create new spread sheet
     */
    create: async (data: Partial<Spreadsheet>) => {
      const response = await api.post<Spreadsheet>(
        ENDPOINTS.GENERAL_LEDGER.SPREAD_SHEETS,
        data
      );
      return response.data;
    },

    /**
     * Update spread sheet
     */
    update: async (id: number | string, data: Partial<Spreadsheet>) => {
      const response = await api.patch<Spreadsheet>(
        `${ENDPOINTS.GENERAL_LEDGER.SPREAD_SHEETS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete spread sheet
     */
    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.GENERAL_LEDGER.SPREAD_SHEETS}${id}/`);
    },
  },

  // ============ TRIAL BALANCE ============
  trialBalance: {
    /**
     * Generate trial balance
     */
    generate: async (asOfDate?: string) => {
      const response = await api.get(
        `${ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNTS}trial_balance/`,
        { params: asOfDate ? { as_of_date: asOfDate } : {} }
      );
      return response.data;
    },
  },
};

export default generalLedgerApi;
