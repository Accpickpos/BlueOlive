/**
 * Creditors Module — Type Definitions
 * All field names match the Django serializer output exactly.
 *
 * Key changes from legacy types:
 *   account_number       → supplier_number        (SUPNO N(4))
 *   account_type 'BBF'   → account_category 'B'   (ACCTYPE C(1))
 *   account_type 'OI'    → account_category 'O'
 *   balance              → total_outstanding_balance
 *   current_aging        → balance_current
 *   d30/d60…             → balance_30_days / balance_60_days…
 *   payment_discount_percent → prompt_payment_discount_percent
 *   bank_account_number  → account_number          (BANKACC C(15))
 *   update_selling_price_on_grn → update_selling_price_on_receipt
 *   TransactionType enum → individual typed interfaces per document type
 */

// ============================================================================
// CREDITOR MASTER  (supmast.dbf)
// ============================================================================

export interface CreditorAccount {
  id:             number;
  // Identification
  supplier_number: string;           // SUPNO N(4)
  name:            string;           // SUPNAME C(30)
  // Contact
  contact_person?: string;           // SUPCONT C(20)
  telephone?:      string;           // SUPTEL C(15)
  fax?:            string;           // SUPFAX C(15)
  email?:          string;           // EMAIL C(60)
  // Physical address
  physical_address_line1?: string;   // SUPADD1 C(25)
  physical_address_line2?: string;   // SUPADD2 C(25)
  physical_address_line3?: string;   // SUPADD3 C(25)
  // Postal address
  postal_address_line1?: string;     // SUPPADD1 C(20)
  postal_address_line2?: string;     // SUPPADD2 C(20)
  postal_address_line3?: string;     // SUPPADD3 C(20)
  // Account settings
  our_account_number?:              string;        // SUPOURACC C(15)
  credit_terms?:                    number | null; // FK to CreditTerms
  credit_terms_display?:            string;        // read-only label
  payment_terms_days:               number;        // SUPTERMS (raw days fallback)
  effective_terms_days?:            number;        // computed by serializer
  account_category:                 'B' | 'O' | '';  // ACCTYPE C(1): B=BBF, O=Open Item
  sales_area?:                      number | null;
  sales_area_display?:              string;
  update_selling_price_on_receipt:  boolean;       // UPDSTKSP
  prompt_payment_discount_percent:  number;        // SUPDISC N(5,2)
  // Banking
  bank_name?:     string;            // BANK C(10)
  branch_code?:   string;            // BANKCODE C(10)
  account_number?: string;           // BANKACC C(15) — note: this is the bank account number
  // System-generated balances (read-only)
  balance_brought_forward:   number; // SUPBALBFWD
  total_outstanding_balance: number; // sum of all aging buckets
  balance_current:           number; // SUPCRNT — current (not yet due)
  balance_30_days:           number; // SUP30
  balance_60_days:           number; // SUP60
  balance_90_days:           number; // SUP90
  balance_120_days:          number; // SUP120
  balance_150_days:          number; // SUP150
  balance_180_days:          number; // SUP180 (Django-only; always 0 on import)
  last_paid_amount:          number; // SUPPMT
  last_paid_date?:           string; // SUPPMTDATE
  purchases_mtd:             number; // SUPURCHMTD
  purchases_ytd:             number; // SUPURCHYTD
  total_balance:            number; 
  // Timestamps
  is_active:  boolean;
  created_at: string;
  updated_at: string;
}

/** Fields a user submits to create a creditor. All system-generated fields omitted. */
export interface CreditorCreateData {
  supplier_number:                  string;
  name:                             string;
  contact_person?:                  string;
  telephone?:                       string;
  fax?:                             string;
  email?:                           string;
  physical_address_line1?:          string;
  physical_address_line2?:          string;
  physical_address_line3?:          string;
  postal_address_line1?:            string;
  postal_address_line2?:            string;
  postal_address_line3?:            string;
  our_account_number?:              string;
  credit_terms?:                    number | null;
  payment_terms_days?:              number;
  account_category?:                'B' | 'O' | '';
  sales_area?:                      number | null;
  update_selling_price_on_receipt?: boolean;
  prompt_payment_discount_percent?: number;
  bank_name?:                       string;
  branch_code?:                     string;
  account_number?:                  string;
  is_active?:                       boolean;
}

export type CreditorEditData = Partial<CreditorCreateData>;

// ============================================================================
// AGED BALANCE SUMMARY  (CreditorAgedBalanceSummarySerializer)
// ============================================================================

export interface AgedBalanceSummary {
  id:                        number;
  supplier_number:           string;
  name:                      string;
  balance_current:           number;
  balance_30_days:           number;
  balance_60_days:           number;
  balance_90_days:           number;
  balance_120_days:          number;
  balance_150_days:          number;
  balance_180_days:          number;
  total_outstanding_balance: number;
}

// ============================================================================
// GOODS RECEIVED NOTE  (suptran STYPE='GR')
// ============================================================================

export interface GRNLineItem {
  id?:               number;
  line_number?:      number;
  stock_item:        number;  // FK to StockItem
  stock_code?:       string;  // read-only
  quantity_received: number;
  unit_cost:         number;
  tax_code:          number;  // FK to TaxCode
  tax_code_display?: string;
  // System-calculated (read-only)
  previous_cost?:  number;
  line_subtotal?:  number;
  tax_amount?:     number;
  line_total?:     number;
}

export interface GoodsReceivedNote {
  id:              number;
  creditor:        number;
  creditor_name?:  string;
  // System-set (read-only)
  transaction_number?: string;
  transaction_type?:   string;
  due_date?:           string;
  total_amount?:       number;
  grn_number?:         number;
  station?:            string;
  created_by_user?:    string;
  // User-entered
  transaction_date:        string;
  transaction_reference?:  string;
  additional_reference?:   string;
  supplier_invoice_number: string;
  inclusive_exclusive:     'INC' | 'EXC';
  surcharge_amount?:       number;
  // System totals (read-only)
  subtotal?:       number;
  total_vat?:      number;
  total_quantity?: number;
  // Aging buckets (read-only)
  age_current?: number;
  age_30?:      number;
  age_60?:      number;
  age_90?:      number;
  age_120?:     number;
  age_150?:     number;
  age_180?:     number;
  // Posting
  is_posted?: boolean;
  posted_at?: string;
  line_items?: GRNLineItem[];
}

export interface GoodsReceivedNoteCreateData {
  creditor:                number;
  transaction_date:        string;
  transaction_reference?:  string;
  additional_reference?:   string;
  supplier_invoice_number: string;
  inclusive_exclusive?:    'INC' | 'EXC';
  surcharge_amount?:       number;
  line_items:              GRNLineItem[];
}

// ============================================================================
// CREDITOR INVOICE  (expense invoices — suptran STYPE='IN')
// ============================================================================

export interface InvoiceLineItem {
  id?:                     number;
  line_number?:            number;
  expense_category:        number;
  expense_category_name?:  string;
  amount:                  number;
  tax_code:                number;
  tax_code_display?:       string;
  // System-calculated
  tax_amount?: number;
  line_total?: number;
}

export interface CreditorInvoice {
  id:             number;
  creditor:       number;
  creditor_name?: string;
  // System-set (read-only)
  transaction_number?: string;
  transaction_type?:   string;
  due_date?:           string;
  total_amount?:       number;
  station?:            string;
  created_by_user?:    string;
  // User-entered
  transaction_date:         string;
  transaction_reference?:   string;
  additional_reference?:    string;
  supplier_invoice_number:  string;
  inclusive_exclusive?:     'INC' | 'EXC';
  station_no_area?:         string;
  tax_indicator?:           number;  // 0=exempt, 1=taxable
  related_grn?:             number | null;
  // System totals (read-only)
  subtotal?:  number;
  total_vat?: number;
  // Aging buckets (read-only)
  age_current?: number;
  age_30?:      number;
  age_60?:      number;
  age_90?:      number;
  age_120?:     number;
  age_150?:     number;
  age_180?:     number;
  is_posted?:   boolean;
  posted_at?:   string;
  line_items?:  InvoiceLineItem[];
}

export interface CreditorInvoiceCreateData {
  creditor:                number;
  transaction_date:        string;
  transaction_reference?:  string;
  additional_reference?:   string;
  supplier_invoice_number: string;
  inclusive_exclusive?:    'INC' | 'EXC';
  station_no_area?:        string;
  tax_indicator?:          number;
  related_grn?:            number | null;
  line_items:              InvoiceLineItem[];
}

// ============================================================================
// CREDITOR CREDIT NOTE  (suptran STYPE='CN')
// ============================================================================

export interface CreditNoteLineItem {
  id?:               number;
  line_number?:      number;
  stock_item:        number;
  stock_code?:       string;
  quantity_returned: number;
  unit_cost:         number;
  tax_code:          number;
  tax_code_display?: string;
  // System-calculated
  line_subtotal?: number;
  tax_amount?:    number;
  line_total?:    number;
}

export interface CreditorCreditNote {
  id:             number;
  creditor:       number;
  creditor_name?: string;
  // System-set (read-only)
  transaction_number?: string;
  transaction_type?:   string;
  due_date?:           string;
  total_amount?:       number;
  station?:            string;
  created_by_user?:    string;
  // User-entered
  transaction_date:            string;
  transaction_reference?:      string;
  additional_reference?:       string;
  supplier_credit_note_number: string;
  inclusive_exclusive?:        'INC' | 'EXC';
  original_grn?:               number | null;
  // System totals (read-only)
  subtotal?:  number;
  total_vat?: number;
  // Aging buckets (read-only)
  age_current?: number;
  age_30?:      number;
  age_60?:      number;
  age_90?:      number;
  age_120?:     number;
  age_150?:     number;
  age_180?:     number;
  is_posted?:   boolean;
  posted_at?:   string;
  line_items?:  CreditNoteLineItem[];
}

export interface CreditorCreditNoteCreateData {
  creditor:                    number;
  transaction_date:            string;
  transaction_reference?:      string;
  additional_reference?:       string;
  supplier_credit_note_number: string;
  inclusive_exclusive?:        'INC' | 'EXC';
  original_grn?:               number | null;
  line_items:                  CreditNoteLineItem[];
}

// ============================================================================
// CREDITOR PAYMENT  (suptran STYPE='PY')
// ============================================================================

export interface CreditorPayment {
  id:             number;
  creditor:       number;
  creditor_name?: string;
  // System-set (read-only)
  transaction_number?: string;
  transaction_type?:   string;
  due_date?:           string;
  total_amount?:       number;
  station?:            string;
  created_by_user?:    string;
  // User-entered
  transaction_date:       string;
  transaction_reference?: string;
  additional_reference?:  string;
  amount_due:             number;
  amount_paid:            number;
  payment_method?:        number | null;
  payment_method_display?: string;
  is_unallocated?:        boolean;
  // System-calculated (read-only)
  settlement_discount_amount?:  number;
  settlement_discount_percent?: number;
  // Aging buckets (read-only)
  age_current?: number;
  age_30?:      number;
  age_60?:      number;
  age_90?:      number;
  age_120?:     number;
  age_150?:     number;
  age_180?:     number;
  is_posted?:   boolean;
  posted_at?:   string;
}

export interface CreditorPaymentCreateData {
  creditor:               number;
  transaction_date:       string;
  transaction_reference?: string;
  additional_reference?:  string;
  amount_due:             number;
  amount_paid:            number;
  payment_method?:        number | null;
  is_unallocated?:        boolean;
}

export interface PaymentAllocation {
  open_item:            number;
  amount_paid:          number;
  settlement_discount?: number;
}

// ============================================================================
// CREDITOR JOURNAL  (suptran STYPE='DJ' or 'CJ')
// ============================================================================

export interface CreditorJournal {
  id:             number;
  creditor:       number;
  creditor_name?: string;
  // System-set (read-only)
  transaction_number?: string;
  transaction_type?:   string;  // same as journal_type: 'DJ' or 'CJ'
  due_date?:           string;
  total_amount?:       number;
  station?:            string;
  created_by_user?:    string;
  // User-entered
  transaction_date:       string;
  transaction_reference?: string;
  additional_reference?:  string;
  journal_type:           'DJ' | 'CJ';  // DJ=Debit, CJ=Credit
  journal_amount:         number;
  // Aging buckets (read-only)
  age_current?: number;
  age_30?:      number;
  age_60?:      number;
  age_90?:      number;
  age_120?:     number;
  age_150?:     number;
  age_180?:     number;
  is_posted?:   boolean;
  posted_at?:   string;
}

export interface CreditorJournalCreateData {
  creditor:               number;
  transaction_date:       string;
  transaction_reference?: string;
  additional_reference?:  string;
  journal_type:           'DJ' | 'CJ';
  journal_amount:         number;
}

// ============================================================================
// SUPPLIER LEDGER ENTRY  (read-only — raw suptran.dbf)
// ============================================================================

export interface SupplierLedgerEntry {
  id:                number;
  creditor:          number;
  creditor_name?:    string;
  transaction_number:string;  // STRANO C(10)
  transaction_date:  string;  // STDATE
  due_date?:         string;  // SDUEDATE
  transaction_type:  string;  // STYPE C(2): GR/IN/CN/PY/DJ/CJ
  subtotal:          number;  // STSUB
  vat_amount:        number;  // STGST
  total_amount:      number;  // STTOT
  reference?:        string;  // STREF
  grn_number?:       number;  // GRNNO
  station?:          string;  // STATION
  created_by_user?:  string;  // USER
}

// ============================================================================
// OPEN ITEMS  (supopen.dbf)
// ============================================================================

export interface CreditorOpenItem {
  id:               number;
  creditor:         number;
  creditor_name?:   string;
  transaction_date: string;
  due_date?:        string;
  transaction_type: string;    // TYPE C(2)
  transaction_number: string;  // TRANO C(10)
  // System-maintained (read-only)
  original_amount:    number;
  balance_due:        number;
  age_period?:        number;
  ageing_flag?:       string;
  is_fully_allocated: boolean;
  is_legacy:          boolean;
  // FK links to typed transactions (one should be set for non-legacy records)
  grn?:          number | null;
  invoice?:      number | null;
  credit_note?:  number | null;
  journal?:      number | null;
  ledger_entry?: number | null;
  // Computed
  age_bucket?: string;
  created_at:  string;
  updated_at:  string;
}

export interface OpenItemAllocation {
  id?:                 number;
  payment:             number;
  payment_number?:     string;
  open_item:           number;
  open_item_number?:   string;
  amount_paid:         number;
  settlement_discount?: number;
  allocated_at?:       string;
}

// ============================================================================
// OPEN ITEM AUDIT  (read-only — supoaud.dbf)
// ============================================================================

export interface OpenItemAudit {
  id:                      number;
  creditor:                number;
  creditor_number?:        string;
  transaction_number:      string;  // TRANO C(10)
  transaction_type:        string;  // TYPE C(2)
  this_transaction_type:   string;  // THISTYPE C(2)
  this_transaction_number: number;  // THISTRAN N(6)
  transaction_date:        string;
  amount:                  number;  // AMOUNT N(14,2)
  audit_timestamp:         string;
  audit_notes?:            string;
}

// ============================================================================
// RFC — Return For Credit  (supcrmas + supcrtrn)
// ============================================================================

export type RFCStatus = 'PE' | 'CR' | 'RE' | 'CA';
// PE=Pending with Supplier, CR=Credit Note Received, RE=Stock Replaced, CA=Cancelled

export interface RFCLineItem {
  id?:                        number;
  line_number?:               number;
  stock_item:                 number;
  stock_code?:                string;
  quantity_returned:          number;  // QTYRFC N(10,2)
  quantity_credited?:         number | null; // QTYCRED N(10,2)
  quantity_stock?:            number;  // QTY N(10,2)
  line_value:                 number;  // VAL N(12,2) — from DBF directly
  tax_code:                   number;
  tax_code_display?:          string;
  rfc_line_date?:             string;
  rfc_line_time?:             string;  // "HH:MM" stored as char
  original_transaction_type?: string;
  original_transaction_date?: string;
  supplier_reference_number?: string;
  reason?:                    string;
  // System-calculated (read-only)
  unit_cost?:            number;
  line_value_exclusive?: number;
  tax_amount?:           number;
  line_value_inclusive?: number;
}

export interface RFC {
  id:             number;
  creditor:       number;
  creditor_name?: string;
  rfc_number:     string;  // RFCNO N(6) stored as char
  return_date?:   string;
  date_sent?:     string;  // DATESENT
  date_returned?: string;  // DATERETN
  status:         RFCStatus;
  // System-calculated (read-only)
  total_value_exclusive?: number;
  total_value_inclusive?: number;
  created_at?: string;
  updated_at?: string;
  line_items?: RFCLineItem[];
}

export interface RFCCreateData {
  creditor:       number;
  rfc_number:     string;
  return_date?:   string;
  date_sent?:     string;
  date_returned?: string;
  status?:        RFCStatus;
  line_items:     RFCLineItem[];
}

// ============================================================================
// EXPENSE CATEGORY MONTHLY BALANCE  (supexp.dbf)
// ============================================================================

export interface ExpenseCategoryMonthlyBalance {
  id:                       number;
  expense_category:         number;
  expense_category_display?: string;
  expense_category_name?:   string;  // EXPCATNAME C(20) — denormalised
  year:                     number;  // Django-only; not in DBF
  // System-accumulated (read-only)
  expense_mtd?:   number;
  input_vat_mtd?: number;
  exp_month_1?:   number;
  exp_month_2?:   number;
  exp_month_3?:   number;
  exp_month_4?:   number;
  exp_month_5?:   number;
  exp_month_6?:   number;
  exp_month_7?:   number;
  exp_month_8?:   number;
  exp_month_9?:   number;
  exp_month_10?:  number;
  exp_month_11?:  number;
  exp_month_12?:  number;
  annual_total?:  number;  // computed by serializer
}

// ============================================================================
// EXPENSE CATEGORY TRANSACTION  (supexpt.dbf)
// ============================================================================

export interface ExpenseCategoryTransaction {
  id:                       number;
  expense_category:         number;
  expense_category_display?: string;
  creditor:                 number;
  creditor_name?:           string;
  transaction_date:         string;
  transaction_number:       string;  // TRANO C(10)
  // User/source fields
  amount_exclusive:  number;         // VALUE N(10,2)
  tax_indicator:     number;         // TAXIND N(1): 0=no tax, 1=taxable
  source_type?:      string;         // SOURCE C(2)
  grn_number?:       number | null;  // GRNNO N(6)
  // System-calculated (read-only)
  input_vat_amount?: number;         // INVAT N(10,2)
  amount_inclusive?: number;         // TOTAL N(10,2)
  created_at?: string;
  updated_at?: string;
}

// ============================================================================
// SUPPLIER PAYMENT ORDER  (suppo.dbf)
// ============================================================================

export interface SupplierPaymentOrder {
  id:            number;
  creditor?:     number | null;  // nullable — no SUPNO in DBF
  creditor_name?: string;
  payment_date:  string;
  amount:        number;
  detail_line1?: string;
  detail_line2?: string;
  detail_line3?: string;
  // System-set by payment run (read-only)
  is_processed:   boolean;
  processed_date?: string;
}

export interface SupplierPaymentOrderCreateData {
  creditor?:     number | null;
  payment_date:  string;
  amount:        number;
  detail_line1?: string;
  detail_line2?: string;
  detail_line3?: string;
}

// ============================================================================
// SHARED / UTILITY TYPES
// ============================================================================

export interface PaginatedResponse<T> {
  count:     number;
  next?:     string | null;
  previous?: string | null;
  results:   T[];
}

export interface CreditorFilters {
  search?:           string;
  account_category?: 'B' | 'O' | '';
  is_active?:        boolean;
  page?:             number;
  page_size?:        number;
  ordering?:         string;
}

export interface TransactionFilters {
  creditor?:         number;
  is_posted?:        boolean;
  transaction_type?: string;
  search?:           string;
  start_date?:       string;
  end_date?:         string;
  page?:             number;
  page_size?:        number;
  ordering?:         string;
}

export interface CreditorsSummary {
  total_creditors:  number;
  total_payable:    number;
  balance_current:  number;  // was: current_aging
  balance_30_days:  number;  // was: d30
  balance_60_days:  number;  // was: d60
  balance_90_days:  number;  // was: d90
  balance_120_days: number;  // was: d120
  balance_150_days: number;
  balance_180_days: number;
  critical_aging:   number;
  average_dpo:      number;
}

// ── Expense category types (used by Settings API) ─────────────────────────
export interface ExpenseCategory {
  id:               number;
  category_number:  string;
  number?:          string;
  name:             string;
  category_type?:   string;
  is_active?:       boolean;
  transaction_count?: number;
  total_amount?:      number;
  total_tax?:         number;
  total_mtd?:         number;
  total_ytd?:         number;
  created_at?:        string;
  updated_at?:        string;
}

export interface ExpenseCategoryCreateData
  extends Omit<ExpenseCategory, 'id' | 'transaction_count' | 'total_amount' | 'total_tax' | 'total_mtd' | 'total_ytd' | 'created_at' | 'updated_at'> {}

export interface ExpenseCategoryFilters {
  search?:     string;
  page?:       number;
  page_size?:  number;
  start_date?: string;
  end_date?:   string;
  ordering?:   string;
}

// ── Outstanding Balance types ───────────────────────────────────────────────
export interface OutstandingBalance {
  id: number;
  creditor: number;
  creditor_name?: string;
  supplier_number?: string;
  supplier_account_number?: string;
  transaction_number?: string;
  transaction_date?: string;
  balance: number;
  balance_current?: number;
  balance_30_days?: number;
  balance_60_days?: number;
  balance_90_days?: number;
  balance_120_days?: number;
  balance_150_days?: number;
  balance_180_days?: number;
  original_amount?: number;
  balance_due?: number;
  age_period?: number;
  capture_date?: string;
  as_at_date: string;
  created_at?: string;
  updated_at?: string;
}

export interface OutstandingBalanceCaptureData {
  creditor: number;
  supplier_account_number?: string;
  capture_date?: string;
  as_at_date: string;
  balance: number;
  balance_current?: number;
  balance_30_days?: number;
  balance_60_days?: number;
  balance_90_days?: number;
  balance_120_days?: number;
  balance_150_days?: number;
  balance_180_days?: number;
}

// ── Legacy Transaction type — kept for backward compat with existing hooks ──
// New code should import the specific typed interface instead.
export interface Transaction {
  id:                  number;
  creditor?:           number;
  creditor_name?:      string;
  transaction_number?: string;
  transaction_type?:   string;  // 2-char STYPE code
  transaction_date?:   string;
  due_date?:           string;
  reference?:          string;
  total_amount?:       number;
  vat_amount?:         number;
  is_posted?:          boolean;
  created_at?:         string;
  updated_at?:         string;
}

export interface TransactionCreateData extends Omit<Transaction, 'id' | 'created_at' | 'updated_at'> {}