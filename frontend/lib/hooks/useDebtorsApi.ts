/**
 * useDebtorsApi Hook
 * React hook for interacting with the Debtors API
 * Manages loading, error, and caching state automatically
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
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
} from '../types/debtors';
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
 * Simple API client for debtors
 */
const createDebtorsApiClient = () => ({
  async getDebtors(params: QueryParams) {
    const response = await api.get<PaginatedResponse<DebtorAccount>>(
      ENDPOINTS.DEBTORS.ACCOUNTS,
      { params }
    );
    return response.data;
  },

  async getDebtorById(dno: string) {
    const response = await api.get<DebtorAccount>(
      `${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/`
    );
    return response.data;
  },

  async getTransactions(params: QueryParams) {
    const response = await api.get<PaginatedResponse<Transaction>>(
      ENDPOINTS.DEBTORS.TRANSACTIONS,
      { params }
    );
    return response.data;
  },

  async getOpenItems(params: QueryParams) {
    const response = await api.get<PaginatedResponse<OpenItem>>(
      ENDPOINTS.DEBTORS.OPEN_ITEMS,
      { params }
    );
    return response.data;
  },

  async getAgeAnalysis(dno: string, params?: QueryParams) {
    const response = await api.get<AgeAnalysis>(
      `${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/age-analysis/`,
      { params }
    );
    return response.data;
  },

  async getSummary() {
    const response = await api.get<DebtorsSummary>(
      ENDPOINTS.DEBTORS.SUMMARY
    );
    return response.data;
  },

  async createDebtor(data: DebtorCreateData) {
    const response = await api.post<DebtorAccount>(
      ENDPOINTS.DEBTORS.ACCOUNTS,
      data
    );
    return response.data;
  },

  async updateDebtor(dno: string, data: DebtorEditData) {
    const response = await api.patch<DebtorAccount>(
      `${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/`,
      data
    );
    return response.data;
  },

  async deleteDebtor(dno: string) {
    await api.delete(`${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/`);
  },

  async createTransaction(data: TransactionCreateData) {
    const response = await api.post<Transaction>(
      ENDPOINTS.DEBTORS.TRANSACTIONS,
      data
    );
    return response.data;
  },

  async updateTransaction(id: number, data: Partial<TransactionCreateData>) {
    const response = await api.patch<Transaction>(
      `${ENDPOINTS.DEBTORS.TRANSACTIONS}${id}/`,
      data
    );
    return response.data;
  },

  async deleteTransaction(id: number) {
    await api.delete(`${ENDPOINTS.DEBTORS.TRANSACTIONS}${id}/`);
  },

  async createPostDatedCheque(data: PostDatedChequeCreateData) {
    const response = await api.post<PostDatedCheque>(
      ENDPOINTS.DEBTORS.POST_DATED_CHEQUES,
      data
    );
    return response.data;
  },

  async updatePostDatedCheque(id: number, data: Partial<PostDatedChequeCreateData>) {
    const response = await api.patch<PostDatedCheque>(
      `${ENDPOINTS.DEBTORS.POST_DATED_CHEQUES}${id}/`,
      data
    );
    return response.data;
  },

  async deletePostDatedCheque(id: number) {
    await api.delete(`${ENDPOINTS.DEBTORS.POST_DATED_CHEQUES}${id}/`);
  },

  // Additional methods for debtor-specific operations
  async getDebtorTransactions(dno: string, params: QueryParams) {
    const response = await api.get<PaginatedResponse<Transaction>>(
      `${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/transactions/`,
      { params }
    );
    return response.data;
  },

  async getBalanceDetails(dno: string) {
    const response = await api.get(
      `${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/balance-details/`
    );
    return response.data;
  },

  async blockDebtor(dno: string, reason?: string) {
    const response = await api.post<DebtorAccount>(
      `${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/block/`,
      { reason }
    );
    return response.data;
  },

  async unblockDebtor(dno: string, reason?: string) {
    const response = await api.post<DebtorAccount>(
      `${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/unblock/`,
      { reason }
    );
    return response.data;
  },
});

export interface UseDebtorsApiState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

export interface UseDebtorsApiResponse<T> extends UseDebtorsApiState<T> {
  refetch: () => Promise<void>;
  reset: () => void;
}

/**
 * Hook for fetching debtor accounts
 */
export function useDebtors(
  params: QueryParams = {},
  enabled: boolean = true
): UseDebtorsApiResponse<PaginatedResponse<DebtorAccount>> {
  const [state, setState] = useState<UseDebtorsApiState<PaginatedResponse<DebtorAccount>>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createDebtorsApiClient();

  const refetch = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await client.getDebtors(params);
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
 * Hook for fetching a specific debtor by ID
 */
export function useDebtorById(dno: string): UseDebtorsApiResponse<DebtorAccount> {
  const [state, setState] = useState<UseDebtorsApiState<DebtorAccount>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createDebtorsApiClient();

  const refetch = useCallback(async () => {
    if (!dno) return;

    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await client.getDebtorById(dno);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error as ApiError,
      });
    }
  }, [client, dno]);

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
 * Hook for debtor transactions
 */
export function useTransactions(
  dno: string,
  params: QueryParams = {}
): UseDebtorsApiResponse<PaginatedResponse<Transaction>> {
  const [state, setState] = useState<UseDebtorsApiState<PaginatedResponse<Transaction>>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createDebtorsApiClient();

  const refetch = useCallback(async () => {
    if (!dno) return;

    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await client.getDebtorTransactions(dno, params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error as ApiError,
      });
    }
  }, [client, dno, params]);

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
 * Hook for open items
 */
export function useOpenItems(
  params: QueryParams = {},
  enabled: boolean = true
): UseDebtorsApiResponse<PaginatedResponse<OpenItem>> {
  const [state, setState] = useState<UseDebtorsApiState<PaginatedResponse<OpenItem>>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createDebtorsApiClient();

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
 * Hook for age analysis
 */
export function useAgeAnalysis(dno: string): UseDebtorsApiResponse<any> {
  const [state, setState] = useState<UseDebtorsApiState<any>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createDebtorsApiClient();

  const refetch = useCallback(async () => {
    if (!dno) return;

    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await client.getAgeAnalysis(dno);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error as ApiError,
      });
    }
  }, [client, dno]);

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
 * Hook for balance details
 */
export function useBalanceDetails(dno: string): UseDebtorsApiResponse<any> {
  const [state, setState] = useState<UseDebtorsApiState<any>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createDebtorsApiClient();

  const refetch = useCallback(async () => {
    if (!dno) return;

    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await client.getBalanceDetails(dno);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error as ApiError,
      });
    }
  }, [client, dno]);

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
 * Hook for debtor summary
 */
export function useDebtorsSummary(
  enabled: boolean = true
): UseDebtorsApiResponse<any> {
  const [state, setState] = useState<UseDebtorsApiState<any>>({
    data: null,
    loading: false,
    error: null,
  });

  const client = createDebtorsApiClient();

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
 * Hook for mutations (create, update, delete)
 */
export function useDebtorMutation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const client = createDebtorsApiClient();

  const createDebtor = useCallback(
    async (data: DebtorCreateData) => {
      setLoading(true);
      setError(null);
      try {
        const result = await client.createDebtor(data);
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

  const updateDebtor = useCallback(
    async (dno: string, data: Partial<DebtorAccount>) => {
      setLoading(true);
      setError(null);
      try {
        const result = await client.updateDebtor(dno, data);
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

  const deleteDebtor = useCallback(
    async (dno: string) => {
      setLoading(true);
      setError(null);
      try {
        await client.deleteDebtor(dno);
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

  const blockDebtor = useCallback(
    async (dno: string, reason?: string) => {
      setLoading(true);
      setError(null);
      try {
        const result = await client.blockDebtor(dno, reason);
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

  const unblockDebtor = useCallback(
    async (dno: string, reason?: string) => {
      setLoading(true);
      setError(null);
      try {
        const result = await client.unblockDebtor(dno, reason);
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
    createDebtor,
    updateDebtor,
    deleteDebtor,
    blockDebtor,
    unblockDebtor,
    reset,
  };
}
