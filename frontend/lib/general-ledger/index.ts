/**
 * General Ledger API Client
 *
 * Modular API wrapper for all general ledger endpoints. Composed from
 * specialized modules:
 * - master: Chart of accounts (GLMast)
 * - transactions: Posted ledger transactions (read-only)
 * - batches: Batch capture / balance-check / post (GLBatch)
 * - standingJournals: Standing journals (GLStJnl)
 * - reportFormats: Report format Maintenance (GLRep)
 * - parameters: System parameters, system status, period/year end (GLParam)
 * - integration: Integration settings + transfer pipeline
 * - reports: Trial Balance, Income Statement, Balance Sheet
 *
 * Base URL: /api/v1/general-ledger/
 * All endpoint keys reference ENDPOINTS.GENERAL_LEDGER.* from api-config.ts.
 */

'use client';

export { glMasterApi } from './master';
export { glTransactionsApi } from './transactions';
export { glBatchesApi } from './batches';
export { glStandingJournalsApi } from './standingJournals';
export { glReportFormatsApi } from './reportFormats';
export { glParametersApi } from './parameters';
export { glIntegrationApi } from './integration';
export { glReportsApi } from './reports';

import { glMasterApi } from './master';
import { glTransactionsApi } from './transactions';
import { glBatchesApi } from './batches';
import { glStandingJournalsApi } from './standingJournals';
import { glReportFormatsApi } from './reportFormats';
import { glParametersApi } from './parameters';
import { glIntegrationApi } from './integration';
import { glReportsApi } from './reports';

/**
 * Unified general ledger API client composing all specialized modules.
 */
export const generalLedgerApi = {
  masterAccounts: glMasterApi,
  transactions: glTransactionsApi,
  batches: glBatchesApi,
  standingJournals: glStandingJournalsApi,
  reportFormats: glReportFormatsApi,
  parameters: glParametersApi,
  integration: glIntegrationApi,
  reports: glReportsApi,
};

export default generalLedgerApi;
