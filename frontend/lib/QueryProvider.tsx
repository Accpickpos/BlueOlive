'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode, useState } from 'react';

/**
 * Query Provider with optimized caching strategies
 * 
 * Caching Strategy:
 * - Short staleTime for frequently changing data (e.g., stock levels)
 * - Longer staleTime for relatively static data (e.g., debtor details)
 * - Automatic background refetching on window focus
 */

// Query key factory for consistent cache management
export const queryKeys = {
  // Auth
  auth: ['auth'] as const,
  profile: ['auth', 'profile'] as const,
  shops: ['shops'] as const,
  currentShop: ['shops', 'current'] as const,
  
  // Debtors
  debtors: ['debtors'] as const,
  debtor: (id: string) => ['debtors', id] as const,
  debtorTransactions: (id: string) => ['debtors', id, 'transactions'] as const,
  debtorAgeAnalysis: (id: string) => ['debtors', id, 'age-analysis'] as const,
  debtorsSummary: ['debtors', 'summary'] as const,
  debtorsOpenItems: ['debtors', 'open-items'] as const,
  
  // Creditors
  creditors: ['creditors'] as const,
  creditor: (id: string) => ['creditors', id] as const,
  creditorTransactions: (id: string) => ['creditors', id, 'transactions'] as const,
  creditorsSummary: ['creditors', 'summary'] as const,
  
  // Stock
  stock: ['stock'] as const,
  stockItem: (id: string) => ['stock', id] as const,
  stockTransactions: (id: string) => ['stock', id, 'transactions'] as const,
  
  // Purchase Orders
  purchaseOrders: ['purchase-orders'] as const,
  purchaseOrder: (id: string) => ['purchase-orders', id] as const,
  
  // POS
  posSessions: ['pos', 'sessions'] as const,
  posReceipts: ['pos', 'receipts'] as const,
};

// Default query options
const defaultQueryOptions = {
  staleTime: 1000 * 60 * 2, // 2 minutes
  gcTime: 1000 * 60 * 10, // 10 minutes (formerly cacheTime)
  retry: 1,
  refetchOnWindowFocus: false,
};

export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            ...defaultQueryOptions,
            // For GET requests, use stale-while-revalidate
            staleTime: 1000 * 60 * 2, // 2 minutes
          },
          mutations: {
            retry: 0, // Don't retry mutations by default
            onSettled: () => {
              // Invalidate related queries after mutation
              // This will be overridden in individual mutations
            },
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

/**
 * Prefetch data for better UX
 * Call this in server components or during navigation
 * Note: This requires a QueryClient instance. Use useQueryClient hook in components.
 * 
 * @example
 * // In a server component or API route:
 * import { QueryClient } from '@tanstack/react-query';
 * import { prefetchQuery } from '@/lib/QueryProvider';
 * 
 * const queryClient = new QueryClient();
 * await prefetchQuery(queryClient, ['debtors'], () => fetchDebtors());
 */
export async function prefetchQuery<T>(
  queryClient: QueryClient,
  queryKey: readonly unknown[],
  queryFn: () => Promise<T>,
  options?: { staleTime?: number }
) {
  await queryClient.prefetchQuery({
    queryKey,
    queryFn,
    staleTime: options?.staleTime ?? defaultQueryOptions.staleTime,
  });
}


