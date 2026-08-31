/**
 * General Ledger — Report Format (GLRep) Maintenance API Client
 * Base URL: /api/v1/general-ledger/report-formats/
 *
 * Maintenance CRUD only — defines the layout rows Income Statement/Balance
 * Sheet reports are computed from. See reports.ts for the actual reports.
 */

'use client';

import { api } from '../api';
import { ENDPOINTS } from '../api-config';
import { GLRep, GLRepCreateData, PaginatedResponse } from '../types/generalLedger';

export const glReportFormatsApi = {
  list: async (filters?: Record<string, unknown>) => {
    const { data } = await api.get<PaginatedResponse<GLRep>>(
      ENDPOINTS.GENERAL_LEDGER.REPORT_FORMATS,
      { params: filters }
    );
    return data;
  },

  get: async (id: string | number) => {
    const { data } = await api.get<GLRep>(
      `${ENDPOINTS.GENERAL_LEDGER.REPORT_FORMATS}${id}/`
    );
    return data;
  },

  create: async (body: GLRepCreateData) => {
    const { data } = await api.post<GLRep>(ENDPOINTS.GENERAL_LEDGER.REPORT_FORMATS, body);
    return data;
  },

  update: async (id: string | number, body: Partial<GLRepCreateData>) => {
    const { data } = await api.patch<GLRep>(
      `${ENDPOINTS.GENERAL_LEDGER.REPORT_FORMATS}${id}/`, body
    );
    return data;
  },

  delete: async (id: string | number) => {
    await api.delete(`${ENDPOINTS.GENERAL_LEDGER.REPORT_FORMATS}${id}/`);
  },
};
