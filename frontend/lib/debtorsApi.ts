/**
 * Enhanced Debtors API Client
 * Complete API integration with all debtors endpoints
 * 
 * Base URL: /api/v1/debtors/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';
import type {
  DebtorAccount,
  DebtorCreateData,
  DebtorEditData,
  DebtorFilters,
  Transaction,
  TransactionCreateData,
  TransactionFilters,
  OpenItem,
  PostDatedCheque,
  PostDatedChequeCreateData,
  SalesArea,
  DebtorsSummary,
  AgeAnalysis,
  AgeAnalysisFilters,
  PaginatedResponse,
  AuditLog,
} from './types/debtors';

export const debtorsApi = {
  // ============ DEBTOR ACCOUNTS ============
  accounts: {
    /**
     * List all debtor accounts with filters
     */
    list: async (filters?: DebtorFilters) => {
      try {
        console.log('Debtors filters:', filters);
        const response = await api.get<PaginatedResponse<DebtorAccount>>(
          ENDPOINTS.DEBTORS.ACCOUNTS,
          { params: filters }
        );
        return response.data;
      } catch (error: any) {
    // Log the error details for debugging
    if (error.response) {
      console.error('API error:', error.response.status, error.response.data);
        } else {
          console.error('API error:', error.message);
        }
        throw error;
      }
    },

    /**
     * Get single debtor account with full details
     */
    get: async (id: number) => {
      const response = await api.get<DebtorAccount>(`${ENDPOINTS.DEBTORS.ACCOUNTS}${id}/`);
      return response.data;
    },

    /**
     * Create new debtor account
     */
    create: async (data: DebtorCreateData) => {
      const response = await api.post<DebtorAccount>(ENDPOINTS.DEBTORS.ACCOUNTS, data);
      return response.data;
    },

    /**
     * Update debtor account
     */
    update: async (id: number, data: DebtorEditData) => {
      const response = await api.patch<DebtorAccount>(
        `${ENDPOINTS.DEBTORS.ACCOUNTS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete debtor account
     */
    delete: async (id: number) => {
      await api.delete(`${ENDPOINTS.DEBTORS.ACCOUNTS}${id}/`);
    },

    /**
     * Search debtors by name, number, or contact
     */
    search: async (searchTerm: string) => {
      const response = await api.get<DebtorAccount[]>(
        ENDPOINTS.DEBTORS.ACCOUNTS,
        { params: { search: searchTerm } }
      );
      return response.data;
    },

    /**
     * Get age analysis for a specific debtor
     */
    getAgeAnalysis: async (id: number, filters?: AgeAnalysisFilters) => {
      const response = await api.get<AgeAnalysis>(
        `${ENDPOINTS.DEBTORS.ACCOUNTS}${id}/age_analysis/`,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get transaction history for a debtor
     */
    getTransactions: async (id: number, filters?: TransactionFilters) => {
      const response = await api.get<PaginatedResponse<Transaction>>(
        `${ENDPOINTS.DEBTORS.ACCOUNTS}${id}/transactions/`,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Change debtor status (active/blocked)
     */
    updateStatus: async (id: number, is_active: boolean, blockflag?: boolean) => {
      const response = await api.patch<DebtorAccount>(
        `${ENDPOINTS.DEBTORS.ACCOUNTS}${id}/`,
        { is_active, blockflag }
      );
      return response.data;
    },
  },

  // ============ SUMMARY & ANALYTICS ============
  summary: {
    /**
     * Get overall debtors summary and analytics
     * @param cutoff_date - Optional cutoff date for age analysis (YYYY-MM-DD)
     */
    get: async (cutoff_date?: string) => {
      const response = await api.get<DebtorsSummary>(
        ENDPOINTS.DEBTORS.SUMMARY,
        { params: cutoff_date ? { cutoff_date } : undefined }
      );
      return response.data;
    },

    /**
     * Get top debtors by balance
     */
    getTopDebtors: async (limit: number = 10) => {
      const response = await api.get<DebtorAccount[]>(
        ENDPOINTS.DEBTORS.ACCOUNTS,
        { params: { top_debtors_limit: limit } }
      );
      return response.data;
    },
  },

  // ============ TRANSACTIONS ============
  transactions: {
    /**
     * List all transactions
     */
    list: async (filters?: TransactionFilters) => {
      const response = await api.get<PaginatedResponse<Transaction>>(
        ENDPOINTS.DEBTORS.TRANSACTIONS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single transaction
     */
    get: async (id: number) => {
      const response = await api.get<Transaction>(
        `${ENDPOINTS.DEBTORS.TRANSACTIONS}${id}/`
      );
      return response.data;
    },

    /**
     * Create transaction (invoice, credit note, etc.)
     */
    create: async (data: TransactionCreateData) => {
      const response = await api.post<Transaction>(
        ENDPOINTS.DEBTORS.TRANSACTIONS,
        data
      );
      return response.data;
    },

    /**
     * Update transaction
     */
    update: async (id: number, data: Partial<TransactionCreateData>) => {
      const response = await api.patch<Transaction>(
        `${ENDPOINTS.DEBTORS.TRANSACTIONS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete transaction
     */
    delete: async (id: number) => {
      await api.delete(`${ENDPOINTS.DEBTORS.TRANSACTIONS}${id}/`);
    },

    /**
     * Post debit journal entry
     */
    postDebit: async (data: {
      debtor_id: number;
      amount: number;
      description: string;
      transaction_date: string;
    }) => {
      const response = await api.post<Transaction>(
        `${ENDPOINTS.DEBTORS.TRANSACTIONS}post_debit/`,
        data
      );
      return response.data;
    },

    /**
     * Post credit journal entry
     */
    postCredit: async (data: {
      debtor_id: number;
      amount: number;
      description: string;
      transaction_date: string;
    }) => {
      const response = await api.post<Transaction>(
        `${ENDPOINTS.DEBTORS.TRANSACTIONS}post_credit/`,
        data
      );
      return response.data;
    },

    /**
     * Record receipt payment
     */
    postReceipt: async (data: {
      debtor_id: number;
      amount: number;
      reference_number?: string;
      transaction_date: string;
    }) => {
      const response = await api.post<Transaction>(
        `${ENDPOINTS.DEBTORS.TRANSACTIONS}post_receipt/`,
        data
      );
      return response.data;
    },

    /**
     * Charge interest on debtor account
     */
    chargeInterest: async (data: {
      debtor_id: number;
      amount: number;
      transaction_date: string;
    }) => {
      const response = await api.post<Transaction>(
        `${ENDPOINTS.DEBTORS.TRANSACTIONS}charge_interest/`,
        data
      );
      return response.data;
    },
  },

  // ============ OPEN ITEMS ============
  openItems: {
    /**
     * List open items for debtor
     */
    list: async (debtorId?: number) => {
      const response = await api.get<PaginatedResponse<OpenItem>>(
        ENDPOINTS.DEBTORS.OPEN_ITEMS,
        { params: debtorId ? { debtor_id: debtorId } : {} }
      );
      return response.data;
    },

    /**
     * Get single open item
     */
    get: async (id: number) => {
      const response = await api.get<OpenItem>(
        `${ENDPOINTS.DEBTORS.OPEN_ITEMS}${id}/`
      );
      return response.data;
    },

    /**
     * Allocate receipt to open items
     */
    allocate: async (data: {
      debtor_id: number;
      receipt_amount: number;
      allocations: Array<{
        open_item_id: number;
        amount: number;
      }>;
    }) => {
      const response = await api.post(
        `${ENDPOINTS.DEBTORS.OPEN_ITEMS}allocate/`,
        data
      );
      return response.data;
    },
  },

  // ============ POST-DATED CHEQUES ============
  pdcs: {
    /**
     * List post-dated cheques
     */
    list: async (debtorId?: number) => {
      const response = await api.get<PaginatedResponse<PostDatedCheque>>(
        ENDPOINTS.DEBTORS.POST_DATED_CHEQUES,
        { params: debtorId ? { debtor_id: debtorId } : {} }
      );
      return response.data;
    },

    /**
     * Get single PDC
     */
    get: async (id: number) => {
      const response = await api.get<PostDatedCheque>(
        `${ENDPOINTS.DEBTORS.POST_DATED_CHEQUES}${id}/`
      );
      return response.data;
    },

    /**
     * Create PDC record
     */
    create: async (data: PostDatedChequeCreateData) => {
      const response = await api.post<PostDatedCheque>(
        ENDPOINTS.DEBTORS.POST_DATED_CHEQUES,
        data
      );
      return response.data;
    },

    /**
     * Update PDC status or details
     */
    update: async (id: number, data: Partial<PostDatedChequeCreateData>) => {
      const response = await api.patch<PostDatedCheque>(
        `${ENDPOINTS.DEBTORS.POST_DATED_CHEQUES}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Update PDC status (received/cleared/dishonoured)
     */
    updateStatus: async (
      id: number,
      status: 'OUTSTANDING' | 'RECEIVED' | 'CLEARED' | 'DISHONOURED',
      statusDate?: string
    ) => {
      const response = await api.patch<PostDatedCheque>(
        `${ENDPOINTS.DEBTORS.POST_DATED_CHEQUES}${id}/`,
        { status, status_date: statusDate }
      );
      return response.data;
    },

    /**
     * Delete PDC
     */
    delete: async (id: number) => {
      await api.delete(`${ENDPOINTS.DEBTORS.POST_DATED_CHEQUES}${id}/`);
    },
  },

  // ============ SALES AREAS ============
  areas: {
    /**
     * List all sales areas
     */
    list: async () => {
      const response = await api.get<SalesArea[]>(ENDPOINTS.DEBTORS.SALES_AREAS);
      return response.data;
    },

    /**
     * Get single sales area
     */
    get: async (id: number) => {
      const response = await api.get<SalesArea>(
        `${ENDPOINTS.DEBTORS.SALES_AREAS}${id}/`
      );
      return response.data;
    },

    /**
     * Create sales area
     */
    create: async (data: Omit<SalesArea, 'id' | 'created_at'>) => {
      const response = await api.post<SalesArea>(
        ENDPOINTS.DEBTORS.SALES_AREAS,
        data
      );
      return response.data;
    },

    /**
     * Update sales area
     */
    update: async (id: number, data: Partial<Omit<SalesArea, 'id' | 'created_at'>>) => {
      const response = await api.patch<SalesArea>(
        `${ENDPOINTS.DEBTORS.SALES_AREAS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete sales area
     */
    delete: async (id: number) => {
      await api.delete(`${ENDPOINTS.DEBTORS.SALES_AREAS}${id}/`);
    },
  },

  // ============ AUDIT TRAIL ============
  audit: {
    /**
     * Get audit trail for debtor
     */
    getDebtorAudit: async (debtorId: number) => {
      const response = await api.get<PaginatedResponse<AuditLog>>(
        ENDPOINTS.DEBTORS.AUDIT,
        { params: { debtor_id: debtorId } }
      );
      return response.data;
    },

    /**
     * Get all audit logs
     */
    list: async (filters?: { date_from?: string; date_to?: string }) => {
      const response = await api.get<PaginatedResponse<AuditLog>>(
        ENDPOINTS.DEBTORS.AUDIT,
        { params: filters }
      );
      return response.data;
    },
  },
};

export default debtorsApi;
