/**
 * Purchase Orders Type Definitions
 */

// ============ CORE PURCHASE ORDER TYPES ============
export interface PurchaseOrder {
  id?: number;
  order_number: string;
  supplier_id: number;
  supplier_name?: string;
  supplier_code?: string;
  order_date: string;
  delivery_date: string;
  status: PurchaseOrderStatus;
  order_type: 'COST' | 'RETAIL';
  extract_stock_items: boolean;
  layout_option: OrderLayoutOption;
  total_amount: number;
  total_vat: number;
  total_landed_cost: number;
  reference?: string;
  notes?: string;
  created_by?: number;
  created_at?: string;
  updated_at?: string;
  line_items?: PurchaseOrderLineItem[];
  expenses?: POExpense[];
}

export type PurchaseOrderStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'ISSUED'
  | 'PARTIALLY_RECEIVED'
  | 'RECEIVED'
  | 'CLOSED'
  | 'CANCELLED';

export type OrderLayoutOption =
  | 'MONTH_TO_DATE_SALES'
  | 'REORDER_QUANTITY'
  | 'QUANTITY_TO_ORDER';

// ============ LINE ITEMS ============
export interface PurchaseOrderLineItem {
  id?: number;
  po_id?: number;
  line_number?: number;
  stock_code: string;
  stock_description?: string;
  quantity: number;
  quantity_on_hand?: number;
  quantity_sold?: number;
  last_cost: number;
  current_cost: number;
  tax_code: string;
  tax_rate: number;
  landed_cost: number;
  total_cost: number;
  total_vat: number;
  is_ordered: boolean;
  comments?: string;
}

// ============ EXPENSES (Landed Costs) ============
export interface POExpense {
  id?: number;
  po_id?: number;
  expense_category: string;
  description: string;
  amount: number;
  is_vat_inclusive: boolean;
  vat_amount: number;
}

// ============ GOODS RECEIVED NOTES ============
export interface GoodsReceivedNote {
  id?: number;
  po_id: number;
  order_number?: string;
  receipt_date: string;
  invoice_date: string;
  invoice_number: string;
  additional_reference?: string;
  status: 'DRAFT' | 'POSTED' | 'CANCELLED';
  total_amount: number;
  total_vat: number;
  created_by?: number;
  created_at?: string;
  line_items?: GRNAccountingLineItem[];
}

export interface GRNAccountingLineItem {
  id?: number;
  grn_id?: number;
  stock_code: string;
  stock_description?: string;
  quantity_ordered: number;
  quantity_received: number;
  quantity_outstanding: number;
  unit_cost: number;
  total_cost: number;
  variance?: number;
  is_corrected: boolean;
}

// ============ ENQUIRY TYPES ============
export interface OutstandingByDeliveryFilter {
  date_from: string;
  date_to: string;
}

export interface OutstandingByStockFilter {
  stock_code?: string;
  include_received?: boolean;
}

export interface OutstandingOrder {
  order_number: string;
  order_date: string;
  supplier_name: string;
  delivery_date: string;
  exclusive_value_due: number;
  status: PurchaseOrderStatus;
}

// ============ REPORT TYPES ============
export interface POReportFilters {
  date_from?: string;
  date_to?: string;
  supplier_id?: number;
  stock_code?: string;
  include_costs?: boolean;
  status?: PurchaseOrderStatus;
}

export type ReportType =
  | 'OUTSTANDING_DELIVERY_DATE'
  | 'OUTSTANDING_STOCK_ITEMS'
  | 'OUTSTANDING_SUPPLIER'
  | 'REPRINT_ORDER'
  | 'BACK_ORDERS'
  | 'PRE_ORDERS'
  | 'DELIVERED_ORDERS';

// ============ BACK ORDERS ============
export interface BackOrder {
  id?: number;
  po_id: number;
  original_order_number: string;
  stock_code: string;
  supplier_id: number;
  supplier_name?: string;
  quantity_ordered: number;
  quantity_received: number;
  quantity_outstanding: number;
  status: 'PENDING' | 'PARTIAL' | 'COMPLETE';
  expected_date?: string;
  created_at?: string;
}

// ============ PAGINATION ============
export interface PaginatedPOResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

export interface POSummary {
  total_orders: number;
  pending_orders: number;
  received_orders: number;
  total_value_pending: number;
  total_value_received: number;
  overdue_orders: number;
}

// ============ FORM FILTERS ============
export interface PurchaseOrderFilters {
  status?: PurchaseOrderStatus;
  supplier_id?: number;
  date_from?: string;
  date_to?: string;
  search?: string;
  page?: number;
  page_size?: number;
}
