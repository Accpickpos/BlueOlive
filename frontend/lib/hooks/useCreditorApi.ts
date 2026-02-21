/**
 * useCreditorApi Hook
 * React hooks for interacting with the Creditors API.
 * Manages loading, error, and auto-fetch state.
 *
 * Authentication:
 *   - All endpoints require IsAuthenticated permission
 *   - Cookie-based JWT (sent automatically via withCredentials)
 *   - X-Tenant header injected by the axios interceptor in api.ts
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  CreditorAccount,
  AgedBalanceSummary,
  GoodsReceivedNote,
  CreditorInvoice,
  CreditorCreditNote,
  CreditorPayment,
  CreditorJournal,
  SupplierLedgerEntry,
  CreditorOpenItem,
  OpenItemAllocation,
  RFC,
  SupplierPaymentOrder,
  PaginatedResponse,
  CreditorCreateData,
  CreditorEditData,
  CreditorFilters,
  CreditorsSummary,
  TransactionFilters,
  GoodsReceivedNoteCreateData,
  CreditorInvoiceCreateData,
  CreditorCreditNoteCreateData,
  CreditorPaymentCreateData,
  PaymentAllocation,
  CreditorJournalCreateData,
  RFCCreateData,
  RFCStatus,
  SupplierPaymentOrderCreateData,
} from '../types/creditors';
import { api } from '../api';
import { ENDPOINTS } from '../api-config';

// ============================================================================
// Shared hook types
// ============================================================================

export interface ApiError {
  message: string;
  status?: number;
  details?: any;
}

export type QueryParams = Record<string, any>;

export interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

export interface UseApiResponse<T> extends UseApiState<T> {
  refetch: () => Promise<void>;
  reset: () => void;
}

// ============================================================================
// Generic fetch hook factory — keeps every hook DRY
// ============================================================================

function useApiFetch<T>(
  fetcher: () => Promise<T>,
  enabled = true
): UseApiResponse<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const refetch = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await fetcher();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as ApiError });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  useEffect(() => {
    if (enabled) refetch();
  }, [enabled, refetch]);

  return { ...state, refetch, reset };
}

// ============================================================================
// Generic mutation hook factory
// ============================================================================

function useApiMutation<TArgs extends any[], TResult>(
  mutator: (...args: TArgs) => Promise<TResult>
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const execute = useCallback(
    async (...args: TArgs): Promise<TResult> => {
      setLoading(true);
      setError(null);
      try {
        const result = await mutator(...args);
        setLoading(false);
        return result;
      } catch (err) {
        setError(err as ApiError);
        setLoading(false);
        throw err;
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
  }, []);

  return { loading, error, execute, reset };
}

// ============================================================================
// CREDITOR LIST / DETAIL
// ============================================================================

/**
 * Paginated list of creditors.
 * Filter params: search, account_category ('B'|'O'), is_active, page, ordering
 */
export function useCreditors(
  params: CreditorFilters = {},
  enabled = true
): UseApiResponse<PaginatedResponse<CreditorAccount>> {
  return useApiFetch(
    () => api.get<PaginatedResponse<CreditorAccount>>(
      ENDPOINTS.CREDITORS.ACCOUNTS, { params }
    ).then((r) => r.data),
    enabled
  );
}

/** Single creditor by id. */
export function useCreditorById(
  id: string | number | null,
  enabled = true
): UseApiResponse<CreditorAccount> {
  return useApiFetch(
    () => api.get<CreditorAccount>(
      `${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`
    ).then((r) => r.data),
    enabled && id !== null
  );
}

/** Aged-balance snapshot for a single creditor. */
export function useCreditorAgedBalances(
  id: string | number | null,
  enabled = true
): UseApiResponse<AgedBalanceSummary> {
  return useApiFetch(
    () => api.get<AgedBalanceSummary>(
      ENDPOINTS.CREDITORS.AGED_BALANCES(id!)
    ).then((r) => r.data),
    enabled && id !== null
  );
}

/** Age analysis across all creditors with an outstanding balance. */
export function useAgeAnalysis(
  enabled = true
): UseApiResponse<AgedBalanceSummary[]> {
  return useApiFetch(
    () => api.get<AgedBalanceSummary[]>(
      ENDPOINTS.CREDITORS.AGE_ANALYSIS
    ).then((r) => r.data),
    enabled
  );
}

// ============================================================================
// GOODS RECEIVED NOTES
// ============================================================================

export function useGrns(
  params: TransactionFilters = {},
  enabled = true
): UseApiResponse<PaginatedResponse<GoodsReceivedNote>> {
  return useApiFetch(
    () => api.get<PaginatedResponse<GoodsReceivedNote>>(
      ENDPOINTS.CREDITORS.GRNS, { params }
    ).then((r) => r.data),
    enabled
  );
}

export function useGrnById(
  id: string | number | null,
  enabled = true
): UseApiResponse<GoodsReceivedNote> {
  return useApiFetch(
    () => api.get<GoodsReceivedNote>(
      `${ENDPOINTS.CREDITORS.GRNS}${id}/`
    ).then((r) => r.data),
    enabled && id !== null
  );
}

// ============================================================================
// CREDITOR INVOICES
// ============================================================================

export function useCreditorInvoices(
  params: TransactionFilters = {},
  enabled = true
): UseApiResponse<PaginatedResponse<CreditorInvoice>> {
  return useApiFetch(
    () => api.get<PaginatedResponse<CreditorInvoice>>(
      ENDPOINTS.CREDITORS.INVOICES, { params }
    ).then((r) => r.data),
    enabled
  );
}

export function useCreditorInvoiceById(
  id: string | number | null,
  enabled = true
): UseApiResponse<CreditorInvoice> {
  return useApiFetch(
    () => api.get<CreditorInvoice>(
      `${ENDPOINTS.CREDITORS.INVOICES}${id}/`
    ).then((r) => r.data),
    enabled && id !== null
  );
}

// ============================================================================
// CREDIT NOTES
// ============================================================================

export function useCreditorCreditNotes(
  params: TransactionFilters = {},
  enabled = true
): UseApiResponse<PaginatedResponse<CreditorCreditNote>> {
  return useApiFetch(
    () => api.get<PaginatedResponse<CreditorCreditNote>>(
      ENDPOINTS.CREDITORS.CREDIT_NOTES, { params }
    ).then((r) => r.data),
    enabled
  );
}

export function useCreditorCreditNoteById(
  id: string | number | null,
  enabled = true
): UseApiResponse<CreditorCreditNote> {
  return useApiFetch(
    () => api.get<CreditorCreditNote>(
      `${ENDPOINTS.CREDITORS.CREDIT_NOTES}${id}/`
    ).then((r) => r.data),
    enabled && id !== null
  );
}

// ============================================================================
// PAYMENTS
// ============================================================================

export function useCreditorPayments(
  params: TransactionFilters = {},
  enabled = true
): UseApiResponse<PaginatedResponse<CreditorPayment>> {
  return useApiFetch(
    () => api.get<PaginatedResponse<CreditorPayment>>(
      ENDPOINTS.CREDITORS.PAYMENTS, { params }
    ).then((r) => r.data),
    enabled
  );
}

export function useCreditorPaymentById(
  id: string | number | null,
  enabled = true
): UseApiResponse<CreditorPayment> {
  return useApiFetch(
    () => api.get<CreditorPayment>(
      `${ENDPOINTS.CREDITORS.PAYMENTS}${id}/`
    ).then((r) => r.data),
    enabled && id !== null
  );
}

// ============================================================================
// JOURNALS
// ============================================================================

export function useCreditorJournals(
  params: TransactionFilters = {},
  enabled = true
): UseApiResponse<PaginatedResponse<CreditorJournal>> {
  return useApiFetch(
    () => api.get<PaginatedResponse<CreditorJournal>>(
      ENDPOINTS.CREDITORS.JOURNALS, { params }
    ).then((r) => r.data),
    enabled
  );
}

// ============================================================================
// SUPPLIER LEDGER (read-only)
// ============================================================================

export function useSupplierLedger(
  params: { creditor?: number; transaction_type?: string; search?: string; page?: number } = {},
  enabled = true
): UseApiResponse<PaginatedResponse<SupplierLedgerEntry>> {
  return useApiFetch(
    () => api.get<PaginatedResponse<SupplierLedgerEntry>>(
      ENDPOINTS.CREDITORS.LEDGER, { params }
    ).then((r) => r.data),
    enabled
  );
}

// ============================================================================
// OPEN ITEMS
// ============================================================================

export function useCreditorOpenItems(
  params: { creditor?: number; is_fully_allocated?: boolean; transaction_type?: string; page?: number } = {},
  enabled = true
): UseApiResponse<PaginatedResponse<CreditorOpenItem>> {
  return useApiFetch(
    () => api.get<PaginatedResponse<CreditorOpenItem>>(
      ENDPOINTS.CREDITORS.OPEN_ITEMS, { params }
    ).then((r) => r.data),
    enabled
  );
}

/** All unallocated open items across all creditors. */
export function useOutstandingOpenItems(
  enabled = true
): UseApiResponse<CreditorOpenItem[]> {
  return useApiFetch(
    () => api.get<CreditorOpenItem[]>(
      ENDPOINTS.CREDITORS.OPEN_ITEMS_OUTSTANDING
    ).then((r) => r.data),
    enabled
  );
}

// ============================================================================
// RFC
// ============================================================================

export function useRfcs(
  params: { creditor?: number; status?: RFCStatus; page?: number } = {},
  enabled = true
): UseApiResponse<PaginatedResponse<RFC>> {
  return useApiFetch(
    () => api.get<PaginatedResponse<RFC>>(
      ENDPOINTS.CREDITORS.RFC, { params }
    ).then((r) => r.data),
    enabled
  );
}

export function useRfcById(
  id: string | number | null,
  enabled = true
): UseApiResponse<RFC> {
  return useApiFetch(
    () => api.get<RFC>(
      `${ENDPOINTS.CREDITORS.RFC}${id}/`
    ).then((r) => r.data),
    enabled && id !== null
  );
}

// ============================================================================
// SUPPLIER PAYMENT ORDERS
// ============================================================================

export function usePaymentOrders(
  params: { creditor?: number; is_processed?: boolean } = {},
  enabled = true
): UseApiResponse<PaginatedResponse<SupplierPaymentOrder>> {
  return useApiFetch(
    () => api.get<PaginatedResponse<SupplierPaymentOrder>>(
      ENDPOINTS.CREDITORS.PAYMENT_ORDERS, { params }
    ).then((r) => r.data),
    enabled
  );
}

export function usePendingPaymentOrders(
  enabled = true
): UseApiResponse<SupplierPaymentOrder[]> {
  return useApiFetch(
    () => api.get<SupplierPaymentOrder[]>(
      ENDPOINTS.CREDITORS.PAYMENT_ORDERS_PENDING
    ).then((r) => r.data),
    enabled
  );
}

// ============================================================================
// MUTATION HOOKS
// ============================================================================

/** Create, update, delete creditors. */
export function useCreditorMutation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const run = async <T>(fn: () => Promise<T>): Promise<T> => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setLoading(false);
      return result;
    } catch (err) {
      setError(err as ApiError);
      setLoading(false);
      throw err;
    }
  };

  const createCreditor = (data: CreditorCreateData) =>
    run(() => api.post<CreditorAccount>(ENDPOINTS.CREDITORS.ACCOUNTS, data).then((r) => r.data));

  const updateCreditor = (id: string | number, data: CreditorEditData) =>
    run(() => api.patch<CreditorAccount>(`${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`, data).then((r) => r.data));

  const deleteCreditor = (id: string | number) =>
    run(() => api.delete(`${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`).then(() => undefined));

  const recalculateAged = (id: string | number) =>
    run(() => api.post<AgedBalanceSummary>(ENDPOINTS.CREDITORS.RECALCULATE_AGED(id)).then((r) => r.data));

  const reset = () => { setLoading(false); setError(null); };

  return { loading, error, createCreditor, updateCreditor, deleteCreditor, recalculateAged, reset };
}

/** Create, update, delete, post GRNs. */
export function useGrnMutation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const run = async <T>(fn: () => Promise<T>): Promise<T> => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setLoading(false);
      return result;
    } catch (err) {
      setError(err as ApiError);
      setLoading(false);
      throw err;
    }
  };

  const createGrn = (data: GoodsReceivedNoteCreateData) =>
    run(() => api.post<GoodsReceivedNote>(ENDPOINTS.CREDITORS.GRNS, data).then((r) => r.data));

  const updateGrn = (id: string | number, data: Partial<GoodsReceivedNoteCreateData>) =>
    run(() => api.patch<GoodsReceivedNote>(`${ENDPOINTS.CREDITORS.GRNS}${id}/`, data).then((r) => r.data));

  const deleteGrn = (id: string | number) =>
    run(() => api.delete(`${ENDPOINTS.CREDITORS.GRNS}${id}/`).then(() => undefined));

  const postGrn = (id: string | number) =>
    run(() => api.post<GoodsReceivedNote>(ENDPOINTS.CREDITORS.POST_GRN(id)).then((r) => r.data));

  const reset = () => { setLoading(false); setError(null); };

  return { loading, error, createGrn, updateGrn, deleteGrn, postGrn, reset };
}

/** Create, update, delete, post creditor invoices. */
export function useInvoiceMutation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const run = async <T>(fn: () => Promise<T>): Promise<T> => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setLoading(false);
      return result;
    } catch (err) {
      setError(err as ApiError);
      setLoading(false);
      throw err;
    }
  };

  const createInvoice = (data: CreditorInvoiceCreateData) =>
    run(() => api.post<CreditorInvoice>(ENDPOINTS.CREDITORS.INVOICES, data).then((r) => r.data));

  const updateInvoice = (id: string | number, data: Partial<CreditorInvoiceCreateData>) =>
    run(() => api.patch<CreditorInvoice>(`${ENDPOINTS.CREDITORS.INVOICES}${id}/`, data).then((r) => r.data));

  const deleteInvoice = (id: string | number) =>
    run(() => api.delete(`${ENDPOINTS.CREDITORS.INVOICES}${id}/`).then(() => undefined));

  const postInvoice = (id: string | number) =>
    run(() => api.post<CreditorInvoice>(ENDPOINTS.CREDITORS.POST_INVOICE(id)).then((r) => r.data));

  const reset = () => { setLoading(false); setError(null); };

  return { loading, error, createInvoice, updateInvoice, deleteInvoice, postInvoice, reset };
}

/** Create, update, delete, post credit notes. */
export function useCreditNoteMutation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const run = async <T>(fn: () => Promise<T>): Promise<T> => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setLoading(false);
      return result;
    } catch (err) {
      setError(err as ApiError);
      setLoading(false);
      throw err;
    }
  };

  const createCreditNote = (data: CreditorCreditNoteCreateData) =>
    run(() => api.post<CreditorCreditNote>(ENDPOINTS.CREDITORS.CREDIT_NOTES, data).then((r) => r.data));

  const updateCreditNote = (id: string | number, data: Partial<CreditorCreditNoteCreateData>) =>
    run(() => api.patch<CreditorCreditNote>(`${ENDPOINTS.CREDITORS.CREDIT_NOTES}${id}/`, data).then((r) => r.data));

  const deleteCreditNote = (id: string | number) =>
    run(() => api.delete(`${ENDPOINTS.CREDITORS.CREDIT_NOTES}${id}/`).then(() => undefined));

  const postCreditNote = (id: string | number) =>
    run(() => api.post<CreditorCreditNote>(ENDPOINTS.CREDITORS.POST_CREDIT_NOTE(id)).then((r) => r.data));

  const reset = () => { setLoading(false); setError(null); };

  return { loading, error, createCreditNote, updateCreditNote, deleteCreditNote, postCreditNote, reset };
}

/** Create, update, delete, post, and allocate payments. */
export function usePaymentMutation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const run = async <T>(fn: () => Promise<T>): Promise<T> => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setLoading(false);
      return result;
    } catch (err) {
      setError(err as ApiError);
      setLoading(false);
      throw err;
    }
  };

  const createPayment = (data: CreditorPaymentCreateData) =>
    run(() => api.post<CreditorPayment>(ENDPOINTS.CREDITORS.PAYMENTS, data).then((r) => r.data));

  const updatePayment = (id: string | number, data: Partial<CreditorPaymentCreateData>) =>
    run(() => api.patch<CreditorPayment>(`${ENDPOINTS.CREDITORS.PAYMENTS}${id}/`, data).then((r) => r.data));

  const deletePayment = (id: string | number) =>
    run(() => api.delete(`${ENDPOINTS.CREDITORS.PAYMENTS}${id}/`).then(() => undefined));

  const postPayment = (id: string | number) =>
    run(() => api.post<CreditorPayment>(ENDPOINTS.CREDITORS.POST_PAYMENT(id)).then((r) => r.data));

  const allocatePayment = (id: string | number, allocations: PaymentAllocation | PaymentAllocation[]) => {
    const body = Array.isArray(allocations) ? allocations : [allocations];
    return run(() => api.post(ENDPOINTS.CREDITORS.ALLOCATE_PAYMENT(id), body).then((r) => r.data));
  };

  const reset = () => { setLoading(false); setError(null); };

  return { loading, error, createPayment, updatePayment, deletePayment, postPayment, allocatePayment, reset };
}

/** Create, update, delete, post journals. */
export function useJournalMutation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const run = async <T>(fn: () => Promise<T>): Promise<T> => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setLoading(false);
      return result;
    } catch (err) {
      setError(err as ApiError);
      setLoading(false);
      throw err;
    }
  };

  const createJournal = (data: CreditorJournalCreateData) =>
    run(() => api.post<CreditorJournal>(ENDPOINTS.CREDITORS.JOURNALS, data).then((r) => r.data));

  const updateJournal = (id: string | number, data: Partial<CreditorJournalCreateData>) =>
    run(() => api.patch<CreditorJournal>(`${ENDPOINTS.CREDITORS.JOURNALS}${id}/`, data).then((r) => r.data));

  const deleteJournal = (id: string | number) =>
    run(() => api.delete(`${ENDPOINTS.CREDITORS.JOURNALS}${id}/`).then(() => undefined));

  const postJournal = (id: string | number) =>
    run(() => api.post<CreditorJournal>(ENDPOINTS.CREDITORS.POST_JOURNAL(id)).then((r) => r.data));

  const reset = () => { setLoading(false); setError(null); };

  return { loading, error, createJournal, updateJournal, deleteJournal, postJournal, reset };
}

/** Create, update, delete RFCs and update their status. */
export function useRfcMutation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const run = async <T>(fn: () => Promise<T>): Promise<T> => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setLoading(false);
      return result;
    } catch (err) {
      setError(err as ApiError);
      setLoading(false);
      throw err;
    }
  };

  const createRfc = (data: RFCCreateData) =>
    run(() => api.post<RFC>(ENDPOINTS.CREDITORS.RFC, data).then((r) => r.data));

  const updateRfc = (id: string | number, data: Partial<RFCCreateData>) =>
    run(() => api.patch<RFC>(`${ENDPOINTS.CREDITORS.RFC}${id}/`, data).then((r) => r.data));

  const deleteRfc = (id: string | number) =>
    run(() => api.delete(`${ENDPOINTS.CREDITORS.RFC}${id}/`).then(() => undefined));

  const updateRfcStatus = (id: string | number, status: RFCStatus) =>
    run(() => api.patch<RFC>(ENDPOINTS.CREDITORS.RFC_UPDATE_STATUS(id), { status }).then((r) => r.data));

  const reset = () => { setLoading(false); setError(null); };

  return { loading, error, createRfc, updateRfc, deleteRfc, updateRfcStatus, reset };
}

/** Create, update, delete, and process supplier payment orders. */
export function usePaymentOrderMutation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const run = async <T>(fn: () => Promise<T>): Promise<T> => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setLoading(false);
      return result;
    } catch (err) {
      setError(err as ApiError);
      setLoading(false);
      throw err;
    }
  };

  const createOrder = (data: SupplierPaymentOrderCreateData) =>
    run(() => api.post<SupplierPaymentOrder>(ENDPOINTS.CREDITORS.PAYMENT_ORDERS, data).then((r) => r.data));

  const updateOrder = (id: string | number, data: Partial<SupplierPaymentOrderCreateData>) =>
    run(() => api.patch<SupplierPaymentOrder>(`${ENDPOINTS.CREDITORS.PAYMENT_ORDERS}${id}/`, data).then((r) => r.data));

  const deleteOrder = (id: string | number) =>
    run(() => api.delete(`${ENDPOINTS.CREDITORS.PAYMENT_ORDERS}${id}/`).then(() => undefined));

  const processOrder = (id: string | number) =>
    run(() => api.post<SupplierPaymentOrder>(ENDPOINTS.CREDITORS.PROCESS_PAYMENT_ORDER(id)).then((r) => r.data));

  const reset = () => { setLoading(false); setError(null); };

  return { loading, error, createOrder, updateOrder, deleteOrder, processOrder, reset };
}

// ── Backward-compat aliases (so existing imports don't break) ────────────────

/**
 * @deprecated Use useCreditorAgedBalances(id) instead.
 * Previously called AGING_ANALYSIS which pointed to a non-existent URL.
 * Now calls /creditors/creditors/{id}/aged_balances/
 */
export function useCreditorAgingAnalysis(
  id: string | number | null
): UseApiResponse<AgedBalanceSummary> {
  return useCreditorAgedBalances(id);
}

/**
 * @deprecated Use useAgeAnalysis() instead.
 * Previously called CREDITORS.SUMMARY which no longer exists.
 * Now calls /creditors/creditors/age_analysis/
 */
export function useCreditorsSummary(
  enabled = true
): UseApiResponse<AgedBalanceSummary[]> {
  return useAgeAnalysis(enabled);
}