/**
 * General Ledger Module — Type Definitions
 * All field names match the Django serializer output exactly
 * (backend/core/apps/general_ledger/serializers.py).
 */

export interface PaginatedResponse<T> {
  count: number;
  next?: string | null;
  previous?: string | null;
  results: T[];
}

export type DrOrCr = 'D' | 'C';
export type AccountType = 'I' | 'B'; // Income Statement | Balance Sheet
export type JournalSource = 'M' | 'S' | 'I' | 'B' | 'O'; // Manual/System/Import/Bank/Other

// ============================================================================
// GLMast — Master Chart of Accounts
// ============================================================================

export interface GLMast {
  id: number;
  accno: number;
  name: string;
  type: AccountType;
  type_display: string;
  drorcr: DrOrCr;
  drorcr_display: string;
  repline: number;
  balbfwd: number;
  period1: number; period2: number; period3: number; period4: number;
  period5: number; period6: number; period7: number; period8: number;
  period9: number; period10: number; period11: number; period12: number;
  period13: number;
  budget1: number; budget2: number; budget3: number; budget4: number;
  budget5: number; budget6: number; budget7: number; budget8: number;
  budget9: number; budget10: number; budget11: number; budget12: number;
  lastyear1: number; lastyear2: number; lastyear3: number; lastyear4: number;
  lastyear5: number; lastyear6: number; lastyear7: number; lastyear8: number;
  lastyear9: number; lastyear10: number; lastyear11: number; lastyear12: number;
  created_at: string;
  updated_at: string;
}

export interface GLMastListItem {
  id: number;
  accno: number;
  name: string;
  type: AccountType;
  type_display: string;
  drorcr: DrOrCr;
  drorcr_display: string;
  repline: number;
  balbfwd: number;
}

export interface GLMastCreateData {
  accno: number;
  name: string;
  type: AccountType;
  drorcr: DrOrCr;
  repline: number;
  balbfwd?: number;
}

// ============================================================================
// GLTran — Posted Ledger Transactions (read-only via the API)
// ============================================================================

export interface GLTran {
  id: number;
  accno: number;
  batchno: number;
  date: string;
  time?: string | null;
  type: DrOrCr;
  type_display: string;
  source: JournalSource;
  source_display: string;
  station?: string;
  reference?: string;
  details?: string;
  amount: number;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// GLBatch — Staging entries (capture -> balance_check -> post)
// ============================================================================

export interface GLBatch {
  id: number;
  accno: number;
  batchno: number;
  capturedat: string;
  date: string;
  time?: string;
  drorcr: DrOrCr;
  drorcr_display: string;
  source: JournalSource;
  source_display: string;
  station?: string;
  reference?: string;
  details?: string;
  amount: number;
  postdate: string | null;
  postime: string | null;
  period: number;
  created_at: string;
  updated_at: string;
}

export interface GLBatchCreateData {
  accno: number;
  batchno: number;
  capturedat: string;
  date: string;
  time?: string;
  drorcr: DrOrCr;
  source?: JournalSource;
  station?: string;
  reference?: string;
  details?: string;
  amount: number;
  period: number;
}

export interface BatchBalanceCheck {
  batchno: string | number;
  line_count?: number;
  total_debit: number;
  total_credit: number;
  is_balanced: boolean;
  already_posted?: boolean;
  status?: 'no_data';
  message?: string;
}

export interface BatchPostResult {
  batchno: string | number;
  gl_batchno: number;
  lines_posted: number;
}

// ============================================================================
// GLStJnl — Standing Journals
// ============================================================================

export interface GLStJnl {
  id: number;
  accno: number;
  details: string;
  drorcr: DrOrCr;
  drorcr_display: string;
  amount: number;
  frequency: number;
  stperiod: number;
  times: number;
  timesbal: number;
  nextperiod: number;
  descriptor?: string;
  journalno: number;
  created_at: string;
  updated_at: string;
}

export interface GLStJnlCreateData {
  accno: number;
  details: string;
  drorcr: DrOrCr;
  amount: number;
  frequency: number;
  stperiod: number;
  times: number;
  nextperiod: number;
  descriptor?: string;
  journalno: number;
}

export interface JournalBalanceCheck {
  journalno: string | number;
  total_debit: number;
  total_credit: number;
  is_balanced: boolean;
}

export interface PostDueResult {
  journals_posted: number[];
  journals_skipped_unbalanced: number[];
  journals_completed: number[];
}

// ============================================================================
// GLSpread — Spread sheets
// ============================================================================

export interface GLSpread {
  id: number;
  accno: number;
  name: string;
  ytddebit: number;
  ytdcredit: number;
  curdebit: number;
  curcredit: number;
  curbuddeb: number;
  curbudcred: number;
  ytdbuddeb: number;
  ytdbudcred: number;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// GLRep — Report Format rows (Maintenance only)
// ============================================================================

export type GLRepFieldType = 'H' | 'T' | 'D' | 'S'; // Heading/Total/Detail/Subtotal

export interface GLRep {
  id: number;
  type: AccountType;
  type_display: string;
  fieldtype: GLRepFieldType;
  fieldtype_display: string;
  line: number;
  printdet: 'D' | 'S' | 'N';
  printdet_display: string;
  name: string;
  start: number;
  endcalc: number;
  created_at: string;
  updated_at: string;
}

export interface GLRepCreateData {
  type: AccountType;
  fieldtype: GLRepFieldType;
  line: number;
  printdet: 'D' | 'S' | 'N';
  name: string;
  start: number;
  endcalc: number;
}

// ============================================================================
// GLParam — System parameters (singleton)
// ============================================================================

export interface GLParam {
  id: number;
  startper: number;
  batchno: number;
  curperiod: number;
  adjusted: 'Y' | 'N';
  adjusted_display: string;
  currentyr: number;
  retained_earnings_accno: number | null;
  created_at: string;
  updated_at: string;
}

export interface SystemStatus {
  startper: number;
  curperiod: number;
  currentyr: number;
  adjusted: 'Y' | 'N';
  next_batchno: number;
  outstanding_batches: number;
  outstanding_batchnos: number[];
  last_transaction_date: string | null;
  retained_earnings_accno: number | null;
}

export interface PeriodEndResult {
  previous_period: number;
  curperiod: number;
}

export interface YearEndResult {
  previous_year: number;
  currentyr: number;
  curperiod: number;
  net_income: number;
  closing_gl_batchno: number | null;
}

// ============================================================================
// GLIntegrationSettings — Integration control-account mapping (singleton)
// ============================================================================

export interface GLIntegrationSettings {
  id: number;
  debtors_control_accno: number | null;
  creditors_control_accno: number | null;
  bank_control_accno: number | null;
  cash_control_accno: number | null;
  sales_accno: number | null;
  vat_output_accno: number | null;
  vat_input_accno: number | null;
  stock_control_accno: number | null;
  stock_shrinkage_expense_accno: number | null;
  stock_gain_income_accno: number | null;
  debtors_interest_income_accno: number | null;
  debtors_suspense_accno: number | null;
  creditors_discount_received_accno: number | null;
  creditors_suspense_accno: number | null;
  cashbook_default_income_accno: number | null;
  cashbook_default_expense_accno: number | null;
  created_at: string;
  updated_at: string;
}

export type IntegrationSource = 'debtors' | 'creditors' | 'stock_control' | 'cash_book' | 'all';

export interface IntegrationTransferRequest {
  source: IntegrationSource;
  date_from?: string;
  date_to?: string;
}

export interface IntegrationTransferSummary {
  transferred: number;
  skipped: Array<Record<string, unknown>>;
  errors: Array<Record<string, unknown>>;
}

export interface IntegrationTransferResponse {
  report_title: string;
  results: Record<string, IntegrationTransferSummary>;
}

export interface IntegrationOutstandingResponse {
  report_title: string;
  outstanding: {
    debtors: number;
    creditors: Record<string, number>;
    stock_control: number;
    cash_book: number;
  };
}

// ============================================================================
// Reports
// ============================================================================

export interface TrialBalanceRow {
  accno: number;
  name: string;
  drorcr: DrOrCr;
  debit: number;
  credit: number;
}

export interface TrialBalanceResponse {
  report_title: string;
  as_of_period: number;
  currentyr: number | null;
  accounts: TrialBalanceRow[];
  total_debit: number;
  total_credit: number;
  is_balanced: boolean;
}

// Income Statement layout modes (7. General Ledger, Enquiries > 5. Income
// Statement in the manual). "current" is a single "amount" column;
// everything else carries a different, mode-specific set of numeric
// columns instead (see FinancialReportLine.columns).
export type IncomeStatementMode =
  | 'current'
  | 'current_ytd'
  | 'current_last_year'
  | 'current_budget'
  | 'budget_12'
  | 'variance'
  | 'actual_12';

export interface FinancialReportLine {
  line: number;
  fieldtype: GLRepFieldType;
  name: string;
  printdet: string;
  // "current" mode (and every Balance Sheet line, which only has one mode)
  amount?: number;
  // Every other Income Statement mode: whatever named columns that mode
  // produces (e.g. current/ytd/budget/ytd_budget, or month1..month12) —
  // deliberately untyped since the shape varies by mode.
  [key: string]: number | string | undefined;
}

export interface IncomeStatementResponse {
  report_title: string;
  as_of_period: number;
  mode: IncomeStatementMode;
  currentyr: number | null;
  lines: FinancialReportLine[];
  net_result: number | null;
  is_seeded: boolean;
}

export interface BalanceSheetResponse {
  report_title: string;
  as_of_period: number;
  currentyr: number | null;
  lines: FinancialReportLine[];
  total_assets: number;
  total_liabilities_and_equity: number;
  net_income: number;
  is_balanced: boolean;
  is_seeded: boolean;
}
