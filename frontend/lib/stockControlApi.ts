/**
 * Stock Control API Client
 * Complete API integration for all stock control endpoints
 *
 * Base URL: /api/v1/stock-control/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';
import type {
  StockItem,
  StockItemFilters,
  PaginatedStockItems,
  SpecialDeal,
  SpecialDealCreateData,
  PaginatedSpecialDeals,
  FuturePricing,
  PaginatedFuturePricing,
  ShrinkWrap,
  PaginatedShrinkWraps,
  PackBundle,
  PackBundleIngredient,
  PaginatedPackBundles,
  StockTransaction,
  StockTransactionFilters,
  PaginatedStockTransactions,
  StockMovementLedger,
  PaginatedMovementLedger,
  StockTake,
  StockTakeItem,
  StockTakeFilters,
  PaginatedStockTakes,
  ContractPricing,
  PaginatedContractPricing,
  OneTouchLookupKey,
  PaginatedLookupKeys,
  StockMonthlyStatistic,
  PaginatedMonthlyStats,
  Branch,
  PaginatedBranches,
  BranchStock,
  PaginatedBranchStock,
  GroupOrder,
  GroupOrderItem,
  PaginatedGroupOrders,
  BranchTransfer,
  BranchTransferItem,
  PaginatedBranchTransfers,
  BranchTransferInvoice,
  PaginatedBranchTransferInvoices,
  StockItemPricing,
  StockAdjustment,
  LowStockItem,
} from './types/stockControl';

// ============================================================================
// Stock Items
// ============================================================================

export const stockControlApi = {
  // ============ STOCK ITEMS ============
  stockItems: {
    /**
     * List all stock items with filters
     */
    list: async (filters?: StockItemFilters) => {
      const response = await api.get<PaginatedStockItems>(
        ENDPOINTS.STOCK_CONTROL.STOCK_ITEMS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Thin typeahead lookup for stock item pickers — hits
     * StockItemViewSet.lookup (LookupActionMixin), returns
     * {results, count, has_more} of StockItemListSerializer rows.
     */
    lookup: async (
      query: string,
      limit = 20,
      offset = 0
    ): Promise<{ results: StockItem[]; count: number; hasMore: boolean }> => {
      const response = await api.get<{ results: StockItem[]; count: number; has_more: boolean }>(
        `${ENDPOINTS.STOCK_CONTROL.STOCK_ITEMS}lookup/`,
        { params: { search: query, limit, offset } }
      );
      return {
        results: response.data.results,
        count: response.data.count,
        hasMore: response.data.has_more,
      };
    },

    /**
     * Get single stock item by code
     */
    get: async (stockCode: string) => {
      const response = await api.get<StockItem>(
        ENDPOINTS.STOCK_CONTROL.STOCK_ITEM_DETAIL(stockCode)
      );
      return response.data;
    },

    /**
     * Create new stock item
     */
    create: async (data: Partial<StockItem>) => {
      const response = await api.post<StockItem>(
        ENDPOINTS.STOCK_CONTROL.STOCK_ITEMS,
        data
      );
      return response.data;
    },

    /**
     * Update stock item
     */
    update: async (stockCode: string, data: Partial<StockItem>) => {
      const response = await api.patch<StockItem>(
        ENDPOINTS.STOCK_CONTROL.STOCK_ITEM_DETAIL(stockCode),
        data
      );
      return response.data;
    },

    /**
     * Delete stock item
     */
    delete: async (stockCode: string) => {
      await api.delete(ENDPOINTS.STOCK_CONTROL.STOCK_ITEM_DETAIL(stockCode));
    },

    /**
     * Get pricing information for stock item
     */
    getPricing: async (stockCode: string) => {
      const response = await api.get<StockItemPricing>(
        ENDPOINTS.STOCK_CONTROL.STOCK_ITEM_PRICING(stockCode)
      );
      return response.data;
    },

    /**
     * Get transaction history for stock item
     */
    getTransactions: async (stockCode: string, filters?: StockTransactionFilters) => {
      const response = await api.get<PaginatedStockTransactions>(
        ENDPOINTS.STOCK_CONTROL.STOCK_ITEM_TRANSACTIONS(stockCode),
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get monthly statistics for stock item
     */
    getMonthlyStats: async (stockCode: string) => {
      const response = await api.get<PaginatedMonthlyStats>(
        ENDPOINTS.STOCK_CONTROL.STOCK_ITEM_MONTHLY_STATS(stockCode)
      );
      return response.data;
    },

    /**
     * Adjust stock quantity manually
     */
    adjustStock: async (stockCode: string, data: StockAdjustment) => {
      const response = await api.post(
        ENDPOINTS.STOCK_CONTROL.STOCK_ITEM_ADJUST_STOCK(stockCode),
        data
      );
      return response.data;
    },

    /**
     * Get low stock items
     */
    getLowStock: async () => {
      const response = await api.get<StockItem[]>(
        ENDPOINTS.STOCK_CONTROL.STOCK_ITEMS_LOW_STOCK
      );
      return response.data;
    },

    /**
     * Get items needing reorder
     */
    getNeedsReorder: async () => {
      const response = await api.get<LowStockItem[]>(
        ENDPOINTS.STOCK_CONTROL.STOCK_ITEMS_NEEDS_REORDER
      );
      return response.data;
    },
  },

  // ============ SPECIAL DEALS ============
  specialDeals: {
    /**
     * List all special deals
     */
    list: async (filters?: { stock_item?: string; is_active?: boolean }) => {
      const response = await api.get<PaginatedSpecialDeals>(
        ENDPOINTS.STOCK_CONTROL.SPECIAL_DEALS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single special deal
     */
    get: async (id: number) => {
      const response = await api.get<SpecialDeal>(
        `${ENDPOINTS.STOCK_CONTROL.SPECIAL_DEALS}${id}/`
      );
      return response.data;
    },

    /**
     * Create special deal
     */
    create: async (data: SpecialDealCreateData) => {
      const response = await api.post<SpecialDeal>(
        ENDPOINTS.STOCK_CONTROL.SPECIAL_DEALS,
        data
      );
      return response.data;
    },

    /**
     * Update special deal
     */
    update: async (id: number, data: Partial<SpecialDealCreateData>) => {
      const response = await api.patch<SpecialDeal>(
        `${ENDPOINTS.STOCK_CONTROL.SPECIAL_DEALS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete special deal
     */
    delete: async (id: number) => {
      await api.delete(`${ENDPOINTS.STOCK_CONTROL.SPECIAL_DEALS}${id}/`);
    },

    /**
     * Get active deals for today
     */
    getActiveToday: async () => {
      const response = await api.get<SpecialDeal[]>(
        ENDPOINTS.STOCK_CONTROL.SPECIAL_DEALS_ACTIVE_TODAY
      );
      return response.data;
    },
  },

  // ============ FUTURE PRICING ============
  futurePricing: {
    /**
     * List future pricing entries
     */
    list: async (filters?: { stock_item?: string; is_applied?: boolean }) => {
      const response = await api.get<PaginatedFuturePricing>(
        ENDPOINTS.STOCK_CONTROL.FUTURE_PRICING,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single future pricing
     */
    get: async (id: number) => {
      const response = await api.get<FuturePricing>(
        `${ENDPOINTS.STOCK_CONTROL.FUTURE_PRICING}${id}/`
      );
      return response.data;
    },

    /**
     * Create future pricing
     */
    create: async (data: Partial<FuturePricing>) => {
      const response = await api.post<FuturePricing>(
        ENDPOINTS.STOCK_CONTROL.FUTURE_PRICING,
        data
      );
      return response.data;
    },

    /**
     * Update future pricing
     */
    update: async (id: number, data: Partial<FuturePricing>) => {
      const response = await api.patch<FuturePricing>(
        `${ENDPOINTS.STOCK_CONTROL.FUTURE_PRICING}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete future pricing
     */
    delete: async (id: number) => {
      await api.delete(`${ENDPOINTS.STOCK_CONTROL.FUTURE_PRICING}${id}/`);
    },

    /**
     * Apply future pricing to stock item
     */
    apply: async (id: number) => {
      const response = await api.post(
        ENDPOINTS.STOCK_CONTROL.FUTURE_PRICING_APPLY(id)
      );
      return response.data;
    },
  },

  // ============ SHRINK WRAPS ============
  shrinkWraps: {
    /**
     * List shrink wraps
     */
    list: async () => {
      const response = await api.get<PaginatedShrinkWraps>(
        ENDPOINTS.STOCK_CONTROL.SHRINK_WRAPS
      );
      return response.data;
    },

    /**
     * Get single shrink wrap
     */
    get: async (id: number) => {
      const response = await api.get<ShrinkWrap>(
        `${ENDPOINTS.STOCK_CONTROL.SHRINK_WRAPS}${id}/`
      );
      return response.data;
    },

    /**
     * Create shrink wrap
     */
    create: async (data: Partial<ShrinkWrap>) => {
      const response = await api.post<ShrinkWrap>(
        ENDPOINTS.STOCK_CONTROL.SHRINK_WRAPS,
        data
      );
      return response.data;
    },

    /**
     * Update shrink wrap
     */
    update: async (id: number, data: Partial<ShrinkWrap>) => {
      const response = await api.patch<ShrinkWrap>(
        `${ENDPOINTS.STOCK_CONTROL.SHRINK_WRAPS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete shrink wrap
     */
    delete: async (id: number) => {
      await api.delete(`${ENDPOINTS.STOCK_CONTROL.SHRINK_WRAPS}${id}/`);
    },
  },

  // ============ PACK BUNDLES ============
  packBundles: {
    /**
     * List pack bundles
     */
    list: async () => {
      const response = await api.get<PaginatedPackBundles>(
        ENDPOINTS.STOCK_CONTROL.PACK_BUNDLES
      );
      return response.data;
    },

    /**
     * Get single pack bundle
     */
    get: async (stockCode: string) => {
      const response = await api.get<PackBundle>(
        `${ENDPOINTS.STOCK_CONTROL.PACK_BUNDLES}${stockCode}/`
      );
      return response.data;
    },

    /**
     * Create pack bundle
     */
    create: async (data: { stock_item: string; ingredients: Partial<PackBundleIngredient>[] }) => {
      const response = await api.post<PackBundle>(
        ENDPOINTS.STOCK_CONTROL.PACK_BUNDLES,
        data
      );
      return response.data;
    },

    /**
     * Update pack bundle
     */
    update: async (stockCode: string, data: Partial<PackBundle>) => {
      const response = await api.patch<PackBundle>(
        `${ENDPOINTS.STOCK_CONTROL.PACK_BUNDLES}${stockCode}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete pack bundle
     */
    delete: async (stockCode: string) => {
      await api.delete(`${ENDPOINTS.STOCK_CONTROL.PACK_BUNDLES}${stockCode}/`);
    },

    /**
     * Recalculate pack bundle cost
     */
    recalculateCost: async (stockCode: string) => {
      const response = await api.post(
        ENDPOINTS.STOCK_CONTROL.PACK_BUNDLE_RECALC_COST(stockCode)
      );
      return response.data;
    },
  },

  // ============ STOCK TRANSACTIONS ============
  transactions: {
    /**
     * List stock transactions
     */
    list: async (filters?: StockTransactionFilters) => {
      const response = await api.get<PaginatedStockTransactions>(
        ENDPOINTS.STOCK_CONTROL.TRANSACTIONS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single transaction
     */
    get: async (id: number) => {
      const response = await api.get<StockTransaction>(
        `${ENDPOINTS.STOCK_CONTROL.TRANSACTIONS}${id}/`
      );
      return response.data;
    },

    /**
     * Create transaction
     */
    create: async (data: Partial<StockTransaction>) => {
      const response = await api.post<StockTransaction>(
        ENDPOINTS.STOCK_CONTROL.TRANSACTIONS,
        data
      );
      return response.data;
    },

    /**
     * Update transaction
     */
    update: async (id: number, data: Partial<StockTransaction>) => {
      const response = await api.patch<StockTransaction>(
        `${ENDPOINTS.STOCK_CONTROL.TRANSACTIONS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete transaction
     */
    delete: async (id: number) => {
      await api.delete(`${ENDPOINTS.STOCK_CONTROL.TRANSACTIONS}${id}/`);
    },
  },

  // ============ STOCK MOVEMENT LEDGER ============
  movementLedger: {
    /**
     * List movement ledger entries
     */
    list: async (filters?: { stock_item?: string; movement_type?: string; movement_date?: string }) => {
      const response = await api.get<PaginatedMovementLedger>(
        ENDPOINTS.STOCK_CONTROL.MOVEMENT_LEDGER,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single ledger entry
     */
    get: async (id: number) => {
      const response = await api.get<StockMovementLedger>(
        `${ENDPOINTS.STOCK_CONTROL.MOVEMENT_LEDGER}${id}/`
      );
      return response.data;
    },
  },

  // ============ STOCK TAKES ============
  stockTakes: {
    /**
     * List stock takes
     */
    list: async (filters?: StockTakeFilters) => {
      const response = await api.get<PaginatedStockTakes>(
        ENDPOINTS.STOCK_CONTROL.STOCK_TAKES,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single stock take
     */
    get: async (id: number) => {
      const response = await api.get<StockTake>(
        `${ENDPOINTS.STOCK_CONTROL.STOCK_TAKES}${id}/`
      );
      return response.data;
    },

    /**
     * Create stock take
     */
    create: async (data: Partial<StockTake>) => {
      const response = await api.post<StockTake>(
        ENDPOINTS.STOCK_CONTROL.STOCK_TAKES,
        data
      );
      return response.data;
    },

    /**
     * Update stock take
     */
    update: async (id: number, data: Partial<StockTake>) => {
      const response = await api.patch<StockTake>(
        `${ENDPOINTS.STOCK_CONTROL.STOCK_TAKES}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete stock take
     */
    delete: async (id: number) => {
      await api.delete(`${ENDPOINTS.STOCK_CONTROL.STOCK_TAKES}${id}/`);
    },

    /**
     * Complete stock take
     */
    complete: async (id: number) => {
      const response = await api.post(
        ENDPOINTS.STOCK_CONTROL.STOCK_TAKE_COMPLETE(id)
      );
      return response.data;
    },

    /**
     * Update stock from stock take. mode 'overwrite' (default) treats
     * quantity_counted as the new QOH; 'additive' treats it as a delta
     * added to current QOH.
     */
    updateStock: async (id: number, mode?: 'overwrite' | 'additive') => {
      const response = await api.post(
        ENDPOINTS.STOCK_CONTROL.STOCK_TAKE_UPDATE_STOCK(id),
        mode ? { mode } : undefined
      );
      return response.data;
    },

    /**
     * Get variance report
     */
    getVarianceReport: async (id: number) => {
      const response = await api.get<StockTakeItem[]>(
        ENDPOINTS.STOCK_CONTROL.STOCK_TAKE_VARIANCE_REPORT(id)
      );
      return response.data;
    },
  },

  // ============ STOCK TAKE ITEMS ============
  stockTakeItems: {
    /**
     * List stock take items, e.g. filter by { stock_take, stock_item } to
     * find an existing row before deciding whether to create() or
     * recordCount() against it.
     */
    list: async (filters?: { stock_take?: number; stock_item?: string; is_counted?: boolean }) => {
      const response = await api.get<{ results: StockTakeItem[] } | StockTakeItem[]>(
        ENDPOINTS.STOCK_CONTROL.STOCK_TAKE_ITEMS,
        { params: filters }
      );
      const data = response.data as any;
      return (data.results ?? data) as StockTakeItem[];
    },

    /**
     * Add an item to a stock take, capturing the system quantity at the
     * time it's added. Count it afterwards via recordCount().
     */
    create: async (data: { stock_take: number; stock_item: string; quantity_on_hand: number; cost_price_at_count?: number }) => {
      const response = await api.post<StockTakeItem>(
        ENDPOINTS.STOCK_CONTROL.STOCK_TAKE_ITEMS,
        data
      );
      return response.data;
    },

    /**
     * Get single stock take item
     */
    get: async (id: number) => {
      const response = await api.get<StockTakeItem>(
        `${ENDPOINTS.STOCK_CONTROL.STOCK_TAKE_ITEMS}${id}/`
      );
      return response.data;
    },

    /**
     * Update stock take item
     */
    update: async (id: number, data: Partial<StockTakeItem>) => {
      const response = await api.patch<StockTakeItem>(
        `${ENDPOINTS.STOCK_CONTROL.STOCK_TAKE_ITEMS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Record counted quantity
     */
    recordCount: async (id: number, quantityCounted: number) => {
      const response = await api.post(
        ENDPOINTS.STOCK_CONTROL.STOCK_TAKE_ITEM_COUNT(id),
        { quantity_counted: quantityCounted }
      );
      return response.data;
    },
  },

  // ============ CONTRACT PRICING ============
  contractPricing: {
    /**
     * List contract pricing entries
     */
    list: async (filters?: { debtor?: number; stock_item?: string; is_active?: boolean }) => {
      const response = await api.get<PaginatedContractPricing>(
        ENDPOINTS.STOCK_CONTROL.CONTRACT_PRICING,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single contract pricing
     */
    get: async (id: number) => {
      const response = await api.get<ContractPricing>(
        `${ENDPOINTS.STOCK_CONTROL.CONTRACT_PRICING}${id}/`
      );
      return response.data;
    },

    /**
     * Create contract pricing
     */
    create: async (data: Partial<ContractPricing>) => {
      const response = await api.post<ContractPricing>(
        ENDPOINTS.STOCK_CONTROL.CONTRACT_PRICING,
        data
      );
      return response.data;
    },

    /**
     * Update contract pricing
     */
    update: async (id: number, data: Partial<ContractPricing>) => {
      const response = await api.patch<ContractPricing>(
        `${ENDPOINTS.STOCK_CONTROL.CONTRACT_PRICING}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete contract pricing
     */
    delete: async (id: number) => {
      await api.delete(`${ENDPOINTS.STOCK_CONTROL.CONTRACT_PRICING}${id}/`);
    },
  },

  // ============ LOOKUP KEYS ============
  lookupKeys: {
    /**
     * List lookup keys
     */
    list: async (filters?: { stock_item?: string; is_active?: boolean }) => {
      const response = await api.get<PaginatedLookupKeys>(
        ENDPOINTS.STOCK_CONTROL.LOOKUP_KEYS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single lookup key
     */
    get: async (id: number) => {
      const response = await api.get<OneTouchLookupKey>(
        `${ENDPOINTS.STOCK_CONTROL.LOOKUP_KEYS}${id}/`
      );
      return response.data;
    },

    /**
     * Create lookup key
     */
    create: async (data: Partial<OneTouchLookupKey>) => {
      const response = await api.post<OneTouchLookupKey>(
        ENDPOINTS.STOCK_CONTROL.LOOKUP_KEYS,
        data
      );
      return response.data;
    },

    /**
     * Update lookup key
     */
    update: async (id: number, data: Partial<OneTouchLookupKey>) => {
      const response = await api.patch<OneTouchLookupKey>(
        `${ENDPOINTS.STOCK_CONTROL.LOOKUP_KEYS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete lookup key
     */
    delete: async (id: number) => {
      await api.delete(`${ENDPOINTS.STOCK_CONTROL.LOOKUP_KEYS}${id}/`);
    },
  },

  // ============ MONTHLY STATISTICS ============
  monthlyStats: {
    /**
     * List monthly statistics
     */
    list: async (filters?: { stock_item?: string; year?: number }) => {
      const response = await api.get<PaginatedMonthlyStats>(
        ENDPOINTS.STOCK_CONTROL.MONTHLY_STATS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single monthly statistic
     */
    get: async (id: number) => {
      const response = await api.get<StockMonthlyStatistic>(
        `${ENDPOINTS.STOCK_CONTROL.MONTHLY_STATS}${id}/`
      );
      return response.data;
    },
  },

  // ============ BRANCHES ============
  branches: {
    /**
     * List branches
     */
    list: async (filters?: { branch_type?: string; is_active?: boolean }) => {
      const response = await api.get<PaginatedBranches>(
        ENDPOINTS.STOCK_CONTROL.BRANCHES,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single branch
     */
    get: async (branchCode: string) => {
      const response = await api.get<Branch>(
        ENDPOINTS.STOCK_CONTROL.BRANCH_DETAIL(branchCode)
      );
      return response.data;
    },

    /**
     * Create branch
     */
    create: async (data: Partial<Branch>) => {
      const response = await api.post<Branch>(
        ENDPOINTS.STOCK_CONTROL.BRANCHES,
        data
      );
      return response.data;
    },

    /**
     * Update branch
     */
    update: async (branchCode: string, data: Partial<Branch>) => {
      const response = await api.patch<Branch>(
        ENDPOINTS.STOCK_CONTROL.BRANCH_DETAIL(branchCode),
        data
      );
      return response.data;
    },

    /**
     * Delete branch
     */
    delete: async (branchCode: string) => {
      await api.delete(ENDPOINTS.STOCK_CONTROL.BRANCH_DETAIL(branchCode));
    },

    /**
     * Get stock levels at branch
     */
    getStockLevels: async (branchCode: string, search?: string) => {
      const response = await api.get<BranchStock[]>(
        ENDPOINTS.STOCK_CONTROL.BRANCH_STOCK_LEVELS(branchCode),
        { params: { search } }
      );
      return response.data;
    },
  },

  // ============ BRANCH STOCK ============
  branchStock: {
    /**
     * List branch stock entries
     */
    list: async (filters?: { branch?: string; stock_item?: string }) => {
      const response = await api.get<PaginatedBranchStock>(
        ENDPOINTS.STOCK_CONTROL.BRANCH_STOCK,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single branch stock
     */
    get: async (id: number) => {
      const response = await api.get<BranchStock>(
        `${ENDPOINTS.STOCK_CONTROL.BRANCH_STOCK}${id}/`
      );
      return response.data;
    },

    /**
     * Get low stock at branch
     */
    getLowStock: async (branchCode?: string) => {
      const response = await api.get<BranchStock[]>(
        ENDPOINTS.STOCK_CONTROL.BRANCH_STOCK_LOW,
        { params: branchCode ? { branch: branchCode } : undefined }
      );
      return response.data;
    },
  },

  // ============ GROUP ORDERS ============
  groupOrders: {
    /**
     * List group orders
     */
    list: async (filters?: { status?: string; branch?: number }) => {
      const response = await api.get<PaginatedGroupOrders>(
        ENDPOINTS.STOCK_CONTROL.GROUP_ORDERS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single group order
     */
    get: async (id: number) => {
      const response = await api.get<GroupOrder>(
        `${ENDPOINTS.STOCK_CONTROL.GROUP_ORDERS}${id}/`
      );
      return response.data;
    },

    /**
     * Create group order
     */
    create: async (data: Partial<GroupOrder>) => {
      const response = await api.post<GroupOrder>(
        ENDPOINTS.STOCK_CONTROL.GROUP_ORDERS,
        data
      );
      return response.data;
    },

    /**
     * Update group order
     */
    update: async (id: number, data: Partial<GroupOrder>) => {
      const response = await api.patch<GroupOrder>(
        `${ENDPOINTS.STOCK_CONTROL.GROUP_ORDERS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete group order
     */
    delete: async (id: number) => {
      await api.delete(`${ENDPOINTS.STOCK_CONTROL.GROUP_ORDERS}${id}/`);
    },

    /**
     * Recalculate group order total
     */
    recalculateTotal: async (id: number) => {
      const response = await api.post(
        ENDPOINTS.STOCK_CONTROL.GROUP_ORDER_RECALC_TOTAL(id)
      );
      return response.data;
    },
  },

  // ============ BRANCH TRANSFERS ============
  branchTransfers: {
    /**
     * List branch transfers
     */
    list: async (filters?: { status?: string; from_branch?: string; to_branch?: string }) => {
      const response = await api.get<PaginatedBranchTransfers>(
        ENDPOINTS.STOCK_CONTROL.BRANCH_TRANSFERS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single branch transfer
     */
    get: async (id: number) => {
      const response = await api.get<BranchTransfer>(
        `${ENDPOINTS.STOCK_CONTROL.BRANCH_TRANSFERS}${id}/`
      );
      return response.data;
    },

    /**
     * Create branch transfer
     */
    create: async (data: Partial<BranchTransfer>) => {
      const response = await api.post<BranchTransfer>(
        ENDPOINTS.STOCK_CONTROL.BRANCH_TRANSFERS,
        data
      );
      return response.data;
    },

    /**
     * Update branch transfer
     */
    update: async (id: number, data: Partial<BranchTransfer>) => {
      const response = await api.patch<BranchTransfer>(
        `${ENDPOINTS.STOCK_CONTROL.BRANCH_TRANSFERS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete branch transfer
     */
    delete: async (id: number) => {
      await api.delete(`${ENDPOINTS.STOCK_CONTROL.BRANCH_TRANSFERS}${id}/`);
    },

    /**
     * Approve transfer
     */
    approve: async (id: number) => {
      const response = await api.post(
        ENDPOINTS.STOCK_CONTROL.TRANSFER_APPROVE(id)
      );
      return response.data;
    },

    /**
     * Dispatch transfer
     */
    dispatch: async (id: number) => {
      const response = await api.post(
        ENDPOINTS.STOCK_CONTROL.TRANSFER_DISPATCH(id)
      );
      return response.data;
    },

    /**
     * Receive transfer
     */
    receive: async (id: number, items: { stock_item: string; quantity_received: number }[]) => {
      const response = await api.post(
        ENDPOINTS.STOCK_CONTROL.TRANSFER_RECEIVE(id),
        { items }
      );
      return response.data;
    },

    /**
     * Cancel transfer
     */
    cancel: async (id: number) => {
      const response = await api.post(
        ENDPOINTS.STOCK_CONTROL.TRANSFER_CANCEL(id)
      );
      return response.data;
    },
  },

  // ============ BRANCH TRANSFER ITEMS ============
  branchTransferItems: {
    /**
     * Add a line item to a branch transfer
     */
    create: async (data: { transfer: number; stock_item: string; quantity_requested: number }) => {
      const response = await api.post(
        ENDPOINTS.STOCK_CONTROL.BRANCH_TRANSFER_ITEMS,
        data
      );
      return response.data;
    },
  },

  // ============ BRANCH TRANSFER INVOICES ============
  branchTransferInvoices: {
    /**
     * List branch transfer invoices
     */
    list: async (filters?: { status?: string; branch_transfer?: number }) => {
      const response = await api.get<PaginatedBranchTransferInvoices>(
        ENDPOINTS.STOCK_CONTROL.BRANCH_TRANSFER_INVOICES,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single invoice
     */
    get: async (id: number) => {
      const response = await api.get<BranchTransferInvoice>(
        `${ENDPOINTS.STOCK_CONTROL.BRANCH_TRANSFER_INVOICES}${id}/`
      );
      return response.data;
    },

    /**
     * Create invoice
     */
    create: async (data: Partial<BranchTransferInvoice>) => {
      const response = await api.post<BranchTransferInvoice>(
        ENDPOINTS.STOCK_CONTROL.BRANCH_TRANSFER_INVOICES,
        data
      );
      return response.data;
    },

    /**
     * Issue invoice
     */
    issue: async (id: number) => {
      const response = await api.post(
        ENDPOINTS.STOCK_CONTROL.INVOICE_ISSUE(id)
      );
      return response.data;
    },

    /**
     * Mark invoice as paid
     */
    markPaid: async (id: number) => {
      const response = await api.post(
        ENDPOINTS.STOCK_CONTROL.INVOICE_MARK_PAID(id)
      );
      return response.data;
    },
  },
};

// ============================================================================
// Stock Transactions
// ============================================================================

/**
 * Get all stock transactions
 */
export const getTransactions = async (filters?: StockTransactionFilters) => {
  const response = await api.get<PaginatedStockTransactions>(
    ENDPOINTS.STOCK_CONTROL.TRANSACTIONS,
    { params: filters }
  );
  return response.data;
};

/**
 * Record a stock transaction
 */
export const recordTransaction = async (data: {
  stock_code: string;
  quantity: number;
  transaction_type: 'IN' | 'OUT' | 'ADJUST' | string;
  reference?: string;
  notes?: string;
}) => {
  const response = await api.post(
    ENDPOINTS.STOCK_CONTROL.TRANSACTIONS,
    data
  );
  return response.data;
};

/**
 * Get stock summary
 */
export const getStockSummary = async () => {
  const response = await api.get(
    ENDPOINTS.STOCK_CONTROL.STOCK_ITEMS
  );
  return response.data;
};

// ============================================================================
// Convenience Exports (standalone functions)
// ============================================================================

/**
 * Get single stock item by code
 */
export const getStockItem = async (stockCode: string) => {
  return stockControlApi.stockItems.get(stockCode);
};

/**
 * Get all stock items with optional filters
 */
export const getStockItems = async (filters?: StockItemFilters) => {
  return stockControlApi.stockItems.list(filters);
};

/**
 * Create new stock item
 */
export const createStockItem = async (data: Partial<StockItem>) => {
  return stockControlApi.stockItems.create(data);
};

/**
 * Update stock item
 */
export const updateStockItem = async (stockCode: string, data: Partial<StockItem>) => {
  return stockControlApi.stockItems.update(stockCode, data);
};

/**
 * Delete stock item
 */
export const deleteStockItem = async (stockCode: string) => {
  return stockControlApi.stockItems.delete(stockCode);
};

/**
 * Get pricing information for stock item
 */
export const getStockItemPricing = async (stockCode: string) => {
  return stockControlApi.stockItems.getPricing(stockCode);
};

/**
 * Get transaction history for stock item
 */
export const getStockItemTransactions = async (stockCode: string, filters?: StockTransactionFilters) => {
  return stockControlApi.stockItems.getTransactions(stockCode, filters);
};

/**
 * Adjust stock quantity manually
 */
export const adjustStockItem = async (stockCode: string, data: StockAdjustment) => {
  return stockControlApi.stockItems.adjustStock(stockCode, data);
};

export default stockControlApi;
