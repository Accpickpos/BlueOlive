/**
 * General Ledger — Batch capture / balance-check / post API Client
 * Base URL: /api/v1/general-ledger/batches/
 */

'use client';

import { api } from '../api';
import { ENDPOINTS } from '../api-config';
import {
  GLBatch,
  GLBatchCreateData,
  BatchBalanceCheck,
  BatchPostResult,
  PaginatedResponse,
} from '../types/generalLedger';

export const glBatchesApi = {
  list: async (filters?: Record<string, unknown>) => {
    const { data } = await api.get<PaginatedResponse<GLBatch>>(
      ENDPOINTS.GENERAL_LEDGER.BATCHES,
      { params: filters }
    );
    return data;
  },

  get: async (id: string | number) => {
    const { data } = await api.get<GLBatch>(`${ENDPOINTS.GENERAL_LEDGER.BATCHES}${id}/`);
    return data;
  },

  create: async (body: GLBatchCreateData) => {
    const { data } = await api.post<GLBatch>(ENDPOINTS.GENERAL_LEDGER.BATCHES, body);
    return data;
  },

  update: async (id: string | number, body: Partial<GLBatchCreateData>) => {
    const { data } = await api.patch<GLBatch>(
      `${ENDPOINTS.GENERAL_LEDGER.BATCHES}${id}/`, body
    );
    return data;
  },

  delete: async (id: string | number) => {
    await api.delete(`${ENDPOINTS.GENERAL_LEDGER.BATCHES}${id}/`);
  },

  balanceCheck: async (batchno: string | number) => {
    const { data } = await api.get<BatchBalanceCheck>(
      ENDPOINTS.GENERAL_LEDGER.BATCH_BALANCE_CHECK,
      { params: { batchno } }
    );
    return data;
  },

  post: async (batchno: string | number) => {
    const { data } = await api.post<BatchPostResult>(
      ENDPOINTS.GENERAL_LEDGER.BATCH_POST,
      { batchno }
    );
    return data;
  },
};
