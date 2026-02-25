'use client';

/**
 * Dynamic Imports Utility
 * Provides lazy loading for heavy components to improve initial load time
 */

import dynamic from 'next/dynamic';
import { ComponentType, ReactElement, ReactNode } from 'react';

// Default loading component
const DefaultLoading = () => (
  <div className="flex items-center justify-center min-h-[200px]">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
  </div>
);

// Default error fallback
interface ErrorFallbackProps {
  error: Error;
  resetError?: () => void;
}

const DefaultErrorFallback = ({ error, resetError }: ErrorFallbackProps) => (
  <div className="flex items-center justify-center min-h-[200px] p-6">
    <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
      <h3 className="text-lg font-bold text-red-900 mb-2">Error Loading Component</h3>
      <p className="text-red-800 text-sm mb-4">{error.message}</p>
      {resetError && (
        <button
          onClick={resetError}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm font-medium"
        >
          Try Again
        </button>
      )}
    </div>
  </div>
);

/**
 * Create a dynamic import with loading and error states
 */
export function createDynamicImport<T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  options?: {
    loading?: ReactNode;
    errorFallback?: (props: ErrorFallbackProps) => ReactElement;
    ssr?: boolean;
    prefetch?: boolean;
  }
) {
  const { 
    loading = <DefaultLoading />, 
    errorFallback,
    ssr = false,
    prefetch = false 
  } = options || {};

  return dynamic(importFunc, {
    loading: () => loading,
    ssr,
    ...(errorFallback && { error: errorFallback }),
  });
}

// ============ Feature-specific dynamic imports ============

// Debtors module
export const DebtorsList = createDynamicImport(
  () => import('@/components/debtors/DebtorDetailView'),
  { ssr: false }
);

export const DebtorForm = createDynamicImport(
  () => import('@/components/debtors/forms/DebtorAccountForm'),
  { ssr: false }
);

export const TransactionManagement = createDynamicImport(
  () => import('@/components/debtors/TransactionManagement'),
  { ssr: false }
);

// Creditors module
export const CreditorForm = createDynamicImport(
  () => import('@/components/creditors/CreditorForm'),
  { ssr: false }
);

export const CreditorsMaintenance = createDynamicImport(
  () => import('@/components/creditors/CreditorsMaintenance'),
  { ssr: false }
);

// Stock Control module
export const StockTransactions = createDynamicImport(
  () => import('@/components/stock-control/transactions/StockTransactions'),
  { ssr: false }
);

export const IncomingStock = createDynamicImport(
  () => import('@/components/stock-control/transactions/IncomingStock'),
  { ssr: false }
);

export const StockTake = createDynamicImport(
  () => import('@/components/stock-control/transactions/StockTakeMenu'),
  { ssr: false }
);

// POS module
export const POSPage = createDynamicImport(
  () => import('@/app/dashboard/pos/page'),
  { ssr: false }
);

export const CashSales = createDynamicImport(
  () => import('@/app/dashboard/pos/cash-sales/page'),
  { ssr: false }
);

export const Invoices = createDynamicImport(
  () => import('@/app/dashboard/pos/invoices/page'),
  { ssr: false }
);

export const Receipts = createDynamicImport(
  () => import('@/app/dashboard/pos/receipts/page'),
  { ssr: false }
);

// Purchase Orders module
export const PurchaseOrdersPage = createDynamicImport(
  () => import('@/app/dashboard/purchase-orders/page'),
  { ssr: false }
);

// Reports (usually heavy, definitely lazy load)
export const DebtorsAgeAnalysisChart = createDynamicImport(
  () => import('@/components/debtors/dashboard/AgeAnalysisChart'),
  { ssr: false }
);

export const SalesAnalysis = createDynamicImport(
  () => import('@/components/debtors/enquiries/SalesAnalysis'),
  { ssr: false }
);

// Import functionality (heavy)
export const ImportPage = createDynamicImport(
  () => import('@/app/dashboard/admin/import/page'),
  { ssr: false }
);

// ============ Utility function for custom dynamic imports ============

/**
 * Hook for conditional dynamic loading based on user interaction
 */
export function useDynamicImport<T extends ComponentType<any>>(
  shouldLoad: boolean,
  importFunc: () => Promise<{ default: T }>
): ReactElement | null {
  const Component = dynamic(importFunc, {
    ssr: false,
    loading: () => <DefaultLoading />,
  });

  if (!shouldLoad) {
    return null;
  }

  return <Component />;
}

/**
 * Preload a component on hover or focus
 */
export function preloadComponent<T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>
) {
  if (typeof window !== 'undefined') {
    importFunc();
  }
}
