/**
 * Purchase Orders API Response Types
 */

import {
  PurchaseOrder,
  GoodsReceivedNote,
  BackOrder,
  PurchaseOrderLineItem,
  POExpense,
  GRNAccountingLineItem,
} from './purchaseOrders';

// ============ PAGINATED RESPONSES ============
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface OrderListResponse extends PaginatedResponse<PurchaseOrder> {}

// ============ ORDER RESPONSES ============
export interface OrderDetailResponse extends PurchaseOrder {
  supplier?: {
    id: number;
    account_number: string;
    name: string;
    email?: string;
    phone?: string;
    address?: string;
  };
  line_items: PurchaseOrderLineItem[];
  expenses: POExpense[];
  created_by_user?: {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
  };
}

// ============ CREATE/UPDATE RESPONSES ============
export interface CreateOrderResponse {
  success: boolean;
  order: PurchaseOrder;
  message: string;
}

export interface UpdateOrderResponse {
  success: boolean;
  order: PurchaseOrder;
  changes?: {
    field: string;
    old_value: any;
    new_value: any;
  }[];
}

export interface CancelOrderResponse {
  success: boolean;
  order_id: number;
  status: 'CANCELLED';
  cancelled_at: string;
  cancelled_by?: number;
  reason?: string;
}

export interface ApproveOrderResponse {
  success: boolean;
  order_id: number;
  status: 'APPROVED';
  approved_at: string;
  approved_by?: number;
}

// ============ GRN RESPONSES ============
export interface GRNDetailResponse extends GoodsReceivedNote {
  order?: {
    id: number;
    order_number: string;
    supplier_name: string;
    total_amount: number;
  };
  line_items: GRNAccountingLineItem[];
  variance_total?: number;
}

// ============ BACK ORDER RESPONSES ============
export interface BackOrderListResponse extends PaginatedResponse<BackOrder> {
  total_outstanding_quantity?: number;
  total_value?: number;
}

export interface ConvertBackOrderResponse {
  success: boolean;
  back_order_id: number;
  new_order_id: number;
  new_order_number: string;
}

// ============ ENQUIRY RESPONSES ============
export interface EnquiryResponse {
  orders: OutstandingOrderDetail[];
  total_value: number;
  order_count: number;
  filters_applied?: Record<string, any>;
}

export interface OutstandingOrderDetail {
  order_number: string;
  order_date: string;
  supplier_name: string;
  delivery_date: string;
  exclusive_value_due: number;
  status: string;
  line_items_count?: number;
}

// ============ REPORT RESPONSES ============
export interface ReportResponse {
  report_type: string;
  generated_at: string;
  filters?: Record<string, any>;
  data: any[];
  summary?: {
    total_orders: number;
    total_value: number;
    total_vat: number;
  };
  pagination?: {
    page: number;
    page_size: number;
    total_pages: number;
  };
}

// ============ UTILITY RESPONSES ============
export interface IndexFilesResponse {
  success: boolean;
  message: string;
  files_reindexed: number;
  reindex_time_ms: number;
}

export interface ResetQuantitiesResponse {
  success: boolean;
  message: string;
  items_reset: number;
  reset_time_ms: number;
}

export interface SystemParametersResponse {
  default_order_type: 'COST' | 'RETAIL';
  require_approval: boolean;
  auto_extract_stock: boolean;
  default_tax_code: string;
  allow_back_orders: boolean;
  grn_requires_invoice: boolean;
  print_options?: {
    show_costs: boolean;
    show_vat: boolean;
    show_landed_cost: boolean;
  };
}

// ============ ERROR RESPONSES ============
export interface APIErrorResponse {
  detail?: string;
  message?: string;
  code?: string;
  errors?: Record<string, string[]>;
}

export interface ValidationErrorResponse {
  message: string;
  errors: Record<string, string[]>;
}
