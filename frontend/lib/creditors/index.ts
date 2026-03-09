/**
 * Creditors API Client
 * 
 * Modular API wrapper for all creditor management endpoints.
 * Composed from specialized modules:
 * - master: Creditor accounts and summary
 * - transactions: Journals, payments, open items
 * - documents: GRNs, invoices, credit notes, RFCs
 * - reporting: Ledger, expenses, payment orders, categories
 *
 * Base URL: /api/v1/creditors/
 * All endpoint keys reference ENDPOINTS.CREDITORS.* from api-config.ts.
 */

'use client';

// Re-export all modules
export { creditorsMasterApi } from './master';
export { creditorsTransactionsApi } from './transactions';
export { creditorsDocumentsApi } from './documents';
export { creditorsReportingApi, useCreditorsAPI } from './reporting';

// Re-export types from master for convenience
export type {
  Supplier,
  SupplierCreateData,
  CreditTermsOption,
} from './master';

// Re-export types from reporting for convenience
export type {
  ExpenseCategory,
  ExpenseCategoryCreateData,
  OutstandingBalance,
  OutstandingBalanceCaptureData,
} from './reporting';

// ============================================================================
// Composed API client - provides unified access to all modules
// ============================================================================

/**
 * Unified creditors API client that composes all specialized modules.
 * This maintains backward compatibility with the original monolithic API.
 */
export const creditorsApi = {
  // Master data
  accounts: require('./master').creditorsMasterApi.accounts,
  summary: require('./master').creditorsMasterApi.summary,

  // Transactions
  transactions: require('./transactions').creditorsTransactionsApi.transactions,
  journals: require('./transactions').creditorsTransactionsApi.journals,
  payments: require('./transactions').creditorsTransactionsApi.payments,
  openItems: require('./transactions').creditorsTransactionsApi.openItems,
  openItemAllocations: require('./transactions').creditorsTransactionsApi.openItemAllocations,
  openItemAudits: require('./transactions').creditorsTransactionsApi.openItemAudits,

  // Documents
  grns: require('./documents').creditorsDocumentsApi.grns,
  invoices: require('./documents').creditorsDocumentsApi.invoices,
  creditNotes: require('./documents').creditorsDocumentsApi.creditNotes,
  rfc: require('./documents').creditorsDocumentsApi.rfc,

  // Reporting
  ledger: require('./reporting').creditorsReportingApi.ledger,
  expenseMonthly: require('./reporting').creditorsReportingApi.expenseMonthly,
  expenseTransactions: require('./reporting').creditorsReportingApi.expenseTransactions,
  paymentOrders: require('./reporting').creditorsReportingApi.paymentOrders,
  expenseCategories: require('./reporting').creditorsReportingApi.expenseCategories,
  outstandingBalances: require('./reporting').creditorsReportingApi.outstandingBalances,
};

export default creditorsApi;
