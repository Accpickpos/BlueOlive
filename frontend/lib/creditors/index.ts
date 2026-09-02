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

import { creditorsMasterApi } from './master';
import { creditorsTransactionsApi } from './transactions';
import { creditorsDocumentsApi } from './documents';
import { creditorsReportingApi } from './reporting';

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
  accounts: creditorsMasterApi.accounts,
  summary: creditorsMasterApi.summary,

  // Transactions
  transactions: creditorsTransactionsApi.transactions,
  journals: creditorsTransactionsApi.journals,
  payments: creditorsTransactionsApi.payments,
  openItems: creditorsTransactionsApi.openItems,
  openItemAllocations: creditorsTransactionsApi.openItemAllocations,
  openItemAudits: creditorsTransactionsApi.openItemAudits,

  // Documents
  grns: creditorsDocumentsApi.grns,
  invoices: creditorsDocumentsApi.invoices,
  creditNotes: creditorsDocumentsApi.creditNotes,
  rfc: creditorsDocumentsApi.rfc,

  // Reporting
  ledger: creditorsReportingApi.ledger,
  expenseMonthly: creditorsReportingApi.expenseMonthly,
  expenseTransactions: creditorsReportingApi.expenseTransactions,
  paymentOrders: creditorsReportingApi.paymentOrders,
  expenseCategories: creditorsReportingApi.expenseCategories,
  outstandingBalances: creditorsReportingApi.outstandingBalances,
};

export default creditorsApi;
