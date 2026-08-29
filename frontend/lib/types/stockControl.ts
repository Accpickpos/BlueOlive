/**
 * Stock Control Types
 * TypeScript interfaces for stock control API responses
 */

// ============================================================================
// Stock Items
// ============================================================================

export interface StockItem {
  stock_code: string;
  description: string;
  department: number | string;
  department_detail?: {
    id: number;
    name: string;
    department_number?: number;
  };
  supplier?: number | string;
  supplier_detail?: {
    id: number;
    name: string;
  };
  supplier_code?: string;
  tax_code: number | string;
  tax_code_detail?: {
    id: number;
    code: string;
    rate?: number;
  };
  barcode?: string;
  bin_number?: string;
  reorder_quantity: number;
  quantity_on_hand: number;
  quantity_on_order: number;
  quantity_allocated: number;
  available_quantity?: number;
  cost_price: number;
  average_cost: number;
  selling_price_1: number;
  selling_price_2: number;
  selling_price_3: number;
  markup_1: number;
  markup_2: number;
  markup_3: number;
  maximum_discount_percent?: number;
  default_selling_quantity?: number;
  allow_negative_quantities: boolean;
  kvi_flag: boolean;
  is_active: boolean;
  last_supplier?: number;
  last_supplier_detail?: {
    id: number;
    name: string;
  };
  created_at?: string;
  updated_at?: string;
}

export interface StockItemFilters {
  search?: string;
  department?: number;
  supplier?: number;
  is_active?: boolean;
  tax_code?: number;
  kvi_flag?: boolean;
  code_from?: string;
  code_to?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface PaginatedStockItems {
  count: number;
  next?: string;
  previous?: string;
  results: StockItem[];
}

// ============================================================================
// Special Deals
// ============================================================================

export interface SpecialDeal {
  id: number;
  stock_item: string | number;
  stock_item_detail?: StockItem;
  special_cost_price?: number;
  special_selling_price_1?: number;
  special_selling_price_2?: number;
  special_selling_price_3?: number;
  special_markup_1?: number;
  special_markup_2?: number;
  special_markup_3?: number;
  start_date: string;
  end_date: string;
  is_active: boolean;
  is_valid_today?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface SpecialDealCreateData {
  stock_item: string;
  special_cost_price?: number;
  special_selling_price_1?: number;
  special_selling_price_2?: number;
  special_selling_price_3?: number;
  special_markup_1?: number;
  special_markup_2?: number;
  special_markup_3?: number;
  start_date: string;
  end_date: string;
  is_active?: boolean;
}

export interface PaginatedSpecialDeals {
  count: number;
  next?: string;
  previous?: string;
  results: SpecialDeal[];
}

// ============================================================================
// Future Pricing
// ============================================================================

export interface FuturePricing {
  id: number;
  stock_item: string;
  stock_item_detail?: StockItem;
  future_cost_price?: number;
  future_selling_price_1?: number;
  future_selling_price_2?: number;
  future_selling_price_3?: number;
  future_markup_1?: number;
  future_markup_2?: number;
  future_markup_3?: number;
  effective_date: string;
  is_applied: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PaginatedFuturePricing {
  count: number;
  next?: string;
  previous?: string;
  results: FuturePricing[];
}

// ============================================================================
// Shrink Wraps
// ============================================================================

export interface ShrinkWrap {
  id: number;
  shrink_pack_code: string;
  shrink_pack_code_detail?: StockItem;
  bulk_pack_code: string;
  bulk_pack_code_detail?: StockItem;
  invoice_bulk_value?: number;
  created_at?: string;
  updated_at?: string;
}

export interface PaginatedShrinkWraps {
  count: number;
  next?: string;
  previous?: string;
  results: ShrinkWrap[];
}

// ============================================================================
// Pack Bundles
// ============================================================================

export interface PackBundleIngredient {
  id: number;
  pack_bundle: string;
  ingredient_stock: string;
  ingredient_stock_detail?: StockItem;
  quantity_required: number;
  created_at?: string;
  updated_at?: string;
}

export interface PackBundle {
  stock_item: string;
  stock_item_detail?: StockItem;
  ingredients?: PackBundleIngredient[];
  created_at?: string;
  updated_at?: string;
}

export interface PaginatedPackBundles {
  count: number;
  next?: string;
  previous?: string;
  results: PackBundle[];
}

// ============================================================================
// Stock Transactions
// ============================================================================

export interface StockTransaction {
  id: number;
  stock_item: string;
  stock_item_detail?: StockItem;
  transaction_type: 'IN' | 'OUT' | 'ADJ' | 'SAL' | 'RET' | 'GRN' | 'TRF';
  transaction_date: string;
  quantity: number;
  quantity_before: number;
  quantity_after: number;
  unit_cost?: number;
  total_cost?: number;
  reference?: string;
  reference_number?: string;
  notes?: string;
  created_by?: string;
  created_at?: string;
}

export interface StockTransactionFilters {
  stock_item?: string;
  transaction_type?: string;
  department?: number;
  debtor?: number;
  supplier?: number;
  date_from?: string;
  date_to?: string;
  search?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface PaginatedStockTransactions {
  count: number;
  next?: string;
  previous?: string;
  results: StockTransaction[];
}

// ============================================================================
// Stock Movement Ledger (Read-only)
// ============================================================================

export interface StockMovementLedger {
  id: number;
  stock_item: string;
  stock_item_detail?: StockItem;
  movement_type: string;
  movement_date: string;
  quantity: number;
  unit_cost?: number;
  total_cost?: number;
  reference?: string;
  notes?: string;
  created_at?: string;
}

export interface PaginatedMovementLedger {
  count: number;
  next?: string;
  previous?: string;
  results: StockMovementLedger[];
}

// ============================================================================
// Stock Takes
// ============================================================================

export interface StockTakeItem {
  id: number;
  stock_take: number;
  stock_item: string;
  stock_item_detail?: StockItem;
  quantity_on_hand: number;
  quantity_counted: number;
  variance_quantity?: number;
  variance_value?: number;
  cost_price_at_count?: number;
  is_counted?: boolean;
  count_date?: string;
  created_at?: string;
  updated_at?: string;
}

export interface StockTake {
  id: number;
  stock_take_date: string;
  status: 'IN_PROGRESS' | 'COMPLETED' | 'UPDATED';
  description?: string;
  reset_negatives_to_zero?: boolean;
  set_uncounted_to_zero?: boolean;
  is_after_trading?: boolean;
  trading_start_date?: string;
  item_count?: number;
  items?: StockTakeItem[];
  completed_at?: string;
  created_by?: string;
  created_at?: string;
  updated_at?: string;
}

export interface StockTakeFilters {
  status?: string;
  stock_take_date?: string;
  page?: number;
  page_size?: number;
}

export interface PaginatedStockTakes {
  count: number;
  next?: string;
  previous?: string;
  results: StockTake[];
}

// ============================================================================
// Contract Pricing
// ============================================================================

export interface ContractPricing {
  id: number;
  debtor: number | string;
  stock_item?: string | null;
  department?: number | null;
  supplier?: number | null;
  pricing_method: 'ACTUAL' | 'COST_MARKUP';
  contract_price?: number | null;
  markup_percent?: number | null;
  discount_percent?: number;
  last_selling_price?: number;
  last_updated_date?: string | null;
  valid_from?: string | null;
  valid_until?: string | null;
  is_fixed_pricing?: boolean;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PaginatedContractPricing {
  count: number;
  next?: string;
  previous?: string;
  results: ContractPricing[];
}

// ============================================================================
// Lookup Keys (OneTouch)
// ============================================================================

export interface OneTouchLookupKey {
  id: number;
  key_character: string;
  stock_item: string;
  created_at?: string;
  updated_at?: string;
}

export interface PaginatedLookupKeys {
  count: number;
  next?: string;
  previous?: string;
  results: OneTouchLookupKey[];
}

// ============================================================================
// Monthly Statistics
// ============================================================================

export interface StockMonthlyStatistic {
  id: number;
  stock_item: string;
  stock_item_detail?: StockItem;
  year: number;
  month: number;
  quantity_sold: number;
  total_sales: number;
  total_cost: number;
  gross_profit: number;
  average_quantity_on_hand?: number;
  created_at?: string;
  updated_at?: string;
}

export interface PaginatedMonthlyStats {
  count: number;
  next?: string;
  previous?: string;
  results: StockMonthlyStatistic[];
}

// ============================================================================
// Branches
// ============================================================================

export interface Branch {
  branch_code: string;
  branch_name: string;
  branch_type: 'RETAIL' | 'WAREHOUSE' | 'HQ';
  is_active: boolean;
  is_default?: boolean;
  address?: string;
  contact_phone?: string;
  created_at?: string;
  updated_at?: string;
}

export interface BranchStock {
  id: number;
  branch: string;
  branch_detail?: Branch;
  stock_item: string;
  stock_item_detail?: StockItem;
  quantity_on_hand: number;
  quantity_on_order: number;
  quantity_allocated: number;
  reorder_quantity: number;
  available_quantity?: number;
  last_stock_count_date?: string;
  created_at?: string;
  updated_at?: string;
}

export interface PaginatedBranches {
  count: number;
  next?: string;
  previous?: string;
  results: Branch[];
}

export interface PaginatedBranchStock {
  count: number;
  next?: string;
  previous?: string;
  results: BranchStock[];
}

// ============================================================================
// Group Orders
// ============================================================================

export interface GroupOrderItem {
  id: number;
  group_order: number;
  stock_item: string;
  stock_item_detail?: StockItem;
  quantity_ordered: number;
  quantity_received?: number;
  unit_price?: number;
  total_price?: number;
}

export interface GroupOrder {
  id: number;
  group_order_number: string;
  order_date: string;
  status: 'PENDING' | 'APPROVED' | 'RECEIVED' | 'CANCELLED';
  branch?: number;
  branch_detail?: Branch;
  items?: GroupOrderItem[];
  total_amount?: number;
  notes?: string;
  created_by?: string;
  created_at?: string;
  updated_at?: string;
}

export interface PaginatedGroupOrders {
  count: number;
  next?: string;
  previous?: string;
  results: GroupOrder[];
}

// ============================================================================
// Branch Transfers (IBT)
// ============================================================================

export interface BranchTransferItem {
  id: number;
  transfer: number;
  stock_item: string;
  stock_item_detail?: StockItem;
  quantity_requested: number;
  quantity_dispatched?: number;
  quantity_received?: number;
  variance?: number;
}

export interface BranchTransfer {
  id: number;
  transfer_number: string;
  from_branch: string;
  from_branch_detail?: Branch;
  to_branch: string;
  to_branch_detail?: Branch;
  status: 'DRAFT' | 'PENDING' | 'APPROVED' | 'DISPATCHED' | 'IN_TRANSIT' | 'RECEIVED' | 'COMPLETED' | 'CANCELLED';
  transfer_type?: 'STANDARD' | 'URGENT' | 'RETURN';
  items?: BranchTransferItem[];
  requested_date?: string;
  approved_date?: string;
  dispatched_date?: string;
  received_date?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface BranchTransferInvoice {
  id: number;
  invoice_number: string;
  branch_transfer: number;
  branch_transfer_detail?: BranchTransfer;
  issue_date: string;
  status: 'DRAFT' | 'ISSUED' | 'PAID';
  total_amount?: number;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface PaginatedBranchTransfers {
  count: number;
  next?: string;
  previous?: string;
  results: BranchTransfer[];
}

export interface PaginatedBranchTransferInvoices {
  count: number;
  next?: string;
  previous?: string;
  results: BranchTransferInvoice[];
}

// ============================================================================
// Stock Pricing Response
// ============================================================================

export interface StockItemPricing {
  stock_code: string;
  cost_price: number;
  average_cost: number;
  selling_price_1: number;
  selling_price_2: number;
  selling_price_3: number;
  markup_1: number;
  markup_2: number;
  markup_3: number;
  gross_profit_pct_1?: number;
  gross_profit_pct_2?: number;
  gross_profit_pct_3?: number;
  active_special_deal?: SpecialDeal | null;
  future_prices: FuturePricing[];
}

// ============================================================================
// Stock Adjustment
// ============================================================================

export interface StockAdjustment {
  // Matches StockItemViewSet.adjust_stock's body shape: signed quantity
  // (positive = stock in, negative = stock out), not adjustment_quantity
  // (no such field on the backend).
  quantity: number;
  comments?: string;
}

// ============================================================================
// Low Stock / Reorder
// ============================================================================

export interface LowStockItem extends StockItem {
  reorder_quantity: number;
  quantity_on_hand: number;
}
