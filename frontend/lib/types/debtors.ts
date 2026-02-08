/**
 * Debtors Module - Type Definitions
 * Comprehensive types for debtor management system
 */

// ============ Debtor Account ============
export interface DebtorAccount {
  id: number;
  dno: string; // Account number
  dname: string; // Debtor name
  dsname?: string; // Short name
  dcontact?: string; // Contact person
  dtel?: string; // Telephone
  dfax?: string; // Fax
  email?: string; // Email address
  dadd1?: string; // Postal address line 1
  dadd2?: string; // Postal address line 2
  dadd3?: string; // Postal address line 3
  delad1?: string; // Delivery address line 1
  delad2?: string; // Delivery address line 2
  delad3?: string; // Delivery address line 3
  delad4?: string; // Delivery address line 4
  dtaxno?: string; // Tax/VAT number
  darea?: number; // Sales area ID
  darea_name?: string; // Sales area name
  acctype?: 'BF' | 'OI' | 'CS'; // Account type (Balance Forward, Open Item, Cash)
  price?: number; // Price list (1-3)
  ddiscper?: number; // Trade discount %
  pdisc?: number; // Prompt discount %
  dclimit?: number; // Credit limit
  dintflag?: boolean; // Charge interest flag
  dcrnt?: number; // Current aging bucket
  d30?: number; // 30 days aging bucket
  d60?: number; // 60 days aging bucket
  d90?: number; // 90 days aging bucket
  d120?: number; // 120 days aging bucket
  d150?: number; // 150 days aging bucket
  d180?: number; // 180+ days aging bucket
  dsalesm?: number; // Sales month-to-date
  dsalesy?: number; // Sales year-to-date
  dprofitm?: number; // Profit month-to-date
  dprofity?: number; // Profit year-to-date
  damtlpd?: number; // Amount last paid
  ddatlpd?: string; // Date last paid
  blockflag?: boolean; // Blocked flag
  is_active: boolean; // Active status
  total_balance?: number; // Sum of all aging buckets
  days_sales_outstanding?: number; // DSO metric
  last_transaction_date?: string; // Last transaction date
  created_at?: string;
  updated_at?: string;
}

export interface DebtorCreateData extends Omit<DebtorAccount, 'id' | 'total_balance' | 'days_sales_outstanding' | 'last_transaction_date' | 'created_at' | 'updated_at'> {}

export interface DebtorEditData extends Partial<DebtorCreateData> {}

// ============ Age Analysis ============
export interface AgeAnalysisBucket {
  label: string;
  amount: number;
  days_min: number;
  days_max: number;
  percentage?: number;
}

export interface AgeAnalysis {
  debtor_id: number;
  debtor_number?: string;
  debtor_name?: string;
  buckets: AgeAnalysisBucket[];
  total_balance: number;
  credit_limit?: number;
  utilization_percentage?: number;
  days_sales_outstanding?: number;
  analysis_date?: string;
}

// ============ Transactions ============
export enum TransactionType {
  INVOICE = 'IN',
  CREDITNOTE = 'CN',
  CASHSALE = 'CS',
  CORRECTION = 'CR',
  RECEIPT = 'RCP',
  INTEREST = 'INT',
  JOURNALDEBIT = 'JD',
  JOURNALCREDIT = 'JC',
}

export interface Transaction {
  id: number;
  debtor_id: number;
  debtor_name?: string;
  transaction_date: string;
  transaction_type: TransactionType;
  reference_number?: string;
  description?: string;
  amount: number;
  allocated?: number;
  outstanding?: number;
  created_at?: string;
}

export interface TransactionCreateData {
  debtor_id: number;
  transaction_date: string;
  transaction_type: TransactionType;
  reference_number?: string;
  description?: string;
  amount: number;
}

// ============ Open Items ============
export interface OpenItem {
  id: number;
  debtor_id: number;
  transaction_id?: number;
  document_number?: string;
  document_date: string;
  due_date?: string;
  amount: number;
  allocated: number;
  outstanding: number;
  document_type: string;
  memo?: string;
  created_at?: string;
}

// ============ Post-Dated Cheques ============
export interface PostDatedCheque {
  id: number;
  debtor_id: number;
  cheque_number: string;
  amount: number;
  expected_date: string;
  bank?: string;
  received_date?: string;
  cleared_date?: string;
  status: 'OUTSTANDING' | 'RECEIVED' | 'CLEARED' | 'DISHONOURED';
  notes?: string;
  created_at?: string;
}

export interface PostDatedChequeCreateData extends Omit<PostDatedCheque, 'id' | 'created_at'> {}

// ============ Sales Areas ============
export interface SalesArea {
  id: number;
  name: string;
  code?: string;
  regional_manager?: string;
  created_at?: string;
}

// ============ Summary ============
export interface DebtorsSummary {
  total_debtors: number;
  active_debtors: number;
  blocked_debtors: number;
  total_receivable: number;
  average_dso: number;
  critical_aging: number; // Amount over 120 days
  total_credit_limit: number;
  utilization_percentage: number;
  top_debtors?: DebtorAccount[];
  aging_summary?: {
    current: number;
    days_30: number;
    days_60: number;
    days_90: number;
    days_120_plus: number;
  };
}

// ============ Filters ============
export interface DebtorFilters {
  search?: string;
  area?: number;
  blocked?: boolean;
  is_active?: boolean;
  acctype?: 'BF' | 'OI' | 'CS';
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface TransactionFilters {
  debtor_id?: number;
  transaction_type?: TransactionType;
  date_from?: string;
  date_to?: string;
  amount_from?: number;
  amount_to?: number;
  page?: number;
  page_size?: number;
}

export interface AgeAnalysisFilters {
  cutoff_date?: string;
  include_zero_balance?: boolean;
}

// ============ Reports ============
export interface DebtorReport {
  account_number: string;
  debtor_name: string;
  balance_current: number;
  balance_30: number;
  balance_60: number;
  balance_90: number;
  balance_120_plus: number;
  total_balance: number;
  credit_limit?: number;
  dso?: number;
}

export interface DebtorAgeAnalysisReport {
  total_debtors: number;
  total_balance: number;
  critical_balance: number; // 120+ days
  aging_buckets: {
    current: { count: number; amount: number };
    days_30: { count: number; amount: number };
    days_60: { count: number; amount: number };
    days_90: { count: number; amount: number };
    days_120_plus: { count: number; amount: number };
  };
}

export interface SalesPerformanceReport {
  period: string;
  sales_mtd: number;
  sales_ytd: number;
  profit_mtd: number;
  profit_ytd: number;
  top_customers?: Array<{
    debtor_id: number;
    debtor_name: string;
    sales: number;
    profit: number;
  }>;
}

// ============ Audit ============
export interface AuditLog {
  id: number;
  debtor_id?: number;
  action: string;
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  user?: string;
  timestamp: string;
  ip_address?: string;
}

// ============ Pagination ============
export interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

export interface ListResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
