/**
 * General Ledger — Master Accounts (Chart of Accounts) API Client
 * Base URL: /api/v1/general-ledger/master-accounts/
 */

'use client';

import { api } from '../api';
import { ENDPOINTS } from '../api-config';
import {
  GLMast,
  GLMastListItem,
  GLMastCreateData,
  PaginatedResponse,
} from '../types/generalLedger';

export const glMasterApi = {
  list: async (filters?: Record<string, unknown>) => {
    const { data } = await api.get<PaginatedResponse<GLMastListItem>>(
      ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNTS,
      { params: filters }
    );
    return data;
  },

  get: async (id: string | number) => {
    const { data } = await api.get<GLMast>(
      `${ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNTS}${id}/`
    );
    return data;
  },

  create: async (body: GLMastCreateData) => {
    const { data } = await api.post<GLMast>(
      ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNTS, body
    );
    return data;
  },

  update: async (id: string | number, body: Partial<GLMastCreateData>) => {
    const { data } = await api.patch<GLMast>(
      `${ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNTS}${id}/`, body
    );
    return data;
  },

  delete: async (id: string | number) => {
    await api.delete(`${ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNTS}${id}/`);
  },

  accountHistory: async (id: string | number) => {
    const { data } = await api.get(ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNT_HISTORY(id));
    return data;
  },

  summary: async () => {
    const { data } = await api.get(ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNTS_SUMMARY);
    return data;
  },

  balanceSummary: async () => {
    const { data } = await api.get(ENDPOINTS.GENERAL_LEDGER.MASTER_ACCOUNTS_BALANCE_SUMMARY);
    return data;
  },
};
