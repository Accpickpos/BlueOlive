/**
 * General Ledger API Client
 *
 * DEPRECATED: This file is kept for backward compatibility only. It was
 * previously dead code — imported nowhere — with field names invented
 * against no real backend (account_code, debit_account_id, is_active, a
 * fictional trial_balance/post_journal/execute action set). It has been
 * replaced entirely by the modular client in './general-ledger', whose
 * field names and actions match the real Django serializers/viewsets in
 * backend/core/apps/general_ledger/.
 *
 * Please use the new modular API from './general-ledger' instead:
 * - general-ledger/master.ts: Chart of accounts (GLMast)
 * - general-ledger/transactions.ts: Posted ledger transactions (read-only)
 * - general-ledger/batches.ts: Batch capture / balance-check / post
 * - general-ledger/standingJournals.ts: Standing journals
 * - general-ledger/reportFormats.ts: Report format Maintenance
 * - general-ledger/parameters.ts: System parameters, status, period/year end
 * - general-ledger/integration.ts: Integration settings + transfer
 * - general-ledger/reports.ts: Trial Balance, Income Statement, Balance Sheet
 *
 * Base URL: /api/v1/general-ledger/
 */

'use client';

export {
  generalLedgerApi,
  glMasterApi,
  glTransactionsApi,
  glBatchesApi,
  glStandingJournalsApi,
  glReportFormatsApi,
  glParametersApi,
  glIntegrationApi,
  glReportsApi,
} from './general-ledger';
export { default } from './general-ledger';
