/**
 * Settings — cross-module Utilities reports (Consolidated Expenditure,
 * Data Integrity, Tax Control / VAT-201). Base URL: /api/v1/settings/system-config/
 */

'use client';

import { api } from '../api';
import { ENDPOINTS } from '../api-config';

export interface ConsolidatedExpenditureRow {
  category_id: number;
  category_name: string;
  creditor_amount: string;
  cash_book_amount: string;
  total: string;
}

export interface ConsolidatedExpenditureReport {
  period: string;
  ytd: boolean;
  start_date: string;
  end_date: string;
  rows: ConsolidatedExpenditureRow[];
  grand_total: string;
}

export interface IntegrityDiscrepancy {
  [key: string]: unknown;
  difference: string;
}

export interface IntegrityCheckResult {
  checked: number;
  discrepancy_count: number;
  discrepancies: IntegrityDiscrepancy[];
}

export interface DataIntegrityReport {
  debtors?: IntegrityCheckResult;
  creditors?: IntegrityCheckResult;
  stock?: IntegrityCheckResult;
}

export interface TaxControlCategory {
  label: string;
  amount: string;
}

export interface TaxControlReport {
  start_date: string;
  end_date: string;
  categories: TaxControlCategory[];
  totals: {
    output_vat: string;
    input_vat: string;
    net_vat_payable: string;
  };
  reconciliation: {
    debtors_module_output_vat: string;
    creditors_module_input_vat: string;
    cash_book_module_input_vat: string;
    cash_book_module_output_vat: string;
  };
  assumptions: string;
}

export const settingsReportsApi = {
  consolidatedExpenditure: async (period: string, ytd: boolean) => {
    const { data } = await api.get<ConsolidatedExpenditureReport>(
      ENDPOINTS.SETTINGS.CONSOLIDATED_EXPENDITURE,
      { params: { period, ytd } }
    );
    return data;
  },

  dataIntegrityReport: async (checks?: string[]) => {
    const { data } = await api.get<DataIntegrityReport>(ENDPOINTS.SETTINGS.DATA_INTEGRITY_REPORT, {
      params: checks ? { checks: checks.join(',') } : undefined,
    });
    return data;
  },

  taxControlReport: async (startDate: string, endDate: string) => {
    const { data } = await api.get<TaxControlReport>(ENDPOINTS.SETTINGS.TAX_CONTROL_REPORT, {
      params: { start_date: startDate, end_date: endDate },
    });
    return data;
  },
};
