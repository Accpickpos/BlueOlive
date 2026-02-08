/**
 * useCreditorApi Hook
 * React hook for interacting with the Creditors API
 * Manages loading, error, and caching state automatically
 * 
 * Authentication:
 * - All endpoints require IsAuthenticated permission
 * - JWT Bearer token in Authorization header
 * - X-Tenant-ID header for multi-tenant support
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  CreditorAccount,
  Transaction,
  ExpenseCategory,
  PaginatedResponse,
  CreditorCreateData,
  CreditorEditData,
  ExpenseCategoryCreateData,
  CreditorFilters,
  CreditorsSummary,
} from '../types/creditors';
import { api } from '../api';
import { ENDPOINTS } from '../api-config';

// Type for API errors
export interface ApiError {
  message: string;
  status?: number;
  details?: any;
}

// Query params type
export type QueryParams = Record<string, any>;

/**
 * Simple API client for creditors
 */
const createCreditorsApiClient = () => ({
  async getCreditors(params: QueryParams) {
    const response = await api.get<PaginatedResponse<CreditorAccount>>(
      ENDPOINTS.CREDITORS.ACCOUNTS,
      { params }
    );
    return response.data;
  },

  async getCreditorById(id: string | number) {
    const response = await api.get<CreditorAccount>(
      `${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`
    );
    return response.data;
  },

  async getInvoices(params: QueryParams) {
    const response = await api.get<PaginatedResponse<Transaction>>(
      ENDPOINTS.CREDITORS.INVOICES,
      { params }
    );
    return response.data;
  },

  async getPayments(params: QueryParams) {
    const response = await api.get<PaginatedResponse<Transaction>>(
      ENDPOINTS.CREDITORS.PAYMENTS,
      { params }
    );
    return response.data;
  },

  async getOpenItems(params: QueryParams) {
    const response = await api.get<PaginatedResponse<Transaction>>(
      ENDPOINTS.CREDITORS.OPEN_ITEMS,
      { params }
    );
    return response.data;
  },

  async getGrns(params: QueryParams) {
    const response = await api.get<PaginatedResponse<Transaction>>(
      ENDPOINTS.CREDITORS.GRN,
      { params }
    );
    return response.data;
  },

  async getCreditorAgingAnalysis(id: string | number) {
    const response = await api.get(
      ENDPOINTS.CREDITORS.AGING_ANALYSIS(id)
    );
    return response.data;
  },

  async getSummary() {
    const response = await api.get<CreditorsSummary>(
      ENDPOINTS.CREDITORS.SUMMARY
    );
    return response.data;
  },

  async createCreditor(data: CreditorCreateData) {
    const response = await api.post<CreditorAccount>(
      ENDPOINTS.CREDITORS.ACCOUNTS,
      data
    );
    return response.data;
  },

  async updateCreditor(id: string | number, data: CreditorEditData) {
    const response = await api.patch<CreditorAccount>(
      `${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`,
      data
    );
    return response.data;
  },

  async deleteCreditor(id: string | number) {
    await api.delete(`${ENDPOINTS.CREDITORS.ACCOUNTS}${id}/`);
  },

  async createInvoice(data: any) {
    const response = await api.post<Transaction>(
      ENDPOINTS.CREDITORS.INVOICES,
      data
    );
    return response.data;
  },

  async updateInvoice(id: string | number, data: any) {
    const response = await api.patch<Transaction>(
      `${ENDPOINTS.CREDITORS.INVOICES}${id}/`,
      data
    );
    return response.data;
  },

  async createPayment(data: any) {
    const response = await api.post<Transaction>(
      ENDPOINTS.CREDITORS.PAYMENTS,
      data
    );
    return response.data;
  },

  async updatePayment(id: string | number, data: any) {
    const response = await api.patch<Transaction>(
      `${ENDPOINTS.CREDITORS.PAYMENTS}${id}/`,
      data
    );
    return response.data;
  },
});

export interface UseCreditorApiState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

export interface UseCreditorApiResponse<T> extends UseCreditorApiState<T> {
  refetch: () => Promise<void>;
  reset: () => void;
}

/**
 * Hook for fetching all creditors
 * 
 * Query Parameters:
 * - is_active: boolean
 * - account_type: 'BBF' | 'OI'
 * - search: supplier name or number
 * - ordering: field name for sorting (prefix with - for descending)
 */
export function useCreditors(
  params: QueryParams = {},
  enabled: boolean = true
): UseCreditorApiResponse<PaginatedResponse<CreditorAccount>> {
  const [state, setState] = useState<UseCreditorApiState<PaginatedResponse<CreditorAccount>>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createCreditorsApiClient();

  const refetch = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await client.getCreditors(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error as ApiError,
      });
    }
  }, [client, params]);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  useEffect(() => {
    if (enabled) {
      refetch();
    }
  }, [enabled, refetch]);

  return { ...state, refetch, reset };
}

/**
 * Hook for fetching a specific creditor by ID
 */
export function useCreditorById(id: string | number | null): UseCreditorApiResponse<CreditorAccount> {
  const [state, setState] = useState<UseCreditorApiState<CreditorAccount>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createCreditorsApiClient();

  const refetch = useCallback(async () => {
    if (!id) return;

    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await client.getCreditorById(id);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error as ApiError,
      });
    }
  }, [client, id]);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { ...state, refetch, reset };
}

/**
 * Hook for fetching creditor invoices
 */
export function useCreditorInvoices(
  params: QueryParams = {},
  enabled: boolean = true
): UseCreditorApiResponse<PaginatedResponse<Transaction>> {
  const [state, setState] = useState<UseCreditorApiState<PaginatedResponse<Transaction>>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createCreditorsApiClient();

  const refetch = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await client.getInvoices(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error as ApiError,
      });
    }
  }, [client, params]);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  useEffect(() => {
    if (enabled) {
      refetch();
    }
  }, [enabled, refetch]);

  return { ...state, refetch, reset };
}

/**
 * Hook for fetching payments to creditors
 */
export function useCreditorPayments(
  params: QueryParams = {},
  enabled: boolean = true
): UseCreditorApiResponse<PaginatedResponse<Transaction>> {
  const [state, setState] = useState<UseCreditorApiState<PaginatedResponse<Transaction>>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createCreditorsApiClient();

  const refetch = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await client.getPayments(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error as ApiError,
      });
    }
  }, [client, params]);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  useEffect(() => {
    if (enabled) {
      refetch();
    }
  }, [enabled, refetch]);

  return { ...state, refetch, reset };
}

/**
 * Hook for fetching open items (unpaid invoices)
 */
export function useCreditorOpenItems(
  params: QueryParams = {},
  enabled: boolean = true
): UseCreditorApiResponse<PaginatedResponse<Transaction>> {
  const [state, setState] = useState<UseCreditorApiState<PaginatedResponse<Transaction>>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createCreditorsApiClient();

  const refetch = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await client.getOpenItems(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error as ApiError,
      });
    }
  }, [client, params]);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  useEffect(() => {
    if (enabled) {
      refetch();
    }
  }, [enabled, refetch]);

  return { ...state, refetch, reset };
}

/**
 * Hook for fetching GRNs (Goods Received Notes)
 */
export function useGrns(
  params: QueryParams = {},
  enabled: boolean = true
): UseCreditorApiResponse<PaginatedResponse<any>> {
  const [state, setState] = useState<UseCreditorApiState<PaginatedResponse<any>>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createCreditorsApiClient();

  const refetch = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await client.getGrns(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error as ApiError,
      });
    }
  }, [client, params]);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  useEffect(() => {
    if (enabled) {
      refetch();
    }
  }, [enabled, refetch]);

  return { ...state, refetch, reset };
}

/**
 * Hook for fetching aging analysis for a creditor
 * Returns balance aging breakdown by days
 */
export function useCreditorAgingAnalysis(
  id: string | number | null
): UseCreditorApiResponse<any> {
  const [state, setState] = useState<UseCreditorApiState<any>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createCreditorsApiClient();

  const refetch = useCallback(async () => {
    if (!id) return;

    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await client.getCreditorAgingAnalysis(id);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error as ApiError,
      });
    }
  }, [client, id]);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { ...state, refetch, reset };
}

/**
 * Hook for fetching creditor summary (totals, counts, etc.)
 */
export function useCreditorsSummary(
  enabled: boolean = true
): UseCreditorApiResponse<CreditorsSummary> {
  const [state, setState] = useState<UseCreditorApiState<CreditorsSummary>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createCreditorsApiClient();

  const refetch = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await client.getSummary();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error as ApiError,
      });
    }
  }, [client]);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  useEffect(() => {
    if (enabled) {
      refetch();
    }
  }, [enabled, refetch]);

  return { ...state, refetch, reset };
}

/**
 * Hook for creditor mutations (create, update, delete)
 */
export function useCreditorMutation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const client = createCreditorsApiClient();

  const createCreditor = useCallback(
    async (data: CreditorCreateData) => {
      setLoading(true);
      setError(null);
      try {
        const result = await client.createCreditor(data);
        setLoading(false);
        return result;
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError);
        setLoading(false);
        throw apiError;
      }
    },
    [client]
  );

  const updateCreditor = useCallback(
    async (id: string | number, data: CreditorEditData) => {
      setLoading(true);
      setError(null);
      try {
        const result = await client.updateCreditor(id, data);
        setLoading(false);
        return result;
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError);
        setLoading(false);
        throw apiError;
      }
    },
    [client]
  );

  const deleteCreditor = useCallback(
    async (id: string | number) => {
      setLoading(true);
      setError(null);
      try {
        await client.deleteCreditor(id);
        setLoading(false);
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError);
        setLoading(false);
        throw apiError;
      }
    },
    [client]
  );

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
  }, []);

  return {
    loading,
    error,
    createCreditor,
    updateCreditor,
    deleteCreditor,
    reset,
  };
}

/**
 * Hook for invoice mutations (create, update, delete)
 */
export function useInvoiceMutation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const client = createCreditorsApiClient();

  const createInvoice = useCallback(
    async (data: any) => {
      setLoading(true);
      setError(null);
      try {
        const result = await client.createInvoice(data);
        setLoading(false);
        return result;
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError);
        setLoading(false);
        throw apiError;
      }
    },
    [client]
  );

  const updateInvoice = useCallback(
    async (id: string | number, data: Partial<any>) => {
      setLoading(true);
      setError(null);
      try {
        const result = await client.updateInvoice(id, data);
        setLoading(false);
        return result;
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError);
        setLoading(false);
        throw apiError;
      }
    },
    [client]
  );

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
  }, []);

  return {
    loading,
    error,
    createInvoice,
    updateInvoice,
    reset,
  };
}

/**
 * Hook for payment mutations (create, update)
 */
export function usePaymentMutation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const client = createCreditorsApiClient();

  const createPayment = useCallback(
    async (data: any) => {
      setLoading(true);
      setError(null);
      try {
        const result = await client.createPayment(data);
        setLoading(false);
        return result;
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError);
        setLoading(false);
        throw apiError;
      }
    },
    [client]
  );

  const updatePayment = useCallback(
    async (id: string | number, data: Partial<any>) => {
      setLoading(true);
      setError(null);
      try {
        const result = await client.updatePayment(id, data);
        setLoading(false);
        return result;
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError);
        setLoading(false);
        throw apiError;
      }
    },
    [client]
  );

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
  }, []);

  return {
    loading,
    error,
    createPayment,
    updatePayment,
    reset,
  };
}
