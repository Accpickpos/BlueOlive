/**
 * Creditors Transactions API Client
 * Handles all transactional operations for creditors.
 *
 * Base URL: /api/v1/creditors/
 */

'use client';

import { api } from '../api';
import { ENDPOINTS } from '../api-config';
import {
  TransactionFilters,
  PaginatedResponse,
  SupplierLedgerEntry,
  CreditorJournal,
  CreditorJournalCreateData,
  CreditorPayment,
  CreditorPaymentCreateData,
  PaymentAllocation,
  CreditorOpenItem,
  OpenItemAllocation,
  OpenItemAudit,
} from '../types/creditors';

// ============================================================================
// Transactions API client
// ============================================================================
export const creditorsTransactionsApi = {

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

};
