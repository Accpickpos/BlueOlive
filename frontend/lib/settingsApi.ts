/**
 * Settings API Client
 * 
 * Handles all system settings and configuration endpoints:
 * - Departments
 * - Sales Areas
 * - Categories (Income, Expense)
 * - Tax Codes
 * - Payment Methods
 * - Credit Terms
 * - System Configuration
 * - Statistics
 * - Import utilities
 * 
 * Base URL: /api/v1/settings/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';
import { PaginatedResponse } from './types/creditors';

export interface Department {
  id?: number;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at?: string;
  [key: string]: any;
}

export interface SalesArea {
  id?: number;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at?: string;
  [key: string]: any;
}

export interface IncomeCategory {
  id?: number;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at?: string;
  [key: string]: any;
}

export interface ExpenseCategory {
  id: number;
  category_number?: string;
  number?: number;
  name: string;
  description?: string;
  category_type?: string;
  is_active: boolean;
  transaction_count?: number;
  total_amount?: number;
  total_tax?: number;
  total_mtd?: number;
  total_ytd?: number;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface TaxCode {
  id?: number;
  code: string;
  name: string;
  rate: number;
  description?: string;
  is_active: boolean;
  created_at?: string;
  [key: string]: any;
}

export interface CostingCategory {
  id?: number;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at?: string;
  [key: string]: any;
}

export interface PaymentMethod {
  id?: number;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at?: string;
  [key: string]: any;
}

export interface CreditTerms {
  id?: number;
  code: string;
  name: string;
  days: number;
  description?: string;
  is_active: boolean;
  created_at?: string;
  [key: string]: any;
}

export interface SystemConfig {
  id?: number;
  key: string;
  value: any;
  description?: string;
  created_at?: string;
  [key: string]: any;
}

export const settingsApi = {
  // ============ DEPARTMENTS ============
  departments: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: Department[] }>(
        ENDPOINTS.SETTINGS.DEPARTMENTS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<Department>(
        `${ENDPOINTS.SETTINGS.DEPARTMENTS}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<Department>) => {
      const response = await api.post<Department>(
        ENDPOINTS.SETTINGS.DEPARTMENTS,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<Department>) => {
      const response = await api.patch<Department>(
        `${ENDPOINTS.SETTINGS.DEPARTMENTS}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.SETTINGS.DEPARTMENTS}${id}/`);
    },
  },

  // ============ SALES AREAS ============
  salesAreas: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: SalesArea[] }>(
        ENDPOINTS.SETTINGS.SALES_AREAS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<SalesArea>(
        `${ENDPOINTS.SETTINGS.SALES_AREAS}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<SalesArea>) => {
      const response = await api.post<SalesArea>(
        ENDPOINTS.SETTINGS.SALES_AREAS,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<SalesArea>) => {
      const response = await api.patch<SalesArea>(
        `${ENDPOINTS.SETTINGS.SALES_AREAS}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.SETTINGS.SALES_AREAS}${id}/`);
    },
  },

  // ============ INCOME CATEGORIES ============
  incomeCategories: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: IncomeCategory[] }>(
        ENDPOINTS.SETTINGS.INCOME_CATEGORIES,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<IncomeCategory>(
        `${ENDPOINTS.SETTINGS.INCOME_CATEGORIES}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<IncomeCategory>) => {
      const response = await api.post<IncomeCategory>(
        ENDPOINTS.SETTINGS.INCOME_CATEGORIES,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<IncomeCategory>) => {
      const response = await api.patch<IncomeCategory>(
        `${ENDPOINTS.SETTINGS.INCOME_CATEGORIES}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.SETTINGS.INCOME_CATEGORIES}${id}/`);
    },
  },

  // ============ EXPENSE CATEGORIES ============
  expenseCategories: {
    list: async (filters?: any) => {
      const response = await api.get<PaginatedResponse<ExpenseCategory>>(
        ENDPOINTS.SETTINGS.EXPENSE_CATEGORIES,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<ExpenseCategory>(
        `${ENDPOINTS.SETTINGS.EXPENSE_CATEGORIES}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<ExpenseCategory>) => {
      const response = await api.post<ExpenseCategory>(
        ENDPOINTS.SETTINGS.EXPENSE_CATEGORIES,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<ExpenseCategory>) => {
      const response = await api.patch<ExpenseCategory>(
        `${ENDPOINTS.SETTINGS.EXPENSE_CATEGORIES}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.SETTINGS.EXPENSE_CATEGORIES}${id}/`);
    },
  },

  // ============ TAX CODES ============
  taxCodes: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: TaxCode[] }>(
        ENDPOINTS.SETTINGS.TAX_CODES,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<TaxCode>(
        `${ENDPOINTS.SETTINGS.TAX_CODES}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<TaxCode>) => {
      const response = await api.post<TaxCode>(
        ENDPOINTS.SETTINGS.TAX_CODES,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<TaxCode>) => {
      const response = await api.patch<TaxCode>(
        `${ENDPOINTS.SETTINGS.TAX_CODES}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.SETTINGS.TAX_CODES}${id}/`);
    },
  },

  // ============ COSTING CATEGORIES ============
  costingCategories: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: CostingCategory[] }>(
        ENDPOINTS.SETTINGS.COSTING_CATEGORIES,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<CostingCategory>(
        `${ENDPOINTS.SETTINGS.COSTING_CATEGORIES}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<CostingCategory>) => {
      const response = await api.post<CostingCategory>(
        ENDPOINTS.SETTINGS.COSTING_CATEGORIES,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<CostingCategory>) => {
      const response = await api.patch<CostingCategory>(
        `${ENDPOINTS.SETTINGS.COSTING_CATEGORIES}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.SETTINGS.COSTING_CATEGORIES}${id}/`);
    },
  },

  // ============ PAYMENT METHODS ============
  paymentMethods: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: PaymentMethod[] }>(
        ENDPOINTS.SETTINGS.PAYMENT_METHODS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<PaymentMethod>(
        `${ENDPOINTS.SETTINGS.PAYMENT_METHODS}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<PaymentMethod>) => {
      const response = await api.post<PaymentMethod>(
        ENDPOINTS.SETTINGS.PAYMENT_METHODS,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<PaymentMethod>) => {
      const response = await api.patch<PaymentMethod>(
        `${ENDPOINTS.SETTINGS.PAYMENT_METHODS}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.SETTINGS.PAYMENT_METHODS}${id}/`);
    },
  },

  // ============ CREDIT TERMS ============
  creditTerms: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: CreditTerms[] }>(
        ENDPOINTS.SETTINGS.CREDIT_TERMS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<CreditTerms>(
        `${ENDPOINTS.SETTINGS.CREDIT_TERMS}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<CreditTerms>) => {
      const response = await api.post<CreditTerms>(
        ENDPOINTS.SETTINGS.CREDIT_TERMS,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<CreditTerms>) => {
      const response = await api.patch<CreditTerms>(
        `${ENDPOINTS.SETTINGS.CREDIT_TERMS}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.SETTINGS.CREDIT_TERMS}${id}/`);
    },
  },

  // ============ SYSTEM CONFIG ============
  systemConfig: {
    list: async () => {
      const response = await api.get<{ results: SystemConfig[] }>(
        ENDPOINTS.SETTINGS.SYSTEM_CONFIG
      );
      return response.data;
    },

    get: async (key: string) => {
      const response = await api.get<SystemConfig>(
        `${ENDPOINTS.SETTINGS.SYSTEM_CONFIG}${key}/`
      );
      return response.data;
    },

    create: async (data: Partial<SystemConfig>) => {
      const response = await api.post<SystemConfig>(
        ENDPOINTS.SETTINGS.SYSTEM_CONFIG,
        data
      );
      return response.data;
    },

    update: async (key: string, data: Partial<SystemConfig>) => {
      const response = await api.patch<SystemConfig>(
        `${ENDPOINTS.SETTINGS.SYSTEM_CONFIG}${key}/`,
        data
      );
      return response.data;
    },

    delete: async (key: string) => {
      await api.delete(`${ENDPOINTS.SETTINGS.SYSTEM_CONFIG}${key}/`);
    },
  },

  // ============ DEPARTMENT STATS ============
  departmentStats: {
    list: async (filters?: any) => {
      const response = await api.get(
        ENDPOINTS.SETTINGS.DEPARTMENT_STATS,
        { params: filters }
      );
      return response.data;
    },

    get: async (departmentId: number | string) => {
      const response = await api.get(
        `${ENDPOINTS.SETTINGS.DEPARTMENT_STATS}${departmentId}/`
      );
      return response.data;
    },
  },

  // ============ SALES AREA STATS ============
  salesAreaStats: {
    list: async (filters?: any) => {
      const response = await api.get(
        ENDPOINTS.SETTINGS.SALES_AREA_STATS,
        { params: filters }
      );
      return response.data;
    },

    get: async (areaId: number | string) => {
      const response = await api.get(
        `${ENDPOINTS.SETTINGS.SALES_AREA_STATS}${areaId}/`
      );
      return response.data;
    },
  },

  // ============ IMPORT ============
  import: {
    /**
     * Import data from file
     */
    importData: async (file: File, importType: string) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('import_type', importType);

      const response = await api.post(
        ENDPOINTS.SETTINGS.IMPORT,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;
    },

    /**
     * Get import status
     */
    getStatus: async (importId: number | string) => {
      const response = await api.get(
        `${ENDPOINTS.SETTINGS.IMPORT}${importId}/`
      );
      return response.data;
    },
  },
};

export default settingsApi;
