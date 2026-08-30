/**
 * General Ledger — Reports API Client (Trial Balance, Income Statement, Balance Sheet)
 * Base URL: /api/v1/general-ledger/reports/
 */

'use client';

import { api } from '../api';
import { ENDPOINTS } from '../api-config';
import {
  TrialBalanceResponse,
  IncomeStatementResponse,
  BalanceSheetResponse,
} from '../types/generalLedger';

export const glReportsApi = {
  trialBalance: async (as_of_period?: number) => {
    const { data } = await api.get<TrialBalanceResponse>(
      ENDPOINTS.GENERAL_LEDGER.TRIAL_BALANCE,
      { params: as_of_period ? { as_of_period } : {} }
    );
    return data;
  },

  incomeStatement: async (as_of_period?: number) => {
    const { data } = await api.get<IncomeStatementResponse>(
      ENDPOINTS.GENERAL_LEDGER.INCOME_STATEMENT,
      { params: as_of_period ? { as_of_period } : {} }
    );
    return data;
  },

  balanceSheet: async (as_of_period?: number) => {
    const { data } = await api.get<BalanceSheetResponse>(
      ENDPOINTS.GENERAL_LEDGER.BALANCE_SHEET,
      { params: as_of_period ? { as_of_period } : {} }
    );
    return data;
  },
};
