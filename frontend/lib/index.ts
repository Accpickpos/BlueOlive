/**
 * API Index
 * 
 * Central export point for all API modules
 * This allows easy importing: import { debtorsApi, creditorsApi } from '@/lib'
 */

// API Modules
export { authApi } from './authApi';
export { tenantsApi } from './tenantsApi';
export { debtorsApi } from './debtorsApi';
export { creditorsApi } from './creditorsApi';
export { cashBookApi } from './cashBookApi';
export { generalLedgerApi } from './generalLedgerApi';
export { stockControlApi as stockApi } from './stockControlApi';
export { stockControlApi } from './stockControlApi';
export {
  getStockItem,
  getStockItems,
  createStockItem,
  updateStockItem,
  deleteStockItem,
  getStockItemPricing,
  getStockItemTransactions,
  adjustStockItem,
} from './stockControlApi';
export { purchaseOrdersApi } from './purchaseOrdersApi';
export { posAPI, usePOSAPI } from './posApi';
export { settingsApi, default } from './settingsApi';

// Export Creditors Hooks
export {
  useCreditors,
  useCreditorById,
  useCreditorInvoices,
  useCreditorPayments,
  useCreditorOpenItems,
  useGrns,
  useCreditorAgingAnalysis,
  useCreditorsSummary,
  useCreditorMutation,
  useInvoiceMutation,
  usePaymentMutation,
  type UseApiResponse,
  type UseApiState,
} from './hooks/useCreditorApi';

// Export configuration
export { ENDPOINTS, API_BASE_URL, API_V1_BASE, buildApiUrl } from './api-config';

// Export axios instance
export { api, isAuthenticated, clearAuthData, fetchCSRFToken } from './api';

// Re-export from subdirectories for convenient access
export * from './utils';
export * from './hooks';
export * from './types';
