/**
 * Creditors API Client
 * 
 * DEPRECATED: This file is kept for backward compatibility.
 * Please use the new modular API from './creditors' instead.
 *
 * New module structure:
 * - creditors/master.ts: Creditor accounts and summary
 * - creditors/transactions.ts: Journals, payments, open items
 * - creditors/documents.ts: GRNs, invoices, credit notes, RFCs
 * - creditors/reporting.ts: Ledger, expenses, payment orders, categories
 *
 * Base URL: /api/v1/creditors/
 * All endpoint keys reference ENDPOINTS.CREDITORS.* from api-config.ts.
 */

'use client';

// Re-export from new modular structure for backward compatibility
export { creditorsApi, creditorsMasterApi, creditorsTransactionsApi, creditorsDocumentsApi, creditorsReportingApi, useCreditorsAPI } from './creditors';
export { default } from './creditors';

// Re-export types for convenience
export type { Supplier, SupplierCreateData, CreditTermsOption } from './creditors/master';
export type { ExpenseCategory, ExpenseCategoryCreateData, OutstandingBalance, OutstandingBalanceCaptureData } from './creditors/reporting';

// ============================================================================
// Legacy exports - these were originally exported from this file
// ============================================================================

// Note: The useCreditorsAPI hook is now exported from ./creditors/reporting.ts
// Import it from there for new code: import { useCreditorsAPI } from './creditors';

// The creditorsApi object is now composed from modules in ./creditors/index.ts
// This maintains full backward compatibility
