/**
 * General Ledger — Transactions (read-only) API Client
 * Base URL: /api/v1/general-ledger/transactions/
 *
 * Direct create() is blocked backend-side — a single GLTran row can never
 * satisfy the "only balanced journals post" rule. Use batches.ts or
 * standingJournals.ts instead.
 */

'use client';

import { api } from '../api';
import { ENDPOINTS } from '../api-config';
import { GLTran, PaginatedResponse } from '../types/generalLedger';

export const glTransactionsApi = {
  list: async (filters?: Record<string, unknown>) => {
    const { data } = await api.get<PaginatedResponse<GLTran>>(
      ENDPOINTS.GENERAL_LEDGER.TRANSACTIONS,
      { params: filters }
    );
    return data;
  },

  get: async (id: string | number) => {
    const { data } = await api.get<GLTran>(
      `${ENDPOINTS.GENERAL_LEDGER.TRANSACTIONS}${id}/`
    );
    return data;
  },

  byBatch: async (batchno: string | number) => {
    const { data } = await api.get(
      `${ENDPOINTS.GENERAL_LEDGER.TRANSACTIONS}by_batch/`,
      { params: { batchno } }
    );
    return data;
  },

  byAccount: async (accno: string | number) => {
    const { data } = await api.get(
      `${ENDPOINTS.GENERAL_LEDGER.TRANSACTIONS}by_account/`,
      { params: { accno } }
    );
    return data;
  },

  byDateRange: async (start_date: string, end_date: string) => {
    const { data } = await api.get(
      `${ENDPOINTS.GENERAL_LEDGER.TRANSACTIONS}by_date_range/`,
      { params: { start_date, end_date } }
    );
    return data;
  },

  batchSummary: async (batchno: string | number) => {
    const { data } = await api.get(
      `${ENDPOINTS.GENERAL_LEDGER.TRANSACTIONS}batch_summary/`,
      { params: { batchno } }
    );
    return data;
  },

  dailySummary: async (date: string) => {
    const { data } = await api.get(
      `${ENDPOINTS.GENERAL_LEDGER.TRANSACTIONS}daily_summary/`,
      { params: { date } }
    );
    return data;
  },
};
