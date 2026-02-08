/**
 * Cash Book API Client
 * 
 * Handles all cash book and bank management endpoints:
 * - Income and expense categories
 * - Bank transactions (deposits, withdrawals, transfers)
 * - Bank reconciliations
 * - Cash floats
 * - Cheque management
 * 
 * Base URL: /api/v1/cash-book/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';

export interface IncomeCategory {
  id?: number;
  name: string;
  code: string;
  description?: string;
  is_active: boolean;
  created_at?: string;
  [key: string]: any;
}

export interface Transaction {
  id?: number;
  date: string;
  description: string;
  amount: number;
  category_id: number;
  reference?: string;
  created_at?: string;
  [key: string]: any;
}

export interface BankDeposit {
  id?: number;
  date: string;
  amount: number;
  reference?: string;
  notes?: string;
  created_at?: string;
  [key: string]: any;
}

export interface BankTransfer {
  id?: number;
  from_account: string;
  to_account: string;
  amount: number;
  date: string;
  reference?: string;
  created_at?: string;
  [key: string]: any;
}

export interface BankReconciliation {
  id?: number;
  reconciliation_date: string;
  bank_statement_balance: number;
  system_balance: number;
  variance: number;
  notes?: string;
  created_at?: string;
  [key: string]: any;
}

export interface CashFloat {
  id?: number;
  register_name: string;
  opening_float: number;
  current_balance: number;
  date: string;
  created_at?: string;
  [key: string]: any;
}

export interface UnpresentedCheque {
  id?: number;
  cheque_number: string;
  amount: number;
  payee: string;
  date_issued: string;
  status: 'OUTSTANDING' | 'CLEARED' | 'CANCELLED';
  created_at?: string;
  [key: string]: any;
}

export const cashBookApi = {
  // ============ INCOME CATEGORIES ============
  incomeCategories: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: IncomeCategory[] }>(
        ENDPOINTS.CASH_BOOK.INCOME_CATEGORIES,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<IncomeCategory>(
        `${ENDPOINTS.CASH_BOOK.INCOME_CATEGORIES}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<IncomeCategory>) => {
      const response = await api.post<IncomeCategory>(
        ENDPOINTS.CASH_BOOK.INCOME_CATEGORIES,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<IncomeCategory>) => {
      const response = await api.patch<IncomeCategory>(
        `${ENDPOINTS.CASH_BOOK.INCOME_CATEGORIES}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.CASH_BOOK.INCOME_CATEGORIES}${id}/`);
    },
  },

  // ============ EXPENSE CATEGORIES ============
  expenseCategories: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: IncomeCategory[] }>(
        ENDPOINTS.CASH_BOOK.EXPENSE_CATEGORIES,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<IncomeCategory>(
        `${ENDPOINTS.CASH_BOOK.EXPENSE_CATEGORIES}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<IncomeCategory>) => {
      const response = await api.post<IncomeCategory>(
        ENDPOINTS.CASH_BOOK.EXPENSE_CATEGORIES,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<IncomeCategory>) => {
      const response = await api.patch<IncomeCategory>(
        `${ENDPOINTS.CASH_BOOK.EXPENSE_CATEGORIES}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.CASH_BOOK.EXPENSE_CATEGORIES}${id}/`);
    },
  },

  // ============ TRANSACTIONS ============
  transactions: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: Transaction[] }>(
        ENDPOINTS.CASH_BOOK.TRANSACTIONS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<Transaction>(
        `${ENDPOINTS.CASH_BOOK.TRANSACTIONS}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<Transaction>) => {
      const response = await api.post<Transaction>(
        ENDPOINTS.CASH_BOOK.TRANSACTIONS,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<Transaction>) => {
      const response = await api.patch<Transaction>(
        `${ENDPOINTS.CASH_BOOK.TRANSACTIONS}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.CASH_BOOK.TRANSACTIONS}${id}/`);
    },
  },

  // ============ OTHER INCOME ============
  otherIncome: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: Transaction[] }>(
        ENDPOINTS.CASH_BOOK.OTHER_INCOME,
        { params: filters }
      );
      return response.data;
    },

    create: async (data: any) => {
      const response = await api.post(
        ENDPOINTS.CASH_BOOK.OTHER_INCOME,
        data
      );
      return response.data;
    },
  },

  // ============ OTHER EXPENSES ============
  otherExpenses: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: Transaction[] }>(
        ENDPOINTS.CASH_BOOK.OTHER_EXPENSES,
        { params: filters }
      );
      return response.data;
    },

    create: async (data: any) => {
      const response = await api.post(
        ENDPOINTS.CASH_BOOK.OTHER_EXPENSES,
        data
      );
      return response.data;
    },
  },

  // ============ BANK DEPOSITS ============
  deposits: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: BankDeposit[] }>(
        ENDPOINTS.CASH_BOOK.BANK_DEPOSITS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<BankDeposit>(
        `${ENDPOINTS.CASH_BOOK.BANK_DEPOSITS}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<BankDeposit>) => {
      const response = await api.post<BankDeposit>(
        ENDPOINTS.CASH_BOOK.BANK_DEPOSITS,
        data
      );
      return response.data;
    },
  },

  // ============ CASH WITHDRAWALS ============
  withdrawals: {
    list: async (filters?: any) => {
      const response = await api.get(
        ENDPOINTS.CASH_BOOK.CASH_WITHDRAWALS,
        { params: filters }
      );
      return response.data;
    },

    create: async (data: any) => {
      const response = await api.post(
        ENDPOINTS.CASH_BOOK.CASH_WITHDRAWALS,
        data
      );
      return response.data;
    },
  },

  // ============ BANK TRANSFERS ============
  transfers: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: BankTransfer[] }>(
        ENDPOINTS.CASH_BOOK.BANK_TRANSFERS,
        { params: filters }
      );
      return response.data;
    },

    create: async (data: Partial<BankTransfer>) => {
      const response = await api.post<BankTransfer>(
        ENDPOINTS.CASH_BOOK.BANK_TRANSFERS,
        data
      );
      return response.data;
    },
  },

  // ============ BANK CHARGES ============
  charges: {
    list: async (filters?: any) => {
      const response = await api.get(
        ENDPOINTS.CASH_BOOK.BANK_CHARGES,
        { params: filters }
      );
      return response.data;
    },

    create: async (data: any) => {
      const response = await api.post(
        ENDPOINTS.CASH_BOOK.BANK_CHARGES,
        data
      );
      return response.data;
    },
  },

  // ============ INTEREST RECEIVED ============
  interestReceived: {
    list: async (filters?: any) => {
      const response = await api.get(
        ENDPOINTS.CASH_BOOK.INTEREST_RECEIVED,
        { params: filters }
      );
      return response.data;
    },

    create: async (data: any) => {
      const response = await api.post(
        ENDPOINTS.CASH_BOOK.INTEREST_RECEIVED,
        data
      );
      return response.data;
    },
  },

  // ============ BANK RECONCILIATIONS ============
  reconciliations: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: BankReconciliation[] }>(
        ENDPOINTS.CASH_BOOK.RECONCILIATIONS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<BankReconciliation>(
        `${ENDPOINTS.CASH_BOOK.RECONCILIATIONS}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<BankReconciliation>) => {
      const response = await api.post<BankReconciliation>(
        ENDPOINTS.CASH_BOOK.RECONCILIATIONS,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<BankReconciliation>) => {
      const response = await api.patch<BankReconciliation>(
        `${ENDPOINTS.CASH_BOOK.RECONCILIATIONS}${id}/`,
        data
      );
      return response.data;
    },
  },

  // ============ CASH FLOATS ============
  floats: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: CashFloat[] }>(
        ENDPOINTS.CASH_BOOK.CASH_FLOATS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<CashFloat>(
        `${ENDPOINTS.CASH_BOOK.CASH_FLOATS}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<CashFloat>) => {
      const response = await api.post<CashFloat>(
        ENDPOINTS.CASH_BOOK.CASH_FLOATS,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<CashFloat>) => {
      const response = await api.patch<CashFloat>(
        `${ENDPOINTS.CASH_BOOK.CASH_FLOATS}${id}/`,
        data
      );
      return response.data;
    },
  },

  // ============ CATEGORY BALANCES ============
  categoryBalances: {
    list: async (filters?: any) => {
      const response = await api.get(
        ENDPOINTS.CASH_BOOK.CATEGORY_BALANCES,
        { params: filters }
      );
      return response.data;
    },

    get: async (categoryId: number | string) => {
      const response = await api.get(
        `${ENDPOINTS.CASH_BOOK.CATEGORY_BALANCES}${categoryId}/`
      );
      return response.data;
    },
  },

  // ============ UNPRESENTED CHEQUES ============
  unpresentedCheques: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: UnpresentedCheque[] }>(
        ENDPOINTS.CASH_BOOK.UNPRESENTED_CHEQUES,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<UnpresentedCheque>(
        `${ENDPOINTS.CASH_BOOK.UNPRESENTED_CHEQUES}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<UnpresentedCheque>) => {
      const response = await api.post<UnpresentedCheque>(
        ENDPOINTS.CASH_BOOK.UNPRESENTED_CHEQUES,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<UnpresentedCheque>) => {
      const response = await api.patch<UnpresentedCheque>(
        `${ENDPOINTS.CASH_BOOK.UNPRESENTED_CHEQUES}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.CASH_BOOK.UNPRESENTED_CHEQUES}${id}/`);
    },
  },
};

export default cashBookApi;
