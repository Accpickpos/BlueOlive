/**
 * General Ledger — Parameters (singleton), System Status, Period/Year End
 * Base URL: /api/v1/general-ledger/parameters/
 */

'use client';

import { api } from '../api';
import { ENDPOINTS } from '../api-config';
import {
  GLParam,
  SystemStatus,
  PeriodEndResult,
  YearEndResult,
} from '../types/generalLedger';

export const glParametersApi = {
  get: async () => {
    const { data } = await api.get<GLParam>(ENDPOINTS.GENERAL_LEDGER.PARAMETERS_CURRENT);
    return data;
  },

  update: async (body: Partial<Pick<GLParam, 'retained_earnings_accno'>>) => {
    const { data } = await api.patch<GLParam>(
      ENDPOINTS.GENERAL_LEDGER.PARAMETERS_CURRENT, body
    );
    return data;
  },

  systemStatus: async () => {
    const { data } = await api.get<SystemStatus>(ENDPOINTS.GENERAL_LEDGER.SYSTEM_STATUS);
    return data;
  },

  periodEnd: async () => {
    const { data } = await api.post<PeriodEndResult>(ENDPOINTS.GENERAL_LEDGER.PERIOD_END);
    return data;
  },

  yearEnd: async () => {
    const { data } = await api.post<YearEndResult>(ENDPOINTS.GENERAL_LEDGER.YEAR_END);
    return data;
  },
};
