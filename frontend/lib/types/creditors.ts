/**
 * Creditors Module - Type Definitions
 * Comprehensive types for creditor management system
 */

// ============ Creditor Account ============
export interface CreditorAccount {
  id: number;
  account_number: string;
  name: string;
  account_type: 'BBF' | 'OPEN_ITEM';
  contact_person?: string;
  physical_address?: string;
  postal_address?: string;
  telephone?: string;
  fax?: string;
  email?: string;
  our_account_number?: string;
  credit_terms: number;
  payment_discount_percent: number;
  bank_name?: string;
  branch_code?: string;
  bank_account_number?: string;
  update_selling_price_on_grn: boolean;
  balance: number;
  current_aging?: number;
  d30?: number;
  d60?: number;
  d90?: number;
  d120?: number;
  d150?: number;
  d180?: number;
  last_payment_date?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface CreditorCreateData extends Omit<CreditorAccount, 'id' | 'balance' | 'current_aging' | 'd30' | 'd60' | 'd90' | 'd120' | 'd150' | 'd180' | 'last_payment_date' | 'created_at' | 'updated_at'> {}

export interface CreditorEditData extends Partial<CreditorCreateData> {}

// ============ Expense Categories ============
export interface ExpenseCategory {
  id: number;
  category_number: string;
  name: string;
  transaction_count?: number;
  total_amount?: number;
  total_tax?: number;
  created_at?: string;
  updated_at?: string;
}

export interface ExpenseCategoryCreateData extends Omit<ExpenseCategory, 'id' | 'transaction_count' | 'total_amount' | 'total_tax' | 'created_at' | 'updated_at'> {}

// ============ Transactions ============
export enum TransactionType {
  GRN = 'GRN',
  INVOICE_EXPENSE = 'INVOICE_EXPENSE',
  PAYMENT = 'PAYMENT',
  RETURN_STOCK = 'RETURN_STOCK',
  RETURN_EXPENSE = 'RETURN_EXPENSE',
  JOURNAL = 'JOURNAL',
  RFC = 'RFC',
}

export interface Transaction {
  id: number;
  account_id?: number;
  supplier_id?: number;
  supplier_name?: string;
  transaction_type: TransactionType;
  reference_number?: string;
  transaction_date?: string;
  invoice_number?: string;
  invoice_date?: string;
  due_date?: string;
  description?: string;
  amount?: number;
  tax_amount?: number;
  vat_rate?: number;
  vat_option?: 'I' | 'E';
  category_name?: string;
  status?: string;
  item_count?: number;
  return_reason?: string;
  entry_type?: 'DEBIT' | 'CREDIT';
  created_at?: string;
  updated_at?: string;
}

export interface TransactionCreateData extends Omit<Transaction, 'id' | 'created_at' | 'updated_at'> {}

export interface TransactionFilters {
  transaction_type?: string;
  account_id?: number;
  supplier_id?: number;
  search?: string;
  start_date?: string;
  end_date?: string;
  date_from?: string;
  date_to?: string;
  status?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}

// ============ Summary/Reports ============
export interface CreditorsSummary {
  total_creditors: number;
  total_payable: number;
  current_aging: number;
  d30?: number;
  d60?: number;
  d90?: number;
  d120?: number;
  critical_aging: number;
  average_dpo: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

// ============ Filters ============
export interface CreditorFilters {
  search?: string;
  account_type?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface ExpenseCategoryFilters {
  search?: string;
  page?: number;
  page_size?: number;
  start_date?: string;
  end_date?: string;
  ordering?: string;
}
