/**
 * React Query Hooks for Debtors Module
 * 
 * This is the recommended pattern for data fetching.
 * Uses TanStack React Query for:
 * - Automatic caching
 * - Background refetching
 * - Optimistic updates
 * - Error handling
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api';
import { ENDPOINTS } from '../api-config';
import { queryKeys } from '../QueryProvider';
import type { 
  DebtorAccount, 
  DebtorCreateData, 
  DebtorEditData,
  PaginatedResponse,
  Transaction,
  AgeAnalysis,
  DebtorsSummary,
  DebtorFilters 
} from '../types/debtors';

// Query params type alias for backward compatibility
export type QueryParams = DebtorFilters;

// Type for API errors
export interface ApiError {
  message: string;
  status?: number;
  details?: any;
}

// Re-export queryKeys from QueryProvider for convenience
// Also provide debtorKeys alias for backward compatibility
export { queryKeys };
export const debtorKeys = queryKeys;

/**
 * Hook to fetch all debtors with pagination
 */
export function useDebtors(params: QueryParams = {}) {
  return useQuery({
    queryKey: [...queryKeys.debtors, params],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<DebtorAccount>>(
        ENDPOINTS.DEBTORS.ACCOUNTS,
        { params }
      );
      return response.data;
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
    gcTime: 1000 * 60 * 10, // 10 minutes
  });
}

/**
 * Hook to fetch a single debtor by account number
 */
export function useDebtor(dno: string) {
  return useQuery({
    queryKey: queryKeys.debtor(dno),
    queryFn: async () => {
      const response = await api.get<DebtorAccount>(
        `${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/`
      );
      return response.data;
    },
    enabled: !!dno, // Only fetch if dno is provided
    staleTime: 1000 * 60 * 5, // 5 minutes (debtor details change less frequently)
  });
}

/**
 * Hook to fetch debtor summary
 */
export function useDebtorsSummary() {
  return useQuery({
    queryKey: queryKeys.debtorsSummary,
    queryFn: async () => {
      const response = await api.get<DebtorsSummary>(ENDPOINTS.DEBTORS.SUMMARY);
      return response.data;
    },
    staleTime: 1000 * 60 * 1, // 1 minute
  });
}

/**
 * Hook to fetch debtor transactions
 */
export function useDebtorTransactions(dno: string, params: QueryParams = {}) {
  return useQuery({
    queryKey: [...queryKeys.debtorTransactions(dno), params],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Transaction>>(
        `${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/transactions/`,
        { params }
      );
      return response.data;
    },
    enabled: !!dno,
    staleTime: 1000 * 60 * 1, // 1 minute
  });
}

/**
 * Hook to fetch debtor age analysis
 */
export function useDebtorAgeAnalysis(dno: string) {
  return useQuery({
    queryKey: queryKeys.debtorAgeAnalysis(dno),
    queryFn: async () => {
      const response = await api.get<AgeAnalysis>(
        `${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/age_analysis/`
      );
      return response.data;
    },
    enabled: !!dno,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook to create a new debtor
 */
export function useCreateDebtor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: DebtorCreateData) => {
      const response = await api.post<DebtorAccount>(
        ENDPOINTS.DEBTORS.ACCOUNTS,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalidate debtors list cache
      queryClient.invalidateQueries({ queryKey: queryKeys.debtors });
      queryClient.invalidateQueries({ queryKey: queryKeys.debtorsSummary });
    },
  });
}

/**
 * Hook to update an existing debtor
 */
export function useUpdateDebtor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ dno, data }: { dno: string; data: DebtorEditData }) => {
      const response = await api.patch<DebtorAccount>(
        `${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/`,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      // Invalidate specific debtor cache
      queryClient.invalidateQueries({ queryKey: queryKeys.debtor(variables.dno) });
      queryClient.invalidateQueries({ queryKey: queryKeys.debtors });
    },
  });
}

/**
 * Hook to delete a debtor
 */
export function useDeleteDebtor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (dno: string) => {
      await api.delete(`${ENDPOINTS.DEBTORS.ACCOUNTS}${dno}/`);
    },
    onSuccess: () => {
      // Invalidate debtors list cache
      queryClient.invalidateQueries({ queryKey: queryKeys.debtors });
      queryClient.invalidateQueries({ queryKey: queryKeys.debtorsSummary });
    },
  });
}

/**
 * Hook to block/unblock a debtor
 */
export function useToggleDebtorBlock() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ dno, action }: { dno: string; action: 'block' | 'unblock' }) => {
      const endpoint = action === 'block' 
        ? ENDPOINTS.DEBTORS.BLOCK_ACCOUNT(dno)
        : ENDPOINTS.DEBTORS.UNBLOCK_ACCOUNT(dno);
      
      const response = await api.post<DebtorAccount>(endpoint);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.debtor(variables.dno) });
      queryClient.invalidateQueries({ queryKey: queryKeys.debtors });
    },
  });
}
