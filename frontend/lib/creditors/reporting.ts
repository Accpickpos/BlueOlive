/**
 * Creditors Reporting API Client
 * Handles all reporting and analytics endpoints for creditors.
 *
 * Base URL: /api/v1/creditors/
 */

'use client';

import { useCallback, useMemo } from 'react';
import { api } from '../api';
import { ENDPOINTS } from '../api-config';
import settingsApi from '../settingsApi';
import { creditorsMasterApi } from './master';
import {
  PaginatedResponse,
  SupplierLedgerEntry,
  ExpenseCategoryMonthlyBalance,
  ExpenseCategoryTransaction,
  SupplierPaymentOrder,
  SupplierPaymentOrderCreateData,
  ExpenseCategory,
  ExpenseCategoryCreateData,
  ExpenseCategoryFilters,
  OutstandingBalance,
  OutstandingBalanceCaptureData,
  CreditorFilters,
} from '../types/creditors';

export type { ExpenseCategory, ExpenseCategoryCreateData, OutstandingBalance, OutstandingBalanceCaptureData };

// ============================================================================
// Reporting API client
// ============================================================================
export const creditorsReportingApi = {

  // ── SUPPLIER LEDGER (read-only) ───────────────────────────────────────────
  ledger: {
    list: async (filters?: { creditor?: number; transaction_type?: string; search?: string; ordering?: string; page?: number; page_size?: number }) => {
      const { data } = await api.get<PaginatedResponse<SupplierLedgerEntry>>(
        ENDPOINTS.CREDITORS.LEDGER, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<SupplierLedgerEntry>(
        `${ENDPOINTS.CREDITORS.LEDGER}${id}/`
      );
      return data;
    },
  },

  // ── EXPENSE MONTHLY BALANCES (read-only) ──────────────────────────────────
  expenseMonthly: {
    list: async (filters?: { expense_category?: number; year?: number }) => {
      const { data } = await api.get<PaginatedResponse<ExpenseCategoryMonthlyBalance>>(
        ENDPOINTS.CREDITORS.EXPENSE_MONTHLY, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<ExpenseCategoryMonthlyBalance>(
        `${ENDPOINTS.CREDITORS.EXPENSE_MONTHLY}${id}/`
      );
      return data;
    },
  },

  // ── EXPENSE TRANSACTIONS (read-only) ──────────────────────────────────────
  expenseTransactions: {
    list: async (filters?: { expense_category?: number; creditor?: number; source_type?: string; page?: number }) => {
      const { data } = await api.get<PaginatedResponse<ExpenseCategoryTransaction>>(
        ENDPOINTS.CREDITORS.EXPENSE_TRANSACTIONS, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<ExpenseCategoryTransaction>(
        `${ENDPOINTS.CREDITORS.EXPENSE_TRANSACTIONS}${id}/`
      );
      return data;
    },

    byCreditor: async (creditorId: string | number) => {
      const { data } = await api.get<ExpenseCategoryTransaction[]>(
        ENDPOINTS.CREDITORS.EXPENSE_BY_CREDITOR, { params: { creditor: creditorId } }
      );
      return data;
    },

    byCategory: async (categoryId: string | number) => {
      const { data } = await api.get<ExpenseCategoryTransaction[]>(
        ENDPOINTS.CREDITORS.EXPENSE_BY_CATEGORY, { params: { category: categoryId } }
      );
      return data;
    },
  },

  // ── SUPPLIER PAYMENT ORDERS ───────────────────────────────────────────────
  paymentOrders: {
    list: async (filters?: { creditor?: number; is_processed?: boolean }) => {
      const { data } = await api.get<PaginatedResponse<SupplierPaymentOrder>>(
        ENDPOINTS.CREDITORS.PAYMENT_ORDERS, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<SupplierPaymentOrder>(
        `${ENDPOINTS.CREDITORS.PAYMENT_ORDERS}${id}/`
      );
      return data;
    },

    create: async (body: SupplierPaymentOrderCreateData) => {
      const { data } = await api.post<SupplierPaymentOrder>(
        ENDPOINTS.CREDITORS.PAYMENT_ORDERS, body
      );
      return data;
    },

    update: async (id: string | number, body: Partial<SupplierPaymentOrderCreateData>) => {
      const { data } = await api.patch<SupplierPaymentOrder>(
        `${ENDPOINTS.CREDITORS.PAYMENT_ORDERS}${id}/`, body
      );
      return data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.PAYMENT_ORDERS}${id}/`);
    },

    pending: async () => {
      const { data } = await api.get<SupplierPaymentOrder[]>(
        ENDPOINTS.CREDITORS.PAYMENT_ORDERS_PENDING
      );
      return data;
    },

    process: async (id: string | number) => {
      const { data } = await api.post<SupplierPaymentOrder>(
        ENDPOINTS.CREDITORS.PROCESS_PAYMENT_ORDER(id)
      );
      return data;
    },
  },

  // ── EXPENSE CATEGORIES ─────────────────────────────────────────────────────
  expenseCategories: {
    list: async (filters?: ExpenseCategoryFilters) => {
      const data = await settingsApi.expenseCategories.list(filters);
      return data;
    },
    create: async (body: ExpenseCategoryCreateData) => {
      const { data } = await settingsApi.expenseCategories.create(body);
      return data;
    },
    update: async (id: string | number, body: ExpenseCategoryCreateData) => {
      const { data } = await settingsApi.expenseCategories.update(id, body);
      return data;
    },
    delete: async (id: string | number) => {
      await settingsApi.expenseCategories.delete(id);
    },
  },

  // ── OUTSTANDING BALANCE ────────────────────────────────────────────────────
  outstandingBalances: {
    list: async () => {
      const { data } = await api.get(ENDPOINTS.CREDITORS.OUTSTANDING_BALANCES);
      return data;
    },
    get: async (id: string | number) => {
      const { data } = await api.get(`${ENDPOINTS.CREDITORS.OUTSTANDING_BALANCES}${id}/`);
      return data;
    },
    create: async (body: OutstandingBalanceCaptureData) => {
      const { data } = await api.post(ENDPOINTS.CREDITORS.OUTSTANDING_BALANCES, body);
      return data;
    },
    update: async (id: string | number, body: OutstandingBalanceCaptureData) => {
      const { data } = await api.patch(`${ENDPOINTS.CREDITORS.OUTSTANDING_BALANCES}${id}/`, body);
      return data;
    },
    delete: async (id: string | number) => {
      const { data } = await api.delete(`${ENDPOINTS.CREDITORS.OUTSTANDING_BALANCES}${id}/`);
      return data;
    },
    capture: async (body: OutstandingBalanceCaptureData) => {
      const { data } = await api.post(ENDPOINTS.CREDITORS.OUTSTANDING_BALANCE_CAPTURE, body);
      return data;
    },
  },

};

// ============================================================================
// useCreditorsAPI hook - composes all API modules
// ============================================================================
export function useCreditorsAPI() {
  const listSuppliers = useCallback((f?: CreditorFilters) => creditorsMasterApi.accounts.list(f), []);
  const getSupplier = useCallback((id: string | number) => creditorsMasterApi.accounts.get(id), []);
  const createSupplier = useCallback((d: any) => creditorsMasterApi.accounts.create(d), []);
  const updateSupplier = useCallback((id: string | number, d: any) => creditorsMasterApi.accounts.update(id, d), []);
  const deleteSupplier = useCallback((id: string | number) => creditorsMasterApi.accounts.delete(id), []);
  const getAgeAnalysis = useCallback(() => creditorsMasterApi.accounts.ageAnalysis(), []);
  const getAgedBalances = useCallback((id: string | number) => creditorsMasterApi.accounts.agedBalances(id), []);
  const recalculateAged = useCallback((id: string | number) => creditorsMasterApi.accounts.recalculateAged(id), []);

  const listCreditTerms = useCallback(async (): Promise<any[]> => {
    try {
      const { data } = await api.get(
        ENDPOINTS.SETTINGS.CREDIT_TERMS
      );
      return data.results || [];
    } catch {
      return [];
    }
  }, []);

  const listExpenseCategories = useCallback(
    (f?: ExpenseCategoryFilters) =>
      settingsApi.expenseCategories.list(f),
    []
  );
  const createExpenseCategory = useCallback(
    (d: ExpenseCategoryCreateData) => settingsApi.expenseCategories.create(d), []
  );
  const updateExpenseCategory = useCallback(
    (id: number | string, d: Partial<ExpenseCategoryCreateData>) =>
      settingsApi.expenseCategories.update(id, d),
    []
  );
  const deleteExpenseCategory = useCallback(
    (id: number | string) => settingsApi.expenseCategories.delete(id), []
  );

  const listOutstandingBalances = useCallback(
    () => creditorsReportingApi.outstandingBalances.list(),
    []
  );
  const updateOutstandingBalance = useCallback(
    (id: number | string, d: OutstandingBalanceCaptureData) => creditorsReportingApi.outstandingBalances.update(id, d),
    []
  );
  const deleteOutstandingBalance = useCallback(
    (id: number | string) => creditorsReportingApi.outstandingBalances.delete(id), []
  );
  const captureOutstandingBalance = useCallback(
    (d: OutstandingBalanceCaptureData) => creditorsReportingApi.outstandingBalances.capture(d),
    []
  );

  return useMemo(() => ({
    listSuppliers, getSupplier, createSupplier, updateSupplier, deleteSupplier,
    getAgeAnalysis, getAgedBalances, recalculateAged,
    listCreditTerms,
    listExpenseCategories, createExpenseCategory, updateExpenseCategory, deleteExpenseCategory,
    listOutstandingBalances, updateOutstandingBalance, deleteOutstandingBalance, captureOutstandingBalance,
  }), [listSuppliers, getSupplier, createSupplier, updateSupplier, deleteSupplier, getAgeAnalysis, getAgedBalances, recalculateAged, listCreditTerms, listExpenseCategories, createExpenseCategory, updateExpenseCategory, deleteExpenseCategory, listOutstandingBalances, updateOutstandingBalance, deleteOutstandingBalance, captureOutstandingBalance]);
}
