/**
 * Debtors Module - Type Definitions
 * Comprehensive types for debtor management system
 */

// ============ Debtor Account ============
// Note: API returns snake_case fields (customer_number, credit_limit, etc.)
// Components may also use legacy short names (dno, dclimit, dname, etc.)
export interface DebtorAccount {
  id: number;
  // Primary API fields
  customer_number: number; // Account number
  name: string; // Debtor name
  short_name?: string; // Short name
  contact_person?: string; // Contact person
  phone?: string; // Telephone
  phone2?: string; // Alternative phone
  fax?: string; // Fax
  email?: string; // Email address
  address_line1?: string; // Postal address line 1
  address_line2?: string; // Postal address line 2
  address_line3?: string; // Postal address line 3
  postal_code?: string; // Postal code
  delivery_address1?: string; // Delivery address line 1
  delivery_address2?: string; // Delivery address line 2
  delivery_address3?: string; // Delivery address line 3
  delivery_address4?: string; // Delivery address line 4
  tax_number?: string; // Tax/VAT number
  vat_reference?: string; // VAT registration number
  area_code?: number; // Sales area ID
  account_type?: '' | 'O' | 'C' | 'N' | 'B'; // Account type
  price_level?: number; // Price list (1-3)
  payment_terms?: number; // Payment terms (days)
  discount_percentage?: number; // Standard discount %
  prompt_payment_discount?: number; // Prompt discount %
  discount_printable?: string | boolean; // Discount print flag
  credit_limit?: number; // Credit limit
  positive_balance_only?: string | boolean; // Positive balance flag
  interest_flag?: string | boolean; // Charge interest flag
  block_flag?: string | boolean; // Blocked flag
  balance_brought_forward?: number; // Balance brought forward
  balance_current?: number; // Current aging bucket
  balance_30_days?: number; // 30 days aging bucket
  balance_60_days?: number; // 60 days aging bucket
  balance_90_days?: number; // 90 days aging bucket
  balance_120_days?: number; // 120 days aging bucket
  balance_150_days?: number; // 150 days aging bucket
  balance_180_days?: number; // 180+ days aging bucket
  sales_month?: number; // Sales month-to-date
  sales_year?: number; // Sales year-to-date
  profit_month?: number; // Profit month-to-date
  profit_year?: number; // Profit year-to-date
  last_payment_amount?: number; // Amount last paid
  last_payment_date?: string; // Date last paid
  date_opened?: string; // Date account opened
  notes?: string; // Additional notes
  total_balance?: number; // Sum of all aging buckets
  overdue_balance?: number; // Sum of overdue amounts (30+ days)
  available_credit?: number; // Available credit
  credit_utilization_pct?: number; // Credit utilization percentage
  is_blocked_flag?: boolean; // Is account blocked
  is_active: boolean; // Active status
  created_at?: string;
  updated_at?: string;
  
  // Legacy alias fields (used in some components for compatibility)
  // These map to the standard fields above
  dno: number; // Legacy alias for customer_number
  dname: string; // Legacy alias for name
  dclimit?: number; // Legacy alias for credit_limit
  dcrnt?: number; // Legacy alias for balance_current
  d30?: number; // Legacy alias for balance_30_days
  d60?: number; // Legacy alias for balance_60_days
  d90?: number; // Legacy alias for balance_90_days
  d120?: number; // Legacy alias for balance_120_days
  d150: number; // Legacy alias for balance_150_days
  d180?: number; // Legacy alias for balance_180_days
  blockflag?: boolean; // Legacy alias for is_blocked_flag
  darea_name?: string; // Area name (may need separate API call)
  
  // Additional legacy alias fields
  dcontact?: string; // Legacy alias for contact_person
  dsname?: string; // Legacy alias for short_name
  dtel?: string; // Legacy alias for phone
  dfax?: string; // Legacy alias for fax
  dadd1?: string; // Legacy alias for address_line1
  dadd2?: string; // Legacy alias for address_line2
  dadd3?: string; // Legacy alias for address_line3
  dpcode?: string; // Legacy alias for postal_code
  delad1?: string; // Legacy alias for delivery_address1
  delad2?: string; // Legacy alias for delivery_address2
  delad3?: string; // Legacy alias for delivery_address3
  delad4?: string; // Legacy alias for delivery_address4
  acctype?: string; // Legacy alias for account_type
  price?: number; // Legacy alias for price_level
  ddiscper?: number; // Legacy alias for discount_percentage
  pdisc?: number; // Legacy alias for prompt_payment_discount
  terms?: number; // Legacy alias for payment_terms
  dtaxno?: string; // Legacy alias for tax_number
  dintflag?: string | boolean; // Legacy alias for interest_flag
}

export interface DebtorCreateData extends Omit<DebtorAccount, 'id' | 'total_balance' | 'overdue_balance' | 'available_credit' | 'credit_utilization_pct' | 'is_blocked_flag' | 'created_at' | 'updated_at'> {}

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
  // Backend response fields
  total_debtors: number;
  active_debtors: number;
  blocked_debtors: number;
  total_balance: number;
  current_balance: number;
  overdue_30: number;
  overdue_60: number;
  overdue_90: number;
  overdue_120_plus: number;
  
  // Credit limit related fields
  total_credit_limit?: number;
  utilization_percentage?: number;
  
  // Aliases for component compatibility
  total_receivable?: number;
  average_dso?: number;
  critical_aging?: number;
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
