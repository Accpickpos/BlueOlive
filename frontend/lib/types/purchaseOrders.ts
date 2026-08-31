/**
 * Purchase Orders Type Definitions
 *
 * Mirrors backend/core/apps/purchase_orders/serializers.py — PurchaseOrder's
 * primary key is order_number (an AutoField), status is the real 4-state
 * O/P/F/C model (not a fictional multi-stage workflow), and money fields use
 * the real total_/outstanding_ value naming.
 */

// ============ CORE PURCHASE ORDER TYPES ============
export type PurchaseOrderStatus = 'O' | 'P' | 'F' | 'C';

export const PURCHASE_ORDER_STATUS_LABELS: Record<PurchaseOrderStatus, string> = {
  O: 'Outstanding',
  P: 'Partially Received',
  F: 'Fully Received',
  C: 'Cancelled',
};

export type PricingMethod = 'COST' | 'RETAIL';

export interface PurchaseOrder {
  order_number: number;
  supplier: number;
  supplier_name?: string;
  supplier_account?: string;
  order_date: string;
  order_time?: string | null;
  delivery_date: string;
  status: PurchaseOrderStatus;
  status_display?: string;
  pricing_method: PricingMethod;
  pricing_method_display?: string;

  quantity_ordered: number;
  total_quantity_received: number;
  total_quantity_outstanding: number;

  total_value_exclusive: number;
  total_value_vat: number;
  total_value_inclusive: number;

  outstanding_value_exclusive: number;
  outstanding_value_vat: number;
  outstanding_value_inclusive: number;

  is_back_order: boolean;
  parent_order?: number | null;

  notes?: string;
  cancellation_reason?: string;

  created_at?: string;
  updated_at?: string;
  cancelled_at?: string | null;

  is_overdue?: boolean;
  days_until_delivery?: number;
  completion_percentage?: number;

  line_items?: PurchaseOrderLineItem[];
}

// ============ LINE ITEMS ============
export interface PurchaseOrderLineItem {
  id?: number;
  purchase_order?: number;
  line_number: number;
  stock_code: string;
  stock_description?: string;
  supplier_code?: string;

  quantity: number;
  quantity_delivered?: number;
  free_quantity?: number;
  quantity_outstanding?: number;

  base_price: number;
  monetary_discount1?: number;
  monetary_discount2?: number;
  monetary_discount3?: number;
  percent_discount1?: number;
  percent_discount2?: number;
  percent_discount3?: number;

  selling_price1?: number;
  selling_price2?: number;
  selling_price3?: number;

  comments?: string;
  expense_category?: number | null;
  expense_category_name?: string;

  total_exclusive?: number;
  total_vat?: number;
  total_inclusive?: number;
  outstanding_exclusive?: number;
  outstanding_vat?: number;
  outstanding_inclusive?: number;

  quantity_on_hand?: number;
  current_cost?: number;
  quantity_on_hand_at_order?: number;
  monthly_sales_at_order?: number;

  tax_code: number;
  is_fully_received?: boolean;
}

// ============ GOODS RECEIVED (PurchaseOrderReceipt) ============
export interface PurchaseOrderReceipt {
  id?: number;
  purchase_order: number;
  supplier_name?: string;
  receipt_date: string;
  invoice_number: string;
  creditor_grn?: number | null;

  total_quantity?: number;
  total_value_exclusive?: number;
  total_value_vat?: number;
  total_value_inclusive?: number;

  has_variance?: boolean;
  variance_notes?: string;
  created_at?: string;

  line_items?: PurchaseOrderReceiptLine[];
}

export interface PurchaseOrderReceiptLine {
  id?: number;
  receipt?: number;
  purchase_order_line: number;
  stock_code?: string;
  stock_description?: string;
  ordered_cost?: number;

  quantity_received: number;
  actual_unit_cost: number;

  line_exclusive?: number;
  line_vat?: number;
  line_inclusive?: number;

  has_cost_variance?: boolean;
  cost_variance_amount?: number;
  created_at?: string;
}

// ============ ENQUIRY / REPORT TYPES ============
export interface OutstandingByDeliveryFilter {
  date_from: string;
  date_to: string;
}

export interface OutstandingByStockFilter {
  stock_code?: string;
  supplier?: number;
}

export interface StockOnOrderItem {
  stock_code: string;
  description: string;
  quantity_on_hand: number;
  quantity_on_order: number;
  reorder_quantity: number;
  orders: Array<{
    order_number: number;
    supplier: string;
    quantity: number;
    delivery_date: string;
  }>;
}

export interface PreOrderReportItem {
  stock_code: string;
  description: string;
  supplier_name: string;
  quantity_on_hand: number;
  reorder_quantity: number;
  monthly_sales_avg: number;
  suggested_order_qty: number;
  last_cost: number;
  estimated_value: number;
}

export interface DeliveryVarianceItem {
  order_number: number;
  supplier_name: string;
  stock_code: string;
  description: string;
  quantity_ordered: number;
  quantity_received: number;
  quantity_short: number;
  ordered_cost: number;
  actual_cost: number;
  cost_variance: number;
  value_variance: number;
}

// ============ BACK ORDERS ============
export interface BackOrder {
  id?: number;
  original_order: number;
  original_order_number?: number;
  back_order: number;
  back_order_number?: number;
  supplier_name?: string;
  created_date?: string;
  reason?: string;
  triggering_receipt?: number | null;
  created_at?: string;
}

// ============ TEMPLATES ============
export interface PurchaseOrderTemplate {
  id?: number;
  template_name: string;
  supplier: number;
  supplier_name?: string;
  description?: string;
  default_delivery_days?: number;
  pricing_method?: PricingMethod;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
  line_items?: PurchaseOrderTemplateLine[];
}

export interface PurchaseOrderTemplateLine {
  id?: number;
  template?: number;
  line_number: number;
  stock_item: number;
  stock_code?: string;
  stock_description?: string;
  current_cost?: number;
  default_quantity: number;
}

// ============ PAGINATION ============
export interface PaginatedPOResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

// ============ FORM FILTERS ============
export interface PurchaseOrderFilters {
  status?: PurchaseOrderStatus;
  supplier?: number;
  order_date?: string;
  delivery_date?: string;
  search?: string;
  page?: number;
  page_size?: number;
}
