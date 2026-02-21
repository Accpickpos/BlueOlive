/**
 * Creditors API Client
 * RESTful API wrapper for all creditor management endpoints.
 *
 * Base URL: /api/v1/creditors/
 * All endpoint keys reference ENDPOINTS.CREDITORS.* from api-config.ts.
 */

'use client';

import { useCallback } from 'react';
import { api } from './api';
import { ENDPOINTS } from './api-config';
import settingsApi from './settingsApi';
import {
  CreditorAccount,
  CreditorCreateData,
  CreditorEditData,
  CreditorFilters,
  CreditorsSummary,
  PaginatedResponse,
  AgedBalanceSummary,
  GoodsReceivedNote,
  GoodsReceivedNoteCreateData,
  GRNLineItem,
  CreditorInvoice,
  CreditorInvoiceCreateData,
  InvoiceLineItem,
  CreditorCreditNote,
  CreditorCreditNoteCreateData,
  CreditNoteLineItem,
  CreditorPayment,
  CreditorPaymentCreateData,
  PaymentAllocation,
  CreditorJournal,
  CreditorJournalCreateData,
  SupplierLedgerEntry,
  CreditorOpenItem,
  OpenItemAllocation,
  OpenItemAudit,
  RFC,
  RFCCreateData,
  RFCStatus,
  RFCLineItem,
  ExpenseCategoryMonthlyBalance,
  ExpenseCategoryTransaction,
  SupplierPaymentOrder,
  SupplierPaymentOrderCreateData,
  TransactionFilters,
  ExpenseCategory,
  ExpenseCategoryCreateData,
  ExpenseCategoryFilters,
} from './types/creditors';

export type { ExpenseCategory, ExpenseCategoryCreateData };

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
// API client object
// ============================================================================
export const creditorsApi = {

  // ── CREDITOR MASTER ───────────────────────────────────────────────────────
  accounts: {
    list: async (filters?: CreditorFilters) => {
      const { data } = await api.get<PaginatedResponse<CreditorAccount>>(
        ENDPOINTS.CREDITORS.ACCOUNTS, { params: filters }
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
      const { data } = await api.get<CreditorsSummary>(
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
      const ageData = await creditorsApi.summary.ageAnalysis({ include_zero_balance: false });
      
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

  // ── CREDITOR TRANSACTIONS ───────────────────────────────────────────────────
  transactions: {
    list: async (filters?: TransactionFilters) => {
      const { data } = await api.get<PaginatedResponse<SupplierLedgerEntry>>(
        ENDPOINTS.CREDITORS.TRANSACTIONS, { params: filters }
      );
      return data;
    },
    
    get: async (id: string | number) => {
      const { data } = await api.get<SupplierLedgerEntry>(
        `${ENDPOINTS.CREDITORS.TRANSACTIONS}${id}/`
      );
      return data;
    },
    
    // Get transactions for a specific creditor
    byCreditor: async (creditorId: string | number) => {
      const { data } = await api.get<SupplierLedgerEntry[]>(
        ENDPOINTS.CREDITORS.CREDITOR_TRANSACTIONS(creditorId)
      );
      return data;
    },
  },

  // ── GOODS RECEIVED NOTES ──────────────────────────────────────────────────
  grns: {
    list: async (filters?: TransactionFilters) => {
      const { data } = await api.get<PaginatedResponse<GoodsReceivedNote>>(
        ENDPOINTS.CREDITORS.GRNS, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<GoodsReceivedNote>(
        `${ENDPOINTS.CREDITORS.GRNS}${id}/`
      );
      return data;
    },

    create: async (body: GoodsReceivedNoteCreateData) => {
      const { data } = await api.post<GoodsReceivedNote>(
        ENDPOINTS.CREDITORS.GRNS, body
      );
      return data;
    },

    update: async (id: string | number, body: Partial<GoodsReceivedNoteCreateData>) => {
      const { data } = await api.patch<GoodsReceivedNote>(
        `${ENDPOINTS.CREDITORS.GRNS}${id}/`, body
      );
      return data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.GRNS}${id}/`);
    },

    post: async (id: string | number) => {
      const { data } = await api.post<GoodsReceivedNote>(
        ENDPOINTS.CREDITORS.POST_GRN(id)
      );
      return data;
    },

    byCreditor: async (creditorId: string | number, filters?: TransactionFilters) => {
      const { data } = await api.get<GoodsReceivedNote[]>(
        ENDPOINTS.CREDITORS.GRNS_BY_CREDITOR,
        { params: { creditor: creditorId, ...filters } }
      );
      return data;
    },

    lines: {
      list: async (grnId: string | number) => {
        const { data } = await api.get<GRNLineItem[]>(
          ENDPOINTS.CREDITORS.GRN_LINES(grnId)
        );
        return data;
      },
      create: async (grnId: string | number, body: GRNLineItem) => {
        const { data } = await api.post<GRNLineItem>(
          ENDPOINTS.CREDITORS.GRN_LINES(grnId), body
        );
        return data;
      },
      update: async (grnId: string | number, lineId: string | number, body: Partial<GRNLineItem>) => {
        const { data } = await api.patch<GRNLineItem>(
          `${ENDPOINTS.CREDITORS.GRN_LINES(grnId)}${lineId}/`, body
        );
        return data;
      },
      delete: async (grnId: string | number, lineId: string | number) => {
        await api.delete(`${ENDPOINTS.CREDITORS.GRN_LINES(grnId)}${lineId}/`);
      },
    },
  },

  // ── CREDITOR INVOICES (expense) ───────────────────────────────────────────
  invoices: {
    list: async (filters?: TransactionFilters) => {
      const { data } = await api.get<PaginatedResponse<CreditorInvoice>>(
        ENDPOINTS.CREDITORS.INVOICES, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<CreditorInvoice>(
        `${ENDPOINTS.CREDITORS.INVOICES}${id}/`
      );
      return data;
    },

    create: async (body: CreditorInvoiceCreateData) => {
      const { data } = await api.post<CreditorInvoice>(
        ENDPOINTS.CREDITORS.INVOICES, body
      );
      return data;
    },

    update: async (id: string | number, body: Partial<CreditorInvoiceCreateData>) => {
      const { data } = await api.patch<CreditorInvoice>(
        `${ENDPOINTS.CREDITORS.INVOICES}${id}/`, body
      );
      return data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.INVOICES}${id}/`);
    },

    post: async (id: string | number) => {
      const { data } = await api.post<CreditorInvoice>(
        ENDPOINTS.CREDITORS.POST_INVOICE(id)
      );
      return data;
    },

    lines: {
      list: async (invoiceId: string | number) => {
        const { data } = await api.get<InvoiceLineItem[]>(
          ENDPOINTS.CREDITORS.INVOICE_LINES(invoiceId)
        );
        return data;
      },
      create: async (invoiceId: string | number, body: InvoiceLineItem) => {
        const { data } = await api.post<InvoiceLineItem>(
          ENDPOINTS.CREDITORS.INVOICE_LINES(invoiceId), body
        );
        return data;
      },
      update: async (invoiceId: string | number, lineId: string | number, body: Partial<InvoiceLineItem>) => {
        const { data } = await api.patch<InvoiceLineItem>(
          `${ENDPOINTS.CREDITORS.INVOICE_LINES(invoiceId)}${lineId}/`, body
        );
        return data;
      },
      delete: async (invoiceId: string | number, lineId: string | number) => {
        await api.delete(`${ENDPOINTS.CREDITORS.INVOICE_LINES(invoiceId)}${lineId}/`);
      },
    },
  },

  // ── CREDIT NOTES ──────────────────────────────────────────────────────────
  creditNotes: {
    list: async (filters?: TransactionFilters) => {
      const { data } = await api.get<PaginatedResponse<CreditorCreditNote>>(
        ENDPOINTS.CREDITORS.CREDIT_NOTES, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<CreditorCreditNote>(
        `${ENDPOINTS.CREDITORS.CREDIT_NOTES}${id}/`
      );
      return data;
    },

    create: async (body: CreditorCreditNoteCreateData) => {
      const { data } = await api.post<CreditorCreditNote>(
        ENDPOINTS.CREDITORS.CREDIT_NOTES, body
      );
      return data;
    },

    update: async (id: string | number, body: Partial<CreditorCreditNoteCreateData>) => {
      const { data } = await api.patch<CreditorCreditNote>(
        `${ENDPOINTS.CREDITORS.CREDIT_NOTES}${id}/`, body
      );
      return data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.CREDIT_NOTES}${id}/`);
    },

    post: async (id: string | number) => {
      const { data } = await api.post<CreditorCreditNote>(
        ENDPOINTS.CREDITORS.POST_CREDIT_NOTE(id)
      );
      return data;
    },

    lines: {
      list: async (cnId: string | number) => {
        const { data } = await api.get<CreditNoteLineItem[]>(
          ENDPOINTS.CREDITORS.CREDIT_NOTE_LINES(cnId)
        );
        return data;
      },
      create: async (cnId: string | number, body: CreditNoteLineItem) => {
        const { data } = await api.post<CreditNoteLineItem>(
          ENDPOINTS.CREDITORS.CREDIT_NOTE_LINES(cnId), body
        );
        return data;
      },
      update: async (cnId: string | number, lineId: string | number, body: Partial<CreditNoteLineItem>) => {
        const { data } = await api.patch<CreditNoteLineItem>(
          `${ENDPOINTS.CREDITORS.CREDIT_NOTE_LINES(cnId)}${lineId}/`, body
        );
        return data;
      },
      delete: async (cnId: string | number, lineId: string | number) => {
        await api.delete(`${ENDPOINTS.CREDITORS.CREDIT_NOTE_LINES(cnId)}${lineId}/`);
      },
    },
  },

  // ── PAYMENTS ──────────────────────────────────────────────────────────────
  payments: {
    list: async (filters?: TransactionFilters) => {
      const { data } = await api.get<PaginatedResponse<CreditorPayment>>(
        ENDPOINTS.CREDITORS.PAYMENTS, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<CreditorPayment>(
        `${ENDPOINTS.CREDITORS.PAYMENTS}${id}/`
      );
      return data;
    },

    create: async (body: CreditorPaymentCreateData) => {
      const { data } = await api.post<CreditorPayment>(
        ENDPOINTS.CREDITORS.PAYMENTS, body
      );
      return data;
    },

    update: async (id: string | number, body: Partial<CreditorPaymentCreateData>) => {
      const { data } = await api.patch<CreditorPayment>(
        `${ENDPOINTS.CREDITORS.PAYMENTS}${id}/`, body
      );
      return data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.PAYMENTS}${id}/`);
    },

    post: async (id: string | number) => {
      const { data } = await api.post<CreditorPayment>(
        ENDPOINTS.CREDITORS.POST_PAYMENT(id)
      );
      return data;
    },

    allocate: async (id: string | number, allocations: PaymentAllocation | PaymentAllocation[]) => {
      const body = Array.isArray(allocations) ? allocations : [allocations];
      const { data } = await api.post(
        ENDPOINTS.CREDITORS.ALLOCATE_PAYMENT(id), body
      );
      return data;
    },
  },

  // ── JOURNALS ──────────────────────────────────────────────────────────────
  journals: {
    list: async (filters?: TransactionFilters) => {
      const { data } = await api.get<PaginatedResponse<CreditorJournal>>(
        ENDPOINTS.CREDITORS.JOURNALS, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<CreditorJournal>(
        `${ENDPOINTS.CREDITORS.JOURNALS}${id}/`
      );
      return data;
    },

    create: async (body: CreditorJournalCreateData) => {
      const { data } = await api.post<CreditorJournal>(
        ENDPOINTS.CREDITORS.JOURNALS, body
      );
      return data;
    },

    update: async (id: string | number, body: Partial<CreditorJournalCreateData>) => {
      const { data } = await api.patch<CreditorJournal>(
        `${ENDPOINTS.CREDITORS.JOURNALS}${id}/`, body
      );
      return data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.JOURNALS}${id}/`);
    },

    post: async (id: string | number) => {
      const { data } = await api.post<CreditorJournal>(
        ENDPOINTS.CREDITORS.POST_JOURNAL(id)
      );
      return data;
    },
  },

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

  // ── OPEN ITEMS ────────────────────────────────────────────────────────────
  openItems: {
    list: async (filters?: { creditor?: number; transaction_type?: string; is_fully_allocated?: boolean; is_legacy?: boolean; page?: number }) => {
      const { data } = await api.get<PaginatedResponse<CreditorOpenItem>>(
        ENDPOINTS.CREDITORS.OPEN_ITEMS, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<CreditorOpenItem>(
        `${ENDPOINTS.CREDITORS.OPEN_ITEMS}${id}/`
      );
      return data;
    },

    outstanding: async () => {
      const { data } = await api.get<CreditorOpenItem[]>(
        ENDPOINTS.CREDITORS.OPEN_ITEMS_OUTSTANDING
      );
      return data;
    },

    byCreditor: async (creditorId: string | number) => {
      const { data } = await api.get<CreditorOpenItem[]>(
        ENDPOINTS.CREDITORS.OPEN_ITEMS_BY_CREDITOR,
        { params: { creditor: creditorId } }
      );
      return data;
    },
  },

  // ── OPEN ITEM ALLOCATIONS ─────────────────────────────────────────────────
  openItemAllocations: {
    list: async (filters?: { payment?: number; open_item?: number }) => {
      const { data } = await api.get<PaginatedResponse<OpenItemAllocation>>(
        ENDPOINTS.CREDITORS.OPEN_ITEM_ALLOCATIONS, { params: filters }
      );
      return data;
    },

    create: async (body: OpenItemAllocation) => {
      const { data } = await api.post<OpenItemAllocation>(
        ENDPOINTS.CREDITORS.OPEN_ITEM_ALLOCATIONS, body
      );
      return data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.OPEN_ITEM_ALLOCATIONS}${id}/`);
    },
  },

  // ── OPEN ITEM AUDITS (read-only) ──────────────────────────────────────────
  openItemAudits: {
    list: async (filters?: { creditor?: number; transaction_type?: string; page?: number }) => {
      const { data } = await api.get<PaginatedResponse<OpenItemAudit>>(
        ENDPOINTS.CREDITORS.OPEN_ITEM_AUDITS, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<OpenItemAudit>(
        `${ENDPOINTS.CREDITORS.OPEN_ITEM_AUDITS}${id}/`
      );
      return data;
    },
  },

  // ── RFC (RETURN FOR CREDIT) ───────────────────────────────────────────────
  rfc: {
    list: async (filters?: { creditor?: number; status?: RFCStatus; page?: number }) => {
      const { data } = await api.get<PaginatedResponse<RFC>>(
        ENDPOINTS.CREDITORS.RFC, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<RFC>(`${ENDPOINTS.CREDITORS.RFC}${id}/`);
      return data;
    },

    create: async (body: RFCCreateData) => {
      const { data } = await api.post<RFC>(ENDPOINTS.CREDITORS.RFC, body);
      return data;
    },

    update: async (id: string | number, body: Partial<RFCCreateData>) => {
      const { data } = await api.patch<RFC>(
        `${ENDPOINTS.CREDITORS.RFC}${id}/`, body
      );
      return data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.RFC}${id}/`);
    },

    byStatus: async (status: RFCStatus) => {
      const { data } = await api.get<RFC[]>(
        ENDPOINTS.CREDITORS.RFC_BY_STATUS, { params: { status } }
      );
      return data;
    },

    updateStatus: async (id: string | number, status: RFCStatus) => {
      const { data } = await api.patch<RFC>(
        ENDPOINTS.CREDITORS.RFC_UPDATE_STATUS(id), { status }
      );
      return data;
    },

    lines: {
      list: async (rfcId: string | number) => {
        const { data } = await api.get<RFCLineItem[]>(
          ENDPOINTS.CREDITORS.RFC_LINES(rfcId)
        );
        return data;
      },
      create: async (rfcId: string | number, body: RFCLineItem) => {
        const { data } = await api.post<RFCLineItem>(
          ENDPOINTS.CREDITORS.RFC_LINES(rfcId), body
        );
        return data;
      },
      update: async (rfcId: string | number, lineId: string | number, body: Partial<RFCLineItem>) => {
        const { data } = await api.patch<RFCLineItem>(
          `${ENDPOINTS.CREDITORS.RFC_LINES(rfcId)}${lineId}/`, body
        );
        return data;
      },
      delete: async (rfcId: string | number, lineId: string | number) => {
        await api.delete(`${ENDPOINTS.CREDITORS.RFC_LINES(rfcId)}${lineId}/`);
      },
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
};

// ============================================================================
// useCreditorsAPI hook
// ============================================================================
export function useCreditorsAPI() {
  const listSuppliers     = useCallback((f?: CreditorFilters) => creditorsApi.accounts.list(f), []);
  const getSupplier       = useCallback((id: string | number) => creditorsApi.accounts.get(id), []);
  const createSupplier    = useCallback((d: SupplierCreateData) => creditorsApi.accounts.create(d), []);
  const updateSupplier    = useCallback((id: string | number, d: Partial<SupplierCreateData>) => creditorsApi.accounts.update(id, d), []);
  const deleteSupplier    = useCallback((id: string | number) => creditorsApi.accounts.delete(id), []);
  const getAgeAnalysis    = useCallback(() => creditorsApi.accounts.ageAnalysis(), []);
  const getAgedBalances   = useCallback((id: string | number) => creditorsApi.accounts.agedBalances(id), []);
  const recalculateAged   = useCallback((id: string | number) => creditorsApi.accounts.recalculateAged(id), []);

  const listCreditTerms = useCallback(async (): Promise<CreditTermsOption[]> => {
    try {
      const { data } = await api.get<PaginatedResponse<CreditTermsOption>>(
        ENDPOINTS.SETTINGS.CREDIT_TERMS
      );
      return data.results || [];
    } catch {
      return [];
    }
  }, []);

  const listExpenseCategories = useCallback(
    (f?: ExpenseCategoryFilters) =>
      settingsApi.expenseCategories.list(f).then((r) => r.results),
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

  return {
    listSuppliers, getSupplier, createSupplier, updateSupplier, deleteSupplier,
    getAgeAnalysis, getAgedBalances, recalculateAged,
    listCreditTerms,
    listExpenseCategories, createExpenseCategory, updateExpenseCategory, deleteExpenseCategory,
  };
}

export default creditorsApi;