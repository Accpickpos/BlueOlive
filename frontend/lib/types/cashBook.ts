/**
 * Cash Book Module - Comprehensive Type Definitions
 * Organized for income/expense categories, transactions, and bank management
 */

// ============ CATEGORIES ============
export interface IncomeCategory {
  id?: number;
  name: string;
  // Matches IncomeCategory.number on the backend (apps/settings/models.py)
  // — a free-form 1-99999999 category number, not a range-restricted "code".
  number: number;
  description?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface ExpenseCategory {
  id?: number;
  name: string;
  // Matches ExpenseCategory.number on the backend (apps/settings/models.py).
  number: number;
  description?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

// ============ TRANSACTIONS ============
export interface CashBookTransaction {
  id?: number;
  date: string;
  description: string;
  amount: number;
  category_id: number;
  reference?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface OtherIncomeTransaction extends CashBookTransaction {
  income_category_id: number;
  vat_amount?: number;
  vat_inclusive?: boolean;
}

// Actual shape returned by OtherIncomeSerializer (backend/core/apps/cash_book):
// the base CashBookTransaction fields are nested under `transaction`, not flat.
export interface OtherIncomeEntry {
  id: number;
  transaction: {
    id: number;
    transaction_date: string;
    value_excl_vat: string | number;
    tax_amount: string | number;
    total_incl_vat: string | number;
    description: string;
    reference?: string;
  };
  income_category: number;
  category_name: string;
  is_vat_inclusive: boolean;
  vat_amount: string | number;
  tax_code: number;
  paid_into: 'CASH' | 'BANK';
}

export interface OtherExpenseTransaction extends CashBookTransaction {
  expense_category_id: number;
  vat_amount?: number;
  vat_inclusive?: boolean;
  is_petty_cash?: boolean;
}

// ============ BANK OPERATIONS ============
export interface BankDeposit {
  id?: number;
  date: string;
  amount: number;
  reference?: string;
  notes?: string;
  depositing_entity?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface BankWithdrawal {
  id?: number;
  date: string;
  amount: number;
  reference?: string;
  notes?: string;
  withdrawing_entity?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface BankTransfer {
  id?: number;
  from_account: string;
  to_account: string;
  amount: number;
  date: string;
  reference?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface BankCharge {
  id?: number;
  date: string;
  amount: number;
  description: string;
  reference?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface InterestReceived {
  id?: number;
  date: string;
  amount: number;
  description?: string;
  reference?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

// ============ BANK RECONCILIATION ============
// Matches BankReconciliation model / BankReconciliationSerializer
// (backend/core/apps/cash_book) — reconciliation_number is server-generated.
export interface BankReconciliation {
  id?: number;
  reconciliation_number?: string;
  reconciliation_date: string;
  bank_account_number: string;
  statement_date: string;
  statement_number?: string;
  opening_balance: number;
  closing_balance_per_statement: number;
  closing_balance_per_books: number;
  outstanding_deposits?: number;
  outstanding_cheques?: number;
  bank_errors?: number;
  book_errors?: number;
  status?: 'IN_PROGRESS' | 'COMPLETED' | 'REVIEWED';
  is_balanced?: boolean;
  difference?: number;
  notes?: string;
  completed_at?: string;
  completed_by?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ReconciliationItem {
  id?: number;
  reconciliation_id: number;
  transaction_id?: number;
  description: string;
  amount: number;
  status: 'RECONCILED' | 'OUTSTANDING' | 'CANCELLED';
  [key: string]: any;
}

// ============ CASH MANAGEMENT ============
export interface CashFloat {
  id?: number;
  register_name: string;
  opening_float: number;
  current_balance: number;
  date: string;
  updated_by?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface UnpresentedCheque {
  id?: number;
  cheque_number: string;
  amount: number;
  payee: string;
  date_issued: string;
  status: 'OUTSTANDING' | 'CLEARED' | 'CANCELLED';
  bank_account?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

// ============ ANALYSIS & REPORTING ============
export interface CategoryBalance {
  category_id: number;
  category_name: string;
  category_code: string;
  opening_balance: number;
  total_income: number;
  total_expense: number;
  closing_balance: number;
  period_start: string;
  period_end: string;
  [key: string]: any;
}

export interface MonthlyAnalysis {
  month: string;
  year: number;
  category_id: number;
  category_name: string;
  total_amount: number;
  transaction_count: number;
  [key: string]: any;
}

export interface BankingAccountEnquiry {
  account_number: string;
  account_name: string;
  opening_balance: number;
  closing_balance: number;
  total_deposits: number;
  total_withdrawals: number;
  total_charges: number;
  interest_received: number;
  period_start: string;
  period_end: string;
  reconciliation_status: 'RECONCILED' | 'PENDING' | 'VARIANCE';
  variance_amount?: number;
  [key: string]: any;
}

// ============ FILTERS & RESPONSES ============
export interface CashBookFilters {
  date_from?: string;
  date_to?: string;
  category_id?: number;
  search?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export interface PaginatedCashBookResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

// ============ SUMMARY STATISTICS ============
export interface CashBookSummary {
  total_income: number;
  total_expense: number;
  net_position: number;
  bank_balance: number;
  cash_balance: number;
  total_outstanding_cheques: number;
  reconciliation_status: 'RECONCILED' | 'PENDING' | 'VARIANCE';
  last_reconciliation_date?: string;
  [key: string]: any;
}

// ============ VALIDATION TYPES ============
export interface CategoryValidation {
  category_code: string;
  is_valid: boolean;
  message?: string;
  chart_of_accounts_reference?: string;
}

export interface TransactionValidation {
  is_valid: boolean;
  errors: string[];
  warnings?: string[];
}
