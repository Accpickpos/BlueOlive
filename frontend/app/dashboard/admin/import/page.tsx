'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useAuthContext, Shop as AuthShop } from '@/lib/AuthContext';
import { api } from '@/lib/api';
import { ENDPOINTS } from '@/lib/api-config';

// ============================================================
// Helper Functions
// ============================================================

// Helper to extract error message from axios error response
function getErrorMessage(err: any): string {
  // DRF returns errors in 'detail' for 403/404, or 'error' for custom errors
  const responseData = err?.response?.data;
  if (responseData?.detail) {
    return typeof responseData.detail === 'string' 
      ? responseData.detail 
      : JSON.stringify(responseData.detail);
  }
  if (responseData?.error) {
    return responseData.error;
  }
  // Fallback to message or default
  return err?.message || 'An unexpected error occurred';
}

// ============================================================
// Types
// ============================================================
interface Shop {
  id: number;
  name: string;
  code: string;
  schema_name: string;
}

interface TenantWithShops {
  id: number;
  name: string;
  slug: string;
  shops: Shop[];
}

interface AnalysisResult {
  headers: string[];
  total_rows: number;
  sample_rows: string[][];
  suggested_mappings: Record<string, string>;
  available_model_fields: string[];
  delimiter: string;
  model_type: string;
}

interface ImportProgress {
  status: 'started' | 'processing' | 'complete' | 'error';
  total: number;
  processed: number;
  created: number;
  updated: number;
  skipped: number;
  error_count?: number;
  message?: string;
  errors?: string[];
}

interface ImportResult {
  success: boolean;
  model_type: string;
  tenant: string;
  shop: string;
  schema: string;
  total_rows: number;
  created: number;
  updated: number;
  skipped: number;
  errors: string[];
  message: string;
}

type ImportMode = 'create_or_update' | 'create_only' | 'update_only';
type Step = 'select' | 'upload' | 'map' | 'importing' | 'done';
type DataType = 
  | 'debtor' 
  | 'creditor' 
  | 'stock' 
  | 'department' 
  | 'debtran' 
  | 'debtopen' 
  | 'debtoaud' 
  | 'dpdc' 
  | 'suptran' 
  | 'supopen' 
  | 'supoaud' 
  | 'supcrmas' 
  | 'supcrtrn' 
  | 'suppo' 
  | 'supexp' 
  | 'supexpt' 
  | 'stran';

// Model field labels for each data type
const FIELD_LABELS: Record<string, Record<string, string>> = {
  debtor: {
    dno: 'Account Number (DNO)',
    dname: 'Customer Name',
    dsname: 'Short Name',
    dcontact: 'Contact Person',
    dtel: 'Phone',
    dtel2: 'Phone 2',
    dfax: 'Fax',
    email: 'Email',
    address_line1: 'Address Line 1',
    address_line2: 'Address Line 2',
    address_line3: 'Address Line 3',
    postal_code: 'Postal Code',
    delivery_address1: 'Delivery Address 1',
    delivery_address2: 'Delivery Address 2',
    delivery_address3: 'Delivery Address 3',
    delivery_address4: 'Delivery Address 4',
    dtaxno: 'Tax Number',
    vatref: 'VAT Reference',
    darea: 'Sales Area',
    dbalbfwd: 'Balance B/F',
    dcrnt: 'Current Balance',
    d30: '30 Days',
    d60: '60 Days',
    d90: '90 Days',
    d120: '120 Days',
    d150: '150 Days',
    d180: '180 Days',
    dsalesm: 'Sales (Month)',
    dsalesy: 'Sales (Year)',
    dprofitm: 'Profit (Month)',
    dprofity: 'Profit (Year)',
    damtlpd: 'Last Payment Amount',
    ddatlpd: 'Last Payment Date',
    ddiscper: 'Discount %',
    dclimit: 'Credit Limit',
    dintflag: 'Charge Interest',
    price: 'Price Level',
    acctype: 'Account Type',
    terms: 'Payment Terms',
    pdisc: 'Prompt Discount %',
    discount_printable: 'Print Discount',
    dposbal: 'Positive Balance Only',
    blockflag: 'Block Flag',
    dateopened: 'Date Opened',
    notes: 'Notes',
  },
  creditor: {
    supplier_number: 'Supplier Number',
    name: 'Supplier Name',
    contact_person: 'Contact Person',
    telephone: 'Telephone',
    fax: 'Fax',
    email: 'Email',
    physical_address_line1: 'Physical Address 1',
    physical_address_line2: 'Physical Address 2',
    physical_address_line3: 'Physical Address 3',
    postal_address_line1: 'Postal Address 1',
    postal_address_line2: 'Postal Address 2',
    postal_address_line3: 'Postal Address 3',
    our_account_number: 'Our Account Number',
    payment_terms_days: 'Payment Terms (Days)',
    account_category: 'Account Category',
    sales_area: 'Sales Area',
    prompt_payment_discount_percent: 'Prompt Discount %',
    bank_name: 'Bank Name',
    branch_code: 'Branch Code',
    account_number: 'Account Number',
    balance_brought_forward: 'Balance B/F',
    balance_current: 'Current Balance',
    balance_30_days: '30 Days',
    balance_60_days: '60 Days',
    balance_90_days: '90 Days',
    balance_120_days: '120 Days',
    balance_150_days: '150 Days',
    balance_180_days: '180 Days',
    last_paid_amount: 'Last Paid Amount',
    last_paid_date: 'Last Paid Date',
    purchases_mtd: 'Purchases (MTD)',
    purchases_ytd: 'Purchases (YTD)',
    update_selling_price_on_receipt: 'Update Selling Price',
    is_active: 'Active',
  },
  stock: {
    stock_code: 'Stock Code',
    description: 'Description',
    department: 'Department',
    supplier: 'Supplier',
    supplier_code: 'Supplier Code',
    tax_code: 'Tax Code',
    cost_price: 'Cost Price',
    average_cost: 'Average Cost',
    selling_price_1: 'Selling Price 1',
    selling_price_2: 'Selling Price 2',
    selling_price_3: 'Selling Price 3',
    markup_1: 'Markup 1',
    markup_2: 'Markup 2',
    markup_3: 'Markup 3',
    quantity_on_hand: 'Quantity on Hand',
    quantity_allocated: 'Quantity Allocated',
    quantity_sale_order: 'Sale Order Qty',
    quantity_counted: 'Counted Qty',
    reorder_quantity: 'Reorder Quantity',
    quantity_on_order: 'On Order Qty',
    default_selling_quantity: 'Default Qty',
    allow_negative_quantities: 'Allow Negative',
    maximum_discount_percent: 'Max Discount %',
    sales_mtd_quantity: 'Sales MTD Qty',
    sales_mtd_value: 'Sales MTD Value',
    sales_ytd_quantity: 'Sales YTD Qty',
    sales_ytd_value: 'Sales YTD Value',
    gross_profit_mtd: 'GP MTD',
    gross_profit_ytd: 'GP YTD',
    purchased_mtd_quantity: 'Purchased MTD',
    purchased_ytd_quantity: 'Purchased YTD',
    balance_bfwd_quantity: 'BFwd Qty',
    balance_bfwd_value: 'BFwd Value',
    closing_stock_balance: 'Closing Balance',
    date_last_purchased: 'Last Purchased',
    date_last_sold: 'Last Sold',
    bin_number: 'Bin Number',
    weight: 'Weight',
    stock_count_flag: 'Count Flag',
    is_active: 'Active',
  },
  department: {
    number: 'Department Number',
    name: 'Department Name',
    sales_mtd: 'Sales MTD',
    sales_p1: 'Sales Period 1',
    sales_p2: 'Sales Period 2',
    sales_p3: 'Sales Period 3',
    sales_p4: 'Sales Period 4',
    sales_p5: 'Sales Period 5',
    sales_p6: 'Sales Period 6',
    sales_p7: 'Sales Period 7',
    sales_p8: 'Sales Period 8',
    sales_p9: 'Sales Period 9',
    sales_p10: 'Sales Period 10',
    sales_p11: 'Sales Period 11',
    sales_p12: 'Sales Period 12',
  },
  debtran: {
    debtor: 'Customer Number (DNO)',
    transaction_number: 'Transaction Number',
    transaction_date: 'Transaction Date',
    transaction_time: 'Transaction Time',
    transaction_type: 'Transaction Type',
    subtotal: 'Subtotal',
    vat_amount: 'VAT Amount',
    total_amount: 'Total Amount',
    vat_status: 'VAT Status',
    source_station: 'Source Station',
    order_number: 'Order Number',
    customer_reference: 'Customer Reference',
    description_line1: 'Description Line 1',
    description_line2: 'Description Line 2',
    description_line3: 'Description Line 3',
    description_line4: 'Description Line 4',
    station: 'Station',
    vat_reference: 'VAT Reference',
  },
  debtopen: {
    debtor: 'Customer Number (DNO)',
    transaction_number: 'Transaction Number',
    transaction_type: 'Transaction Type',
    transaction_date: 'Transaction Date',
    original_amount: 'Original Amount',
    balance_due: 'Balance Due',
    age_flag: 'Age Flag',
    posted: 'Posted',
  },
  debtoaud: {
    debtor: 'Customer Number (DNO)',
    transaction_number: 'Transaction Number',
    transaction_type: 'Transaction Type',
    current_type: 'Current Type',
    current_transaction: 'Current Transaction',
    audit_date: 'Audit Date',
    amount: 'Amount',
  },
  dpdc: {
    dno: 'Customer Number (DNO)',
    date: 'Date',
    amount: 'Amount',
    status: 'Status',
  },
  suptran: {
    creditor: 'Supplier Number (SUPNO)',
    transaction_number: 'Transaction Number',
    transaction_date: 'Transaction Date',
    due_date: 'Due Date',
    transaction_type: 'Transaction Type',
    subtotal: 'Subtotal',
    vat_amount: 'VAT Amount',
    total_amount: 'Total Amount',
    reference: 'Reference',
    grn_number: 'GRN Number',
    station: 'Station',
    created_by_user: 'Created By User',
  },
  supopen: {
    creditor: 'Supplier Number (SUPNO)',
    transaction_number: 'Transaction Number',
    transaction_type: 'Transaction Type',
    transaction_date: 'Transaction Date',
    original_amount: 'Original Amount',
    balance_due: 'Balance Due',
    ageing_flag: 'Ageing Flag',
  },
  supoaud: {
    creditor: 'Supplier Number (SUPNO)',
    transaction_number: 'Transaction Number',
    transaction_type: 'Transaction Type',
    this_transaction_type: 'This Transaction Type',
    this_transaction_number: 'This Transaction Number',
    transaction_date: 'Transaction Date',
    amount: 'Amount',
  },
  supcrmas: {
    rfc_number: 'RFC Number',
    creditor: 'Supplier Number (SUPNO)',
    date_sent: 'Date Sent',
    date_returned: 'Date Returned',
    status: 'Status',
  },
  supcrtrn: {
    rfc: 'RFC Number',
    original_transaction_type: 'Original Transaction Type',
    stock_item: 'Stock Code',
    rfc_line_date: 'RFC Line Date',
    rfc_line_time: 'RFC Line Time',
    quantity_stock: 'Quantity Stock',
    line_value: 'Line Value',
    quantity_returned: 'Quantity Returned',
    quantity_credited: 'Quantity Credited',
    reason: 'Reason',
    original_transaction_date: 'Original Transaction Date',
    supplier_reference_number: 'Supplier Reference Number',
  },
  suppo: {
    payment_date: 'Payment Date',
    amount: 'Amount',
    detail_line1: 'Detail Line 1',
    detail_line2: 'Detail Line 2',
    detail_line3: 'Detail Line 3',
  },
  supexp: {
    expense_category: 'Expense Category',
    expense_category_name: 'Expense Category Name',
    expense_mtd: 'Expense MTD',
    input_vat_mtd: 'Input VAT MTD',
    exp_month_1: 'Expense Month 1',
    exp_month_2: 'Expense Month 2',
    exp_month_3: 'Expense Month 3',
    exp_month_4: 'Expense Month 4',
    exp_month_5: 'Expense Month 5',
    exp_month_6: 'Expense Month 6',
    exp_month_7: 'Expense Month 7',
    exp_month_8: 'Expense Month 8',
    exp_month_9: 'Expense Month 9',
    exp_month_10: 'Expense Month 10',
    exp_month_11: 'Expense Month 11',
    exp_month_12: 'Expense Month 12',
  },
  supexpt: {
    expense_category: 'Expense Category',
    transaction_date: 'Transaction Date',
    transaction_number: 'Transaction Number',
    creditor: 'Supplier Number (SUPNO)',
    amount_exclusive: 'Amount Exclusive',
    source_type: 'Source Type',
    grn_number: 'GRN Number',
    tax_indicator: 'Tax Indicator',
  },
  stran: {
    transaction_number: 'Transaction Number',
    stock_item: 'Stock Code',
    quantity_in: 'Quantity In',
    quantity_out: 'Quantity Out',
    discount: 'Discount',
    value: 'Value',
    transaction_type: 'Transaction Type',
    transaction_date: 'Transaction Date',
    transaction_time: 'Transaction Time',
    department: 'Department',
    unit_cost: 'Unit Cost',
    tax_code: 'Tax Code',
    station_number: 'Station Number',
    debtor: 'Customer Number (DNO)',
    supplier: 'Supplier Number (SUPNO)',
    comments: 'Comments',
    unit_price: 'Unit Price',
  },
};

// Required field for each data type
const REQUIRED_FIELD: Record<DataType, string> = {
  debtor: 'dno',
  creditor: 'supplier_number',
  stock: 'stock_code',
  department: 'number',
  debtran: 'transaction_number',
  debtopen: 'transaction_number',
  debtoaud: 'transaction_number',
  dpdc: 'dno',
  suptran: 'transaction_number',
  supopen: 'transaction_number',
  supoaud: 'transaction_number',
  supcrmas: 'rfc_number',
  supcrtrn: 'rfc',
  suppo: 'payment_date',
  supexp: 'expense_category',
  supexpt: 'transaction_number',
  stran: 'transaction_number',
};

// Labels for data types
const DATA_TYPE_INFO: Record<DataType, { label: string; icon: string; help: string; file: string; category: string }> = {
  debtor: { 
    label: 'Debtors', 
    icon: 'Users', 
    help: 'Import customer/debtor accounts',
    file: 'dmast.csv',
    category: 'Master Data'
  },
  creditor: { 
    label: 'Creditors', 
    icon: 'Building', 
    help: 'Import supplier/creditor accounts',
    file: 'supmast.csv',
    category: 'Master Data'
  },
  stock: { 
    label: 'Stock Items', 
    icon: 'Package', 
    help: 'Import inventory/stock items',
    file: 'smast.csv',
    category: 'Master Data'
  },
  department: { 
    label: 'Departments', 
    icon: 'Folder', 
    help: 'Import sales departments',
    file: 'dept.csv',
    category: 'Master Data'
  },
  debtran: { 
    label: 'Debtor Transactions', 
    icon: 'ArrowRight', 
    help: 'Import debtor transactions (also dtran.csv)',
    file: 'debtran.csv',
    category: 'Debtor Transactions'
  },
  debtopen: { 
    label: 'Debtor Open Items', 
    icon: 'FileText', 
    help: 'Import debtor open/aging items',
    file: 'debtopen.csv',
    category: 'Debtor Transactions'
  },
  debtoaud: { 
    label: 'Debtor Audit', 
    icon: 'History', 
    help: 'Import debtor audit trail',
    file: 'debtoaud.csv',
    category: 'Debtor Transactions'
  },
  dpdc: { 
    label: 'Debtor PDC', 
    icon: 'CreditCard', 
    help: 'Import debtor post-dated checks',
    file: 'dpdc.csv',
    category: 'Debtor Transactions'
  },
  suptran: { 
    label: 'Supplier Transactions', 
    icon: 'ArrowLeft', 
    help: 'Import supplier ledger transactions',
    file: 'suptran.csv',
    category: 'Creditor Transactions'
  },
  supopen: { 
    label: 'Supplier Open Items', 
    icon: 'FileText', 
    help: 'Import supplier open/aging items',
    file: 'supopen.csv',
    category: 'Creditor Transactions'
  },
  supoaud: { 
    label: 'Supplier Audit', 
    icon: 'History', 
    help: 'Import supplier audit trail',
    file: 'supoaud.csv',
    category: 'Creditor Transactions'
  },
  supcrmas: { 
    label: 'RFC Master', 
    icon: 'RefreshCw', 
    help: 'Import returns/faults credit requests',
    file: 'supcrmas.csv',
    category: 'Creditor Transactions'
  },
  supcrtrn: { 
    label: 'RFC Line Items', 
    icon: 'List', 
    help: 'Import RFC line items',
    file: 'supcrtrn.csv',
    category: 'Creditor Transactions'
  },
  suppo: { 
    label: 'Supplier Payments', 
    icon: 'DollarSign', 
    help: 'Import supplier payment orders',
    file: 'suppo.csv',
    category: 'Creditor Transactions'
  },
  supexp: { 
    label: 'Expense Categories', 
    icon: 'PieChart', 
    help: 'Import expense category monthly balances',
    file: 'supexp.csv',
    category: 'Creditor Transactions'
  },
  supexpt: { 
    label: 'Expense Transactions', 
    icon: 'Receipt', 
    help: 'Import expense category transactions',
    file: 'supexpt.csv',
    category: 'Creditor Transactions'
  },
  stran: { 
    label: 'Stock Transactions', 
    icon: 'Repeat', 
    help: 'Import stock movements/transactions',
    file: 'stran.csv',
    category: 'Stock Transactions'
  },
};

export default function ImportDataPage() {
  // --- State ---
  const { user, currentShop, accessibleShops, isLoading: authLoading } = useAuthContext();
  const [step, setStep] = useState<Step>('select');
  const [tenants, setTenants] = useState<TenantWithShops[]>([]);
  const [selectedTenantId, setSelectedTenantId] = useState<number | null>(null);
  const [selectedShopId, setSelectedShopId] = useState<number | null>(null);
  const [dataType, setDataType] = useState<DataType>('debtor');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // File & analysis
  const [file, setFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);

  // Mappings: csv_header → model_field | '' (unmapped)
  const [mappings, setMappings] = useState<Record<string, string>>({});

  // Import
  const [importMode, setImportMode] = useState<ImportMode>('create_or_update');
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [importProgress, setImportProgress] = useState<ImportProgress | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Derived
  const selectedTenant = tenants.find(t => t.id === selectedTenantId) ?? null;
  const shops = selectedTenant?.shops ?? [];
  const selectedShop = shops.find(s => s.id === selectedShopId) ?? null;

  // ============================================================
  // Step 1: Load tenants from AuthContext
  // ============================================================
  const loadTenants = useCallback(() => {
    // Use accessibleShops from AuthContext
    if (accessibleShops.length > 0) {
      const mappedShops: Shop[] = accessibleShops.map((s: AuthShop) => ({
        id: s.id,
        name: s.name,
        code: s.schema_name || `shop_${s.id}`,
        schema_name: s.schema_name
      }));

      const tenantId = user?.tenant_id || 1;
      
      setTenants([{
        id: tenantId,
        name: 'Current Tenant',
        slug: 'current',
        shops: mappedShops
      }]);
      
      setSelectedTenantId(tenantId);
      
      // Select current shop if available, otherwise first shop
      if (currentShop) {
        setSelectedShopId(currentShop.id);
      } else if (mappedShops.length > 0) {
        setSelectedShopId(mappedShops[0].id);
      }
    } else if (!authLoading) {
      setError('No accessible shops found. Please check your permissions.');
    }
  }, [accessibleShops, user, currentShop, authLoading]);

  // Load tenants on first render after auth
  useEffect(() => {
    if (!authLoading) {
      loadTenants();
    }
  }, [authLoading, loadTenants]);

  // ============================================================
  // Step 2: Upload & analyze
  // ============================================================
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    setAnalysis(null);
    setMappings({});
    setImportResult(null);
    setError(null);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('model_type', dataType);
      
      const res = await api.post<AnalysisResult>(ENDPOINTS.SAAS_ADMIN.IMPORT_ANALYZE, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setAnalysis(res.data);
      setMappings(res.data.suggested_mappings);
      setStep('map');
    } catch (err: any) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // Step 3: Execute import
  // ============================================================
  const handleImport = async () => {
    if (!file || !selectedTenantId || !selectedShopId) return;

    // Filter out unmapped columns
    const activeMappings: Record<string, string> = {};
    const mappingsSource = mappings || {};
    for (const [csvCol, field] of Object.entries(mappingsSource)) {
      if (field) activeMappings[csvCol] = field;
    }

    const requiredField = REQUIRED_FIELD[dataType];
    if (!Object.values(activeMappings).includes(requiredField)) {
      setError(`You must map a column to "${requiredField}" — it is required.`);
      return;
    }

    setStep('importing');
    setLoading(true);
    setError(null);
    setImportResult(null);
    setImportProgress(null);

    try {
      const form = new FormData();
      form.append('file', file);
      form.append('tenant_id', String(selectedTenantId));
      form.append('shop_id', String(selectedShopId));
      form.append('mappings', JSON.stringify(activeMappings));
      form.append('model_type', dataType);
      form.append('mode', importMode);

      // Use fetch with streaming response
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}${ENDPOINTS.SAAS_ADMIN.IMPORT_EXECUTE}`, {
        method: 'POST',
        body: form,
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Import failed: ${response.status}`);
      }

      // Read streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (!reader) {
        throw new Error('Failed to read response');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.trim()) {
            try {
              const progress: ImportProgress = JSON.parse(line);
              setImportProgress(progress);

              if (progress.status === 'complete') {
                // Convert to ImportResult format
                setImportResult({
                  success: true,
                  model_type: dataType,
                  tenant: '',
                  shop: '',
                  schema: '',
                  total_rows: progress.total,
                  created: progress.created,
                  updated: progress.updated,
                  skipped: progress.skipped,
                  errors: progress.errors || [],
                  message: `Import complete: ${progress.created} created, ${progress.updated} updated, ${progress.skipped} skipped`,
                });
              } else if (progress.status === 'error') {
                throw new Error(progress.message || 'Import failed');
              }
            } catch (e) {
              // Ignore parse errors for incomplete lines
            }
          }
        }
      }

      setStep('done');
    } catch (err: any) {
      setError(getErrorMessage(err));
      setStep('map');
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // Reset
  // ============================================================
  const handleReset = () => {
    setStep('select');
    setFile(null);
    setAnalysis(null);
    setMappings({});
    setImportResult(null);
    setError(null);
    setImportMode('create_or_update');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ============================================================
  // Render helpers
  // ============================================================
  const mappingsObj = mappings || {};
  const mappedCount = Object.values(mappingsObj).filter(Boolean).length;
  const hasRequiredField = Object.values(mappingsObj).includes(REQUIRED_FIELD[dataType]);
  const currentLabels = FIELD_LABELS[dataType];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Import Data from CSV</h1>
        <p className="text-gray-500">
          Upload a CSV file and import debtor, creditor, or stock data into a specific tenant shop schema.
        </p>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-4 rounded-lg border border-red-300 bg-red-50 p-4 text-red-800 flex items-start gap-2">
          <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/></svg>
          <span>{error}</span>
        </div>
      )}

      {/* Loading state */}
      {authLoading && (
        <div className="mb-4 rounded-lg border border-blue-300 bg-blue-50 p-4 text-blue-800 flex items-center gap-2">
          <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>Loading...</span>
        </div>
      )}

      {/* Success banner */}
      {importResult && step === 'done' && (
        <div className="mb-4 rounded-lg border border-green-300 bg-green-50 p-4 text-green-800">
          <div className="flex items-center gap-2 font-semibold">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/></svg>
            {importResult.message}
          </div>
          <div className="mt-2 text-sm">
            Created: {importResult.created} | Updated: {importResult.updated} | Skipped: {importResult.skipped}
          </div>
          {importResult.errors && importResult.errors.length > 0 && (
            <div className="mt-2 max-h-32 overflow-y-auto text-sm">
              <p className="font-medium">Errors:</p>
              <ul className="list-disc list-inside">
                {importResult.errors.slice(0, 5).map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
                {importResult.errors.length > 5 && (
                  <li>...and {importResult.errors.length - 5} more errors</li>
                )}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Step indicator */}
      <div className="flex items-center gap-1 mb-8">
        {(['select', 'upload', 'map', 'done'] as const).map((s, i) => {
          const labels = ['1. Select Target', '2. Upload CSV', '3. Map & Import', '4. Done'];
          const active = step === s || (step === 'importing' && s === 'map');
          const completed =
            (s === 'select' && ['upload', 'map', 'importing', 'done'].includes(step)) ||
            (s === 'upload' && ['map', 'importing', 'done'].includes(step)) ||
            (s === 'map' && step === 'done');
          return (
            <div key={s} className="flex items-center gap-1 flex-1">
              <div
                className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold border-2 ${
                  completed
                    ? 'bg-green-600 border-green-600 text-white'
                    : active
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'bg-white border-gray-300 text-gray-400'
                }`}
              >
                {completed ? '✓' : i + 1}
              </div>
              <span className={`text-sm ${active || completed ? 'text-gray-900 font-medium' : 'text-gray-400'}`}>
                {labels[i]}
              </span>
              {i < 3 && <div className={`flex-1 h-0.5 mx-2 ${completed ? 'bg-green-500' : 'bg-gray-200'}`} />}
            </div>
          );
        })}
      </div>

      {/* =============================== */}
      {/* Step 1: Select Data Type, Tenant & Shop */}
      {/* =============================== */}
      {step === 'select' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
          {/* Data Type Selection */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Select Data Type to Import</h2>
            
            {/* Master Data */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-500 mb-2 uppercase tracking-wider">Master Data</h3>
              <div className="grid grid-cols-4 gap-4">
                {(['debtor', 'creditor', 'stock', 'department'] as DataType[]).map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setDataType(type)}
                    className={`p-4 border-2 rounded-lg flex flex-col items-center gap-2 transition ${
                      dataType === type
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      {type === 'debtor' && <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />}
                      {type === 'creditor' && <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />}
                      {type === 'stock' && <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />}
                      {type === 'department' && <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />}
                    </svg>
                    <span className="font-medium">{DATA_TYPE_INFO[type].label}</span>
                    <span className="text-xs text-gray-500">{DATA_TYPE_INFO[type].file}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Debtor Transactions */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-500 mb-2 uppercase tracking-wider">Debtor Transactions</h3>
              <div className="grid grid-cols-4 gap-4">
                {(['debtran', 'debtopen', 'debtoaud', 'dpdc'] as DataType[]).map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setDataType(type)}
                    className={`p-4 border-2 rounded-lg flex flex-col items-center gap-2 transition ${
                      dataType === type
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5v6l-3 3" />
                    </svg>
                    <span className="font-medium">{DATA_TYPE_INFO[type].label}</span>
                    <span className="text-xs text-gray-500">{DATA_TYPE_INFO[type].file}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Creditor Transactions */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-500 mb-2 uppercase tracking-wider">Creditor/Supplier Transactions</h3>
              <div className="grid grid-cols-4 gap-4">
                {(['suptran', 'supopen', 'supoaud', 'supcrmas', 'supcrtrn', 'suppo', 'supexp', 'supexpt'] as DataType[]).map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setDataType(type)}
                    className={`p-4 border-2 rounded-lg flex flex-col items-center gap-2 transition ${
                      dataType === type
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6h18M3 12h18M3 18h18" />
                    </svg>
                    <span className="font-medium">{DATA_TYPE_INFO[type].label}</span>
                    <span className="text-xs text-gray-500">{DATA_TYPE_INFO[type].file}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Stock Transactions */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-500 mb-2 uppercase tracking-wider">Stock Transactions</h3>
              <div className="grid grid-cols-4 gap-4">
                {(['stran'] as DataType[]).map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setDataType(type)}
                    className={`p-4 border-2 rounded-lg flex flex-col items-center gap-2 transition ${
                      dataType === type
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h5" />
                    </svg>
                    <span className="font-medium">{DATA_TYPE_INFO[type].label}</span>
                    <span className="text-xs text-gray-500">{DATA_TYPE_INFO[type].file}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Tenant & Shop Selection */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Select Target Tenant & Shop</h2>
            <p className="text-sm text-gray-500 mb-4">
              Choose which tenant and shop schema to import {DATA_TYPE_INFO[dataType].label.toLowerCase()} into.
            </p>

            {loading || authLoading ? (
              <div className="py-8 text-center text-gray-400">Loading tenants...</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Tenant select */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tenant</label>
                  <select
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={selectedTenantId ?? ''}
                    onChange={e => {
                      const id = Number(e.target.value) || null;
                      setSelectedTenantId(id);
                      setSelectedShopId(null);
                    }}
                  >
                    <option value="">-- Select tenant --</option>
                    {tenants.map(t => (
                      <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                  </select>
                </div>

                {/* Shop select */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Shop Schema</label>
                  <select
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={selectedShopId ?? ''}
                    onChange={e => setSelectedShopId(Number(e.target.value) || null)}
                    disabled={!selectedTenantId || authLoading}
                  >
                    <option value="">-- Select shop --</option>
                    {shops.map(s => (
                      <option key={s.id} value={s.id}>
                        {s.name} ({s.schema_name})
                      </option>
                    ))}
                  </select>
                  {selectedShop && (
                    <p className="mt-1 text-xs text-gray-400">
                      Schema: <span className="font-mono text-gray-600">{selectedShop.schema_name}</span>
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="pt-2 flex justify-end">
            <button
              disabled={!selectedTenantId || !selectedShopId || authLoading}
              onClick={() => setStep('upload')}
              className="px-5 py-2 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              Next: Upload CSV →
            </button>
          </div>
        </div>
      )}

      {/* =============================== */}
      {/* Step 2: Upload CSV */}
      {/* =============================== */}
      {step === 'upload' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Upload CSV File</h2>
            <div className="text-sm text-gray-500">
              Target: <strong>{selectedTenant?.name}</strong> → <strong>{selectedShop?.name}</strong>
              <span className="font-mono text-xs text-gray-400 ml-1">({selectedShop?.schema_name})</span>
            </div>
          </div>

          <div className="border-2 border-dashed border-gray-300 rounded-xl p-10 text-center hover:border-blue-400 transition">
            <svg className="mx-auto h-12 w-12 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="block mx-auto text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <p className="mt-2 text-xs text-gray-400">CSV files only. Semicolon or comma delimited.</p>
          </div>

          {file && (
            <div className="bg-blue-50 rounded-lg p-3 flex items-center gap-3 text-sm">
              <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd"/></svg>
              <span className="text-blue-800 font-medium">{file.name}</span>
              <span className="text-blue-500">({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
          )}

          <div className="pt-2 flex justify-between">
            <button
              onClick={() => setStep('select')}
              className="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition"
            >
              ← Back
            </button>
            <button
              disabled={!file || loading}
              onClick={handleAnalyze}
              className="px-5 py-2 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-2"
            >
              {loading && <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />}
              Analyze & Map Columns →
            </button>
          </div>
        </div>
      )}

      {/* =============================== */}
      {/* Step 3: Map columns & import */}
      {/* =============================== */}
      {(step === 'map' || step === 'importing') && analysis && (
        <div className="space-y-6">
          {/* Summary bar */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex flex-wrap items-center gap-4 text-sm">
            <div>
              File: <strong>{file?.name}</strong>
            </div>
            <div className="text-gray-400">|</div>
            <div>
              Data Type: <strong>{DATA_TYPE_INFO[dataType as DataType].label}</strong>
            </div>
            <div className="text-gray-400">|</div>
            <div>
              Rows: <strong>{analysis?.total_rows ?? 0}</strong>
            </div>
            <div className="text-gray-400">|</div>
            <div>
              Columns: <strong>{analysis?.headers?.length ?? 0}</strong>
            </div>
            <div className="text-gray-400">|</div>
            <div>
              Mapped: <strong className={hasRequiredField ? 'text-green-600' : 'text-red-600'}>{mappedCount}</strong>
              / {analysis?.headers?.length ?? 0}
            </div>
            <div className="text-gray-400">|</div>
            <div>
              Target: <strong>{selectedTenant?.name}</strong> → <strong>{selectedShop?.name}</strong>
            </div>
          </div>

          {/* Column mapping */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Column Mapping</h2>
              <span className="text-xs text-gray-400">Select which model field each CSV column maps to</span>
            </div>

            <div className="overflow-x-auto max-h-[420px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 sticky top-0 z-10">
                  <tr>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">CSV Column</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">→ Model Field</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Sample Values</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {analysis.headers.map((header, idx) => (
                    <tr key={header} className={(mappingsObj || {})[header] ? 'bg-green-50/50' : ''}>
                      <td className="px-4 py-2 font-mono text-xs text-gray-700">{header}</td>
                      <td className="px-4 py-2">
                        <select
                          value={(mappingsObj || {})[header] || ''}
                          onChange={e => setMappings(prev => ({ ...prev, [header]: e.target.value }))}
                          className={`w-full rounded border px-2 py-1 text-xs ${
                            (mappingsObj || {})[header] === REQUIRED_FIELD[dataType]
                              ? 'border-green-500 bg-green-50 font-bold'
                              : (mappingsObj || {})[header]
                              ? 'border-green-300'
                              : 'border-gray-300'
                          }`}
                        >
                          <option value="">-- skip --</option>
                          {(analysis.available_model_fields || []).map(field => (
                            <option key={field} value={field}>
                              {currentLabels[field] || field}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-2 text-xs text-gray-400 max-w-xs truncate">
                        {analysis.sample_rows.slice(0, 3).map(r => r[idx] ?? '').join(' | ')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Import options */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 space-y-4">
            <h3 className="text-sm font-semibold text-gray-700">Import Mode</h3>
            <div className="flex gap-4 flex-wrap">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name="importMode"
                  value="create_or_update"
                  checked={importMode === 'create_or_update'}
                  onChange={(e) => setImportMode(e.target.value as ImportMode)}
                  className="h-4 w-4 text-blue-600"
                />
                <span className="text-sm">Create or Update (recommended)</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name="importMode"
                  value="create_only"
                  checked={importMode === 'create_only'}
                  onChange={(e) => setImportMode(e.target.value as ImportMode)}
                  className="h-4 w-4 text-blue-600"
                />
                <span className="text-sm">Create Only (skip existing)</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name="importMode"
                  value="update_only"
                  checked={importMode === 'update_only'}
                  onChange={(e) => setImportMode(e.target.value as ImportMode)}
                  className="h-4 w-4 text-blue-600"
                />
                <span className="text-sm">Update Only (skip new)</span>
              </label>
            </div>

            <div className="flex gap-4 pt-2">
              <button
                onClick={() => setStep('upload')}
                disabled={loading}
                className="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition disabled:opacity-40"
              >
                ← Back
              </button>
              <button
                onClick={handleImport}
                disabled={!hasRequiredField || loading}
                className="px-6 py-2 rounded-lg text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-2"
              >
                {loading && <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />}
                {loading ? 'Importing...' : 'Start Import'}
              </button>
              <button
                onClick={handleReset}
                disabled={loading}
                className="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition"
              >
                Reset
              </button>
            </div>

            {/* Progress bar during import */}
            {step === 'importing' && importProgress && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-blue-900">
                    {importProgress.status === 'started' && 'Starting import...'}
                    {importProgress.status === 'processing' && 'Importing data...'}
                    {importProgress.status === 'complete' && 'Import complete!'}
                  </span>
                  <span className="text-sm text-blue-700">
                    {importProgress.processed} / {importProgress.total} rows
                  </span>
                </div>
                <div className="w-full bg-blue-200 rounded-full h-3">
                  <div
                    className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${Math.round((importProgress.processed / importProgress.total) * 100)}%` }}
                  />
                </div>
                <div className="flex justify-between mt-2 text-xs text-blue-700">
                  <span>Created: {importProgress.created}</span>
                  <span>Updated: {importProgress.updated}</span>
                  <span>Skipped: {importProgress.skipped}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* =============================== */}
      {/* Step 4: Done */}
      {/* =============================== */}
      {step === 'done' && importResult && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-100 flex items-center justify-center">
              <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900">Import Complete!</h2>
            <p className="text-gray-500 mt-2">{importResult.message}</p>
          </div>

          <div className="grid grid-cols-4 gap-4 text-center">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{importResult.total_rows}</div>
              <div className="text-sm text-gray-500">Total Rows</div>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{importResult.created}</div>
              <div className="text-sm text-gray-500">Created</div>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{importResult.updated}</div>
              <div className="text-sm text-gray-500">Updated</div>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">{importResult.skipped}</div>
              <div className="text-sm text-gray-500">Skipped</div>
            </div>
          </div>

          {importResult.errors && importResult.errors.length > 0 && (
            <div className="border border-red-200 rounded-lg p-4">
              <h3 className="font-medium text-red-800 mb-2">Errors ({importResult.errors.length})</h3>
              <div className="max-h-40 overflow-y-auto text-sm text-red-700">
                <ul className="list-disc list-inside">
                  {importResult.errors.slice(0, 10).map((err, i) => (
                    <li key={i}>{err}</li>
                  ))}
                  {importResult.errors.length > 10 && (
                    <li>...and {importResult.errors.length - 10} more errors</li>
                  )}
                </ul>
              </div>
            </div>
          )}

          <div className="flex justify-center gap-4">
            <button
              onClick={handleReset}
              className="px-6 py-2 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition"
            >
              Import More Data
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
