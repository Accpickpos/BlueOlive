/**
 * General Ledger — Standing Journals API Client
 * Base URL: /api/v1/general-ledger/standing-journals/
 */

'use client';

import { api } from '../api';
import { ENDPOINTS } from '../api-config';
import {
  GLStJnl,
  GLStJnlCreateData,
  JournalBalanceCheck,
  PostDueResult,
  PaginatedResponse,
} from '../types/generalLedger';

export const glStandingJournalsApi = {
  list: async (filters?: Record<string, unknown>) => {
    const { data } = await api.get<PaginatedResponse<GLStJnl>>(
      ENDPOINTS.GENERAL_LEDGER.STANDING_JOURNALS,
      { params: filters }
    );
    return data;
  },

  get: async (id: string | number) => {
    const { data } = await api.get<GLStJnl>(
      `${ENDPOINTS.GENERAL_LEDGER.STANDING_JOURNALS}${id}/`
    );
    return data;
  },

  create: async (body: GLStJnlCreateData) => {
    const { data } = await api.post<GLStJnl>(
      ENDPOINTS.GENERAL_LEDGER.STANDING_JOURNALS, body
    );
    return data;
  },

  update: async (id: string | number, body: Partial<GLStJnlCreateData>) => {
    const { data } = await api.patch<GLStJnl>(
      `${ENDPOINTS.GENERAL_LEDGER.STANDING_JOURNALS}${id}/`, body
    );
    return data;
  },

  delete: async (id: string | number) => {
    await api.delete(`${ENDPOINTS.GENERAL_LEDGER.STANDING_JOURNALS}${id}/`);
  },

  validateBalance: async (journalno: string | number) => {
    const { data } = await api.get<JournalBalanceCheck>(
      ENDPOINTS.GENERAL_LEDGER.STANDING_JOURNAL_VALIDATE,
      { params: { journalno } }
    );
    return data;
  },

  postDue: async () => {
    const { data } = await api.post<PostDueResult>(
      ENDPOINTS.GENERAL_LEDGER.STANDING_JOURNAL_POST_DUE
    );
    return data;
  },

  activeJournals: async () => {
    const { data } = await api.get(ENDPOINTS.GENERAL_LEDGER.STANDING_JOURNAL_ACTIVE);
    return data;
  },
};
