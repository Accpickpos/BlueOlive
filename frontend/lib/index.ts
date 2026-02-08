/**
 * API Index
 * 
 * Central export point for all API modules
 * This allows easy importing: import { debtorsApi, creditorsApi } from '@/lib/api'
 */

export { authApi, default } from './authApi';
export { tenantsApi, default } from './tenantsApi';
export { debtorsApi, default } from './debtorsApi';
export { creditorsApi, default } from './creditorsApi';
export { cashBookApi, default } from './cashBookApi';
export { generalLedgerApi, default } from './generalLedgerApi';
export { stockApi, default } from './stockApi';
export { purchaseOrdersApi, default } from './purchaseOrdersApi';
export { posAPI, usePOSAPI } from './posApi';
export { settingsApi, default } from './settingsApi';

// Export API Clients
// Note: Clients are now created locally in hooks if needed
// The main APIs are: creditorsApi, debtorsApi, stockApi, etc.

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
  type UseCreditorApiResponse,
  type UseCreditorApiState,
} from './hooks/useCreditorApi';

// Export configuration
export { ENDPOINTS, API_BASE_URL, API_V1_BASE, buildApiUrl } from './api-config';

// Export axios instance
export { api, isAuthenticated, clearAuthData, fetchCSRFToken } from './api';
