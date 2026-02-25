/**
 * useDebtorsApi Hook - DEPRECATED
 * 
 * This file re-exports from the React Query implementation for backward compatibility.
 * 
 * @deprecated Use useReactQueryDebtors from './useReactQueryDebtors' instead
 * 
 * Migration Guide:
 * ----------------
 * 
 * BEFORE (old):
 *   import { useDebtors, useDebtor } from '@/lib/hooks/useDebtorsApi';
 *   
 *   function MyComponent() {
 *     const { data, isLoading } = useDebtors({ page: 1 });
 *     const debtor = useDebtor('D001');
 *   }
 * 
 * AFTER (new):
 *   import { useDebtors, useDebtor, queryKeys } from '@/lib/hooks/useReactQueryDebtors';
 *   
 *   function MyComponent() {
 *     const { data, isLoading } = useDebtors({ page: 1 });
 *     const debtor = useDebtor('D001');
 *   }
 * 
 * Benefits of migration:
 * - Centralized query key management via queryKeys
 * - Automatic cache invalidation
 * - Optimized staleTime settings
 * - Better TypeScript support
 */

'use client';

// Re-export all hooks from React Query version for backward compatibility
export {
  useDebtors,
  useDebtor,
  useDebtorsSummary,
  useDebtorTransactions,
  useDebtorAgeAnalysis,
  useCreateDebtor,
  useUpdateDebtor,
  useDeleteDebtor,
  useToggleDebtorBlock,
  debtorKeys,
} from './useReactQueryDebtors';

// Also export the types and utilities
export type { ApiError, QueryParams } from './useReactQueryDebtors';
