/**
 * Creditors API Client
 * RESTful API wrapper for creditor management endpoints
 * 
 * Base URL: /api/v1/creditors/
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
  ExpenseCategory,
  ExpenseCategoryCreateData,
  Transaction,
  TransactionCreateData,
  TransactionFilters,
  CreditorFilters,
  ExpenseCategoryFilters,
  CreditorsSummary,
  PaginatedResponse,
} from './types/creditors';

/**
 * Supplier type - represents a creditor/supplier account
 */
export interface Supplier extends CreditorAccount {
  supplier_number: string;
  short_name?: string;
  physical_address_line1?: string;
  physical_address_line2?: string;
  physical_address_line3?: string;
  physical_city?: string;
  physical_postal_code?: string;
  postal_address_line1?: string;
  postal_address_line2?: string;
  postal_address_line3?: string;
  postal_city?: string;
  postal_postal_code?: string;
  telephone1?: string;
  telephone2?: string;
  vat_number?: string;
  update_selling_price_on_receipt?: boolean;
  prompt_payment_discount_percent?: number;
}

/**
 * Supplier create/edit data
 */
export interface SupplierCreateData extends Partial<Supplier> {
  supplier_number: string;
  account_number: string;
  name: string;
  short_name?: string;
  physical_address_line1?: string;
  physical_address_line2?: string;
  physical_address_line3?: string;
  physical_city?: string;
  physical_postal_code?: string;
  postal_address_line1?: string;
  postal_address_line2?: string;
  postal_address_line3?: string;
  postal_city?: string;
  postal_postal_code?: string;
  telephone1?: string;
  telephone2?: string;
  fax?: string;
  email?: string;
  contact_person?: string;
  account_type?: 'BBF' | 'OPEN_ITEM';
  our_account_number?: string;
  credit_terms?: number | null;
  prompt_payment_discount_percent?: number;
  bank_name?: string;
  bank_branch_code?: string;
  bank_account_number?: string;
  vat_number?: string;
  update_selling_price_on_receipt?: boolean;
  is_active?: boolean;
}

/**
 * Credit terms option
 */
export interface CreditTermsOption {
  id: number;
  name: string;
  days?: number;
}

/**
 * Outstanding balance capture
 */
export interface OutstandingBalance {
  id: number;
  supplier_id: number;
  capture_date: string;
  balance_current: number;
  balance_30_days: number;
  balance_60_days: number;
  balance_90_days: number;
  balance_120_days: number;
  balance_150_days: number;
  balance_180_days: number;
  created_at?: string;
  updated_at?: string;
}

/**
 * Outstanding balance capture data for form
 */
export interface OutstandingBalanceCaptureData {
  supplier_account_number: number | string;
  capture_date: string;
  balance_current: number;
  balance_30_days: number;
  balance_60_days: number;
  balance_90_days: number;
  balance_120_days: number;
  balance_150_days: number;
  balance_180_days: number;
}

/**
 * Outstanding balance filters
 */
export interface OutstandingBalanceFilters {
  supplier_id?: number;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

// ============ RE-EXPORT TYPES FROM types/creditors ============
export type { ExpenseCategory, ExpenseCategoryCreateData };

export const creditorsApi = {
  // ============ ACCOUNTS ============
  accounts: {
    list: async (filters?: CreditorFilters) => {
      const response = await api.get<PaginatedResponse<CreditorAccount>>(
        ENDPOINTS.CREDITORS.ACCOUNTS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: string | number) => {
      const response = await api.get<CreditorAccount>(
        `${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`
      );
      return response.data;
    },

    create: async (data: CreditorCreateData) => {
      const response = await api.post<CreditorAccount>(
        ENDPOINTS.CREDITORS.ACCOUNTS,
        data
      );
      return response.data;
    },

    update: async (id: string | number, data: CreditorEditData) => {
      const response = await api.patch<CreditorAccount>(
        `${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`,
        data
      );
      return response.data;
    },

    updateBalance: async (
      id: string | number,
      data: { balance: number; transaction_type: string }
    ) => {
      const response = await api.patch<CreditorAccount>(
        `${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`);
    },
  },

  // ============ TRANSACTIONS ============
  transactions: {
    list: async (filters?: TransactionFilters) => {
      const response = await api.get<PaginatedResponse<Transaction>>(
        ENDPOINTS.CREDITORS.TRANSACTIONS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: string | number) => {
      const response = await api.get<Transaction>(
        `${ENDPOINTS.CREDITORS.TRANSACTIONS}${id}/`
      );
      return response.data;
    },

    create: async (data: TransactionCreateData) => {
      const response = await api.post<Transaction>(
        ENDPOINTS.CREDITORS.TRANSACTIONS,
        data
      );
      return response.data;
    },

    update: async (id: string | number, data: Partial<TransactionCreateData>) => {
      const response = await api.patch<Transaction>(
        `${ENDPOINTS.CREDITORS.TRANSACTIONS}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.TRANSACTIONS}${id}/`);
    },
  },

  // ============ EXPENSE CATEGORIES ============
  // Now handled by Settings API - see settingsApi.ts
  // This avoids duplication and centralizes category management in the settings app

  // ============ GOODS RECEIVED NOTES (GRN) ============
  grn: {
    list: async (filters?: any) => {
      const response = await api.get(
        ENDPOINTS.CREDITORS.GRN,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: string | number) => {
      const response = await api.get(`${ENDPOINTS.CREDITORS.GRN}${id}/`);
      return response.data;
    },

    create: async (data: any) => {
      const response = await api.post(ENDPOINTS.CREDITORS.GRN, data);
      return response.data;
    },

    update: async (id: string | number, data: any) => {
      const response = await api.patch(`${ENDPOINTS.CREDITORS.GRN}${id}/`, data);
      return response.data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.GRN}${id}/`);
    },
  },

  // ============ INVOICES ============
  invoices: {
    list: async (filters?: any) => {
      const response = await api.get(
        ENDPOINTS.CREDITORS.INVOICES,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: string | number) => {
      const response = await api.get(`${ENDPOINTS.CREDITORS.INVOICES}${id}/`);
      return response.data;
    },

    create: async (data: any) => {
      const response = await api.post(ENDPOINTS.CREDITORS.INVOICES, data);
      return response.data;
    },

    update: async (id: string | number, data: any) => {
      const response = await api.patch(`${ENDPOINTS.CREDITORS.INVOICES}${id}/`, data);
      return response.data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.INVOICES}${id}/`);
    },
  },

  // ============ PAYMENTS ============
  payments: {
    list: async (filters?: any) => {
      const response = await api.get(
        ENDPOINTS.CREDITORS.PAYMENTS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: string | number) => {
      const response = await api.get(`${ENDPOINTS.CREDITORS.PAYMENTS}${id}/`);
      return response.data;
    },

    create: async (data: any) => {
      const response = await api.post(ENDPOINTS.CREDITORS.PAYMENTS, data);
      return response.data;
    },

    update: async (id: string | number, data: any) => {
      const response = await api.patch(`${ENDPOINTS.CREDITORS.PAYMENTS}${id}/`, data);
      return response.data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.PAYMENTS}${id}/`);
    },
  },

  // ============ JOURNALS ============
  journals: {
    list: async (filters?: any) => {
      const response = await api.get(
        ENDPOINTS.CREDITORS.JOURNALS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: string | number) => {
      const response = await api.get(`${ENDPOINTS.CREDITORS.JOURNALS}${id}/`);
      return response.data;
    },

    create: async (data: any) => {
      const response = await api.post(ENDPOINTS.CREDITORS.JOURNALS, data);
      return response.data;
    },

    update: async (id: string | number, data: any) => {
      const response = await api.patch(`${ENDPOINTS.CREDITORS.JOURNALS}${id}/`, data);
      return response.data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.JOURNALS}${id}/`);
    },
  },

  // ============ OPEN ITEMS ============
  openItems: {
    list: async (filters?: any) => {
      const response = await api.get(
        ENDPOINTS.CREDITORS.OPEN_ITEMS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: string | number) => {
      const response = await api.get(`${ENDPOINTS.CREDITORS.OPEN_ITEMS}${id}/`);
      return response.data;
    },
  },

  // ============ RFC (REQUEST FOR CREDIT) ============
  rfc: {
    list: async (filters?: any) => {
      const response = await api.get(
        ENDPOINTS.CREDITORS.RFC,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: string | number) => {
      const response = await api.get(`${ENDPOINTS.CREDITORS.RFC}${id}/`);
      return response.data;
    },

    create: async (data: any) => {
      const response = await api.post(ENDPOINTS.CREDITORS.RFC, data);
      return response.data;
    },

    update: async (id: string | number, data: any) => {
      const response = await api.patch(`${ENDPOINTS.CREDITORS.RFC}${id}/`, data);
      return response.data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.RFC}${id}/`);
    },
  },

  // ============ SUMMARY/DASHBOARD ============
  summary: {
    get: async (params?: { cutoff_date?: string }) => {
      const response = await api.get<CreditorsSummary>(
        ENDPOINTS.CREDITORS.SUMMARY,
        { params }
      );
      return response.data;
    },
  },
};

/**
 * React hook for using the Creditors API
 * Provides convenient methods for supplier, expense category, and outstanding balance management
 */
export function useCreditorsAPI() {
  // ============ SUPPLIER OPERATIONS ============
  const listSuppliers = useCallback(async (filters?: CreditorFilters) => {
    const response = await creditorsApi.accounts.list(filters);
    return response.results as Supplier[];
  }, []);

  const createSupplier = useCallback(async (data: SupplierCreateData): Promise<Supplier> => {
    return creditorsApi.accounts.create(data as CreditorCreateData) as Promise<Supplier>;
  }, []);

  const updateSupplier = useCallback(async (supplierNumber: string | number, data: Partial<SupplierCreateData>): Promise<Supplier> => {
    return creditorsApi.accounts.update(supplierNumber, data as CreditorEditData) as Promise<Supplier>;
  }, []);

  const deleteSupplier = useCallback(async (supplierNumber: string | number) => {
    return creditorsApi.accounts.delete(supplierNumber);
  }, []);

  // ============ CREDIT TERMS OPERATIONS ============
  const listCreditTerms = useCallback(async (): Promise<CreditTermsOption[]> => {
    try {
      // Try to fetch from API endpoint if available
      const response = await api.get<PaginatedResponse<CreditTermsOption>>(
        ENDPOINTS.CREDITORS.CREDIT_TERMS || '/api/v1/creditors/credit-terms/',
        {}
      );
      return response.data.results || [];
    } catch (error) {
      console.warn('Failed to fetch credit terms from API:', error);
      // Return default/empty list if endpoint doesn't exist
      return [];
    }
  }, []);

  // ============ EXPENSE CATEGORY OPERATIONS ============
  // Delegated to Settings API to avoid duplication
  const listExpenseCategories = useCallback(async (filters?: ExpenseCategoryFilters) => {
    const response = await settingsApi.expenseCategories.list(filters);
    return response.results as ExpenseCategory[];
  }, []);

  const createExpenseCategory = useCallback(async (data: any): Promise<ExpenseCategory> => {
    return settingsApi.expenseCategories.create(data);
  }, []);

  const updateExpenseCategory = useCallback(async (id: number | string, data: Partial<ExpenseCategoryCreateData>): Promise<ExpenseCategory> => {
    return settingsApi.expenseCategories.update(id, data);
  }, []);

  const deleteExpenseCategory = useCallback(async (id: number | string) => {
    return settingsApi.expenseCategories.delete(id);
  }, []);

  // ============ OUTSTANDING BALANCE OPERATIONS ============
  const listOutstandingBalances = useCallback(async (filters?: OutstandingBalanceFilters) => {
    try {
      const response = await api.get<PaginatedResponse<OutstandingBalance>>(
        ENDPOINTS.CREDITORS.OUTSTANDING_BALANCE || '/api/v1/creditors/creditors/outstanding-balance/',
        { params: filters }
      );
      
      // Calculate total outstanding balance
      const items = response.data.results || [];
      const totalOutstanding = items.reduce((sum: number, item: OutstandingBalance) => {
        return sum + (item.balance_current || 0);
      }, 0);
      
      return {
        items,
        count: response.data.count || items.length,
        total_outstanding: totalOutstanding,
        next: response.data.next,
        previous: response.data.previous
      };
    } catch (error) {
      console.error('Failed to fetch outstanding balances:', error);
      return {
        items: [],
        count: 0,
        total_outstanding: 0,
        next: null,
        previous: null
      };
    }
  }, []);

  const captureOutstandingBalance = useCallback(async (data: OutstandingBalanceCaptureData): Promise<OutstandingBalance> => {
    const response = await api.post<OutstandingBalance>(
      ENDPOINTS.CREDITORS.OUTSTANDING_BALANCE || '/api/v1/creditors/creditors/outstanding-balance/',
      data
    );
    return response.data;
  }, []);

  const updateOutstandingBalance = useCallback(async (id: number | string, data: Partial<OutstandingBalanceCaptureData>): Promise<OutstandingBalance> => {
    const response = await api.patch<OutstandingBalance>(
      `${ENDPOINTS.CREDITORS.OUTSTANDING_BALANCE || '/api/v1/creditors/creditors/outstanding-balance/'}${id}/`,
      data
    );
    return response.data;
  }, []);

  const deleteOutstandingBalance = useCallback(async (id: number | string) => {
    return api.delete(`${ENDPOINTS.CREDITORS.OUTSTANDING_BALANCE || '/api/v1/creditors/creditors/outstanding-balance/'}${id}/`);
  }, []);

  // Return the API object with all methods
  return {
    listSuppliers,
    createSupplier,
    updateSupplier,
    deleteSupplier,
    listCreditTerms,
    listExpenseCategories,
    createExpenseCategory,
    updateExpenseCategory,
    deleteExpenseCategory,
    listOutstandingBalances,
    captureOutstandingBalance,
    updateOutstandingBalance,
    deleteOutstandingBalance,
  };
}

export default creditorsApi;
