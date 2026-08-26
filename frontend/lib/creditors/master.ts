/**
 * Creditors Master Data API Client
 * Handles all creditor account management endpoints.
 *
 * Base URL: /api/v1/creditors/
 */

'use client';

import { api } from '../api';
import { ENDPOINTS } from '../api-config';
import {
  CreditorAccount,
  CreditorCreateData,
  CreditorEditData,
  CreditorFilters,
  PaginatedResponse,
  AgedBalanceSummary,
  CreditorOpenItem,
  SupplierLedgerEntry,
} from '../types/creditors';

// ============================================================================
// Extended Supplier type (extra fields used by supplier forms)
// ============================================================================
export interface Supplier extends CreditorAccount {
  short_name?: string;
  vat_number?: string;
}

export interface SupplierCreateData extends CreditorCreateData {
  short_name?: string;
  vat_number?: string;
}

export interface CreditTermsOption {
  id:    number;
  name:  string;
  days?: number;
}

// ============================================================================
// Master Data API client
// ============================================================================
export const creditorsMasterApi = {

  // ── CREDITOR ACCOUNTS ─────────────────────────────────────────────────────
  accounts: {
    list: async (filters?: CreditorFilters) => {
      const { data } = await api.get<PaginatedResponse<CreditorAccount>>(
        ENDPOINTS.CREDITORS.ACCOUNTS, { params: filters }
      );
      return data;
    },

    /**
     * Thin typeahead lookup for creditor/supplier pickers — hits
     * CreditorViewSet.lookup (LookupActionMixin), returns a flat array (no
     * pagination envelope) of CreditorListSerializer rows.
     */
    lookup: async (query: string, limit = 20): Promise<CreditorAccount[]> => {
      const { data } = await api.get<CreditorAccount[]>(
        `${ENDPOINTS.CREDITORS.ACCOUNTS}lookup/`,
        { params: { search: query, limit } }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<CreditorAccount>(
        `${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`
      );
      return data;
    },

    create: async (body: CreditorCreateData) => {
      const { data } = await api.post<CreditorAccount>(
        ENDPOINTS.CREDITORS.ACCOUNTS, body
      );
      return data;
    },

    update: async (id: string | number, body: CreditorEditData) => {
      const { data } = await api.patch<CreditorAccount>(
        `${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`, body
      );
      return data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`);
    },

    // Actions
    agedBalances: async (id: string | number) => {
      const { data } = await api.get<AgedBalanceSummary>(
        ENDPOINTS.CREDITORS.AGED_BALANCES(id)
      );
      return data;
    },

    recalculateAged: async (id: string | number) => {
      const { data } = await api.post<AgedBalanceSummary>(
        ENDPOINTS.CREDITORS.RECALCULATE_AGED(id)
      );
      return data;
    },

    creditorOpenItems: async (id: string | number) => {
      const { data } = await api.get<CreditorOpenItem[]>(
        ENDPOINTS.CREDITORS.CREDITOR_OPEN_ITEMS(id)
      );
      return data;
    },

    creditorLedger: async (id: string | number) => {
      const { data } = await api.get<SupplierLedgerEntry[]>(
        ENDPOINTS.CREDITORS.CREDITOR_LEDGER(id)
      );
      return data;
    },

    transactionSummary: async (id: string | number) => {
      const { data } = await api.get(
        ENDPOINTS.CREDITORS.CREDITOR_TRANSACTIONS(id)
      );
      return data;
    },

    ageAnalysis: async () => {
      const { data } = await api.get<AgedBalanceSummary[]>(
        ENDPOINTS.CREDITORS.AGE_ANALYSIS
      );
      return data;
    },
  },

  // ── CREDITOR SUMMARY ────────────────────────────────────────────────────────
  summary: {
    get: async () => {
      const { data } = await api.get(
        ENDPOINTS.CREDITORS.SUMMARY
      );
      return data;
    },
    
    // Get age analysis for all creditors (for summary page)
    ageAnalysis: async (params?: { order_by?: string; include_zero_balance?: boolean }) => {
      const { data } = await api.get<AgedBalanceSummary[]>(
        ENDPOINTS.CREDITORS.AGE_ANALYSIS, { params }
      );
      return data;
    },
    
    // Get control totals (calculated from age analysis)
    controlTotals: async () => {
      const ageData = await creditorsMasterApi.summary.ageAnalysis({ include_zero_balance: false });
      
      // Calculate totals from the age analysis data
      const totals = ageData.reduce(
        (acc, creditor) => ({
          current: acc.current + creditor.balance_current,
          '30_days': acc['30_days'] + creditor.balance_30_days,
          '60_days': acc['60_days'] + creditor.balance_60_days,
          '90_days': acc['90_days'] + creditor.balance_90_days,
          '120_days': acc['120_days'] + creditor.balance_120_days,
          '150_days': acc['150_days'] + creditor.balance_150_days,
          '180_days': acc['180_days'] + creditor.balance_180_days,
          total: acc.total + creditor.total_outstanding_balance,
        }),
        {
          current: 0,
          '30_days': 0,
          '60_days': 0,
          '90_days': 0,
          '120_days': 0,
          '150_days': 0,
          '180_days': 0,
          total: 0,
        }
      );
      
      const activeCreditors = ageData.filter(c => c.total_outstanding_balance > 0).length;
      
      return {
        control_totals: totals,
        statistics: {
          active_suppliers: activeCreditors,
          total_suppliers: ageData.length,
        },
      };
    },
  },

};


