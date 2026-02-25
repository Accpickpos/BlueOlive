/**
 * API Configuration
 * Centralized configuration for all API endpoints
 * 
 * All endpoints follow the pattern: /api/v1/{module}/{resource}/
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
export const API_V1_BASE = `/api/v1`;

// ===== ENDPOINT CONFIGURATION =====
export const ENDPOINTS = {
  // ===== AUTHENTICATION =====
  AUTH: {
    CSRF: `${API_V1_BASE}/users/auth/csrf/`,
    SIGNUP: `${API_V1_BASE}/users/auth/signup/`,
    LOGIN: `${API_V1_BASE}/users/auth/login/`,
    UNIFIED_LOGIN: `${API_V1_BASE}/users/auth/unified-login/`,
    LOGOUT: `${API_V1_BASE}/users/auth/logout/`,
    TOKEN_REFRESH: `${API_V1_BASE}/users/auth/token/refresh/`,
    PROFILE: `${API_V1_BASE}/users/auth/profile/`,
  },

  // ===== USERS =====
  USERS: {
    BASE: `${API_V1_BASE}/users/users/`,
    SUPERUSERS: `${API_V1_BASE}/users/admin/superusers/`,
  },

  // ===== TENANTS/SHOPS =====
  TENANTS: {
    BASE: `${API_V1_BASE}/tenants/tenants/`,
    SHOPS: `${API_V1_BASE}/tenants/shops/`,
    CURRENT_TENANT: `${API_V1_BASE}/tenants/current_tenant/`,
    TENANT_SHOPS: `${API_V1_BASE}/tenants/tenant_shops/`,
    ALL_SHOPS: `${API_V1_BASE}/tenants/all_shops/`,
  },

  // ===== SAAS ADMIN =====
  SAAS_ADMIN: {
    IMPORT_TENANTS: `${API_V1_BASE}/saas-admin/import/tenants/`,
    IMPORT_ANALYZE: `${API_V1_BASE}/saas-admin/import/analyze/`,
    IMPORT_EXECUTE: `${API_V1_BASE}/saas-admin/import/execute/`,
  },

  // ===== DEBTORS =====
  DEBTORS: {
    ACCOUNTS: `${API_V1_BASE}/debtors/debtors/`,
    TRANSACTIONS: `${API_V1_BASE}/debtors/transactions/`,
    OPEN_ITEMS: `${API_V1_BASE}/debtors/open-items/`,
    POST_DATED_CHEQUES: `${API_V1_BASE}/debtors/post-dated-cheques/`,
    AUDIT: `${API_V1_BASE}/debtors/audit/`,
    SALES_AREAS: `${API_V1_BASE}/debtors/sales-areas/`,

    // Special Actions (using template literals for dynamic IDs)
    AGE_ANALYSIS: (dno: string) => `${API_V1_BASE}/debtors/debtors/${dno}/age_analysis/`,
    DEBTOR_TRANSACTIONS: (dno: string) => `${API_V1_BASE}/debtors/debtors/${dno}/transactions/`,
    BALANCE_DETAILS: (dno: string) => `${API_V1_BASE}/debtors/debtors/${dno}/balance_details/`,
    BLOCK_ACCOUNT: (dno: string) => `${API_V1_BASE}/debtors/debtors/${dno}/block/`,
    UNBLOCK_ACCOUNT: (dno: string) => `${API_V1_BASE}/debtors/debtors/${dno}/unblock/`,
    SUMMARY: `${API_V1_BASE}/debtors/debtors/summary/`,
  },

  // ===== CREDITORS =====
  CREDITORS: {
    BASE: `${API_V1_BASE}/creditors/`,
    ACCOUNTS: `${API_V1_BASE}/creditors/creditors/`,
    TRANSACTIONS: `${API_V1_BASE}/creditors/transactions/`,
    CREDIT_TERMS: `${API_V1_BASE}/creditors/credit-terms/`,
    GRNS: `${API_V1_BASE}/creditors/grns/`,
    INVOICES: `${API_V1_BASE}/creditors/invoices/`,
    PAYMENTS: `${API_V1_BASE}/creditors/payments/`,
    JOURNALS: `${API_V1_BASE}/creditors/journals/`,
    CREDIT_NOTES: `${API_V1_BASE}/creditors/credit_notes/`,
    OPEN_ITEMS: `${API_V1_BASE}/creditors/open_items/`,
    LEDGER: `${API_V1_BASE}/creditors/ledger/`,
    RFC: `${API_V1_BASE}/creditors/rfcs/`,
    SUMMARY: `${API_V1_BASE}/creditors/summary/`,
    
    // Expense categories
    EXPENSE_MONTHLY: `${API_V1_BASE}/creditors/expense_monthly/`,
    EXPENSE_TRANSACTIONS: `${API_V1_BASE}/creditors/expense_transactions/`,
    
    // Dynamic endpoints for specific creditor actions
    AGED_BALANCES: (id: string | number) => `${API_V1_BASE}/creditors/creditors/${id}/aged_balances/`,
    RECALCULATE_AGED: (id: string | number) => `${API_V1_BASE}/creditors/creditors/${id}/recalculate_aged/`,
    CREDITOR_OPEN_ITEMS: (id: string | number) => `${API_V1_BASE}/creditors/creditors/${id}/open_items/`,
    CREDITOR_LEDGER: (id: string | number) => `${API_V1_BASE}/creditors/creditors/${id}/ledger/`,
    CREDITOR_TRANSACTIONS: (id: string | number) => `${API_V1_BASE}/creditors/creditors/${id}/transactions/`,
    
    // Age analysis
    AGE_ANALYSIS: `${API_V1_BASE}/creditors/creditors/age_analysis/`,
    
    // GRN endpoints
    GRNS_BY_CREDITOR: `${API_V1_BASE}/creditors/grns/by_creditor/`,
    POST_GRN: (id: string | number) => `${API_V1_BASE}/creditors/grns/${id}/post/`,
    GRN_LINES: (id: string | number) => `${API_V1_BASE}/creditors/grns/${id}/lines/`,
    
    // Invoice endpoints
    INVOICE_LINES: (id: string | number) => `${API_V1_BASE}/creditors/invoices/${id}/lines/`,
    POST_INVOICE: (id: string | number) => `${API_V1_BASE}/creditors/invoices/${id}/post/`,
    
    // Credit note endpoints
    CREDIT_NOTE_LINES: (id: string | number) => `${API_V1_BASE}/creditors/credit_notes/${id}/lines/`,
    POST_CREDIT_NOTE: (id: string | number) => `${API_V1_BASE}/creditors/credit_notes/${id}/post/`,
    
    // Payment endpoints
    POST_PAYMENT: (id: string | number) => `${API_V1_BASE}/creditors/payments/${id}/post/`,
    ALLOCATE_PAYMENT: (id: string | number) => `${API_V1_BASE}/creditors/payments/${id}/allocate/`,
    
    // Journal endpoints
    POST_JOURNAL: (id: string | number) => `${API_V1_BASE}/creditors/journals/${id}/post/`,
    
    // Open items endpoints
    OPEN_ITEMS_OUTSTANDING: `${API_V1_BASE}/creditors/open_items/outstanding/`,
    OPEN_ITEMS_BY_CREDITOR: `${API_V1_BASE}/creditors/open_items/by_creditor/`,
    OPEN_ITEM_ALLOCATIONS: `${API_V1_BASE}/creditors/open_item_allocations/`,
    OPEN_ITEM_AUDITS: `${API_V1_BASE}/creditors/open_item_audits/`,
    
    // RFC endpoints
    RFC_BY_STATUS: `${API_V1_BASE}/creditors/rfcs/by_status/`,
    RFC_UPDATE_STATUS: (id: string | number) => `${API_V1_BASE}/creditors/rfcs/${id}/update_status/`,
    RFC_LINES: (id: string | number) => `${API_V1_BASE}/creditors/rfcs/${id}/lines/`,
    
    // Expense endpoints
    EXPENSE_BY_CREDITOR: `${API_V1_BASE}/creditors/expense_transactions/by_creditor/`,
    EXPENSE_BY_CATEGORY: `${API_V1_BASE}/creditors/expense_transactions/by_category/`,
    
    // Payment orders endpoints
    PAYMENT_ORDERS: `${API_V1_BASE}/creditors/payment_orders/`,
    PAYMENT_ORDERS_PENDING: `${API_V1_BASE}/creditors/payment_orders/pending/`,
    PROCESS_PAYMENT_ORDER: (id: string | number) => `${API_V1_BASE}/creditors/payment_orders/${id}/process/`,
  },

  // ===== CASH BOOK =====
  CASH_BOOK: {
    INCOME_CATEGORIES: `${API_V1_BASE}/cash-book/income-categories/`,
    EXPENSE_CATEGORIES: `${API_V1_BASE}/cash-book/expense-categories/`,
    TRANSACTIONS: `${API_V1_BASE}/cash-book/transactions/`,
    OTHER_INCOME: `${API_V1_BASE}/cash-book/other-income/`,
    OTHER_EXPENSES: `${API_V1_BASE}/cash-book/other-expenses/`,
    BANK_DEPOSITS: `${API_V1_BASE}/cash-book/bank-deposits/`,
    CASH_WITHDRAWALS: `${API_V1_BASE}/cash-book/cash-withdrawals/`,
    BANK_TRANSFERS: `${API_V1_BASE}/cash-book/bank-transfers/`,
    BANK_CHARGES: `${API_V1_BASE}/cash-book/bank-charges/`,
    INTEREST_RECEIVED: `${API_V1_BASE}/cash-book/interest-received/`,
    RECONCILIATIONS: `${API_V1_BASE}/cash-book/bank-reconciliations/`,
    CASH_FLOATS: `${API_V1_BASE}/cash-book/cash-floats/`,
    CATEGORY_BALANCES: `${API_V1_BASE}/cash-book/expense-category-balances/`,
    UNPRESENTED_CHEQUES: `${API_V1_BASE}/cash-book/unpresented-cheques/`,
  },

  // ===== GENERAL LEDGER =====
  GENERAL_LEDGER: {
    MASTER_ACCOUNTS: `${API_V1_BASE}/general-ledger/master-accounts/`,
    TRANSACTIONS: `${API_V1_BASE}/general-ledger/transactions/`,
    STANDING_JOURNALS: `${API_V1_BASE}/general-ledger/standing-journals/`,
    SPREAD_SHEETS: `${API_V1_BASE}/general-ledger/spread-sheets/`,
  },

  // ===== STOCK CONTROL =====
  STOCK_CONTROL: {
    // ── Core resources ────────────────────────────────────────────────────
    STOCK_ITEMS:              `${API_V1_BASE}/stock-control/stock-items/`,
    SPECIAL_DEALS:            `${API_V1_BASE}/stock-control/special-deals/`,
    FUTURE_PRICING:           `${API_V1_BASE}/stock-control/future-pricing/`,
    SHRINK_WRAPS:             `${API_V1_BASE}/stock-control/shrink-wraps/`,
    PACK_BUNDLES:             `${API_V1_BASE}/stock-control/pack-bundles/`,
    PACK_BUNDLE_INGREDIENTS:  `${API_V1_BASE}/stock-control/pack-bundle-ingredients/`,
    TRANSACTIONS:             `${API_V1_BASE}/stock-control/stock-transactions/`,
    MOVEMENT_LEDGER:          `${API_V1_BASE}/stock-control/stock-movement-ledger/`,
    STOCK_TAKES:              `${API_V1_BASE}/stock-control/stock-takes/`,
    STOCK_TAKE_ITEMS:         `${API_V1_BASE}/stock-control/stock-take-items/`,
    CONTRACT_PRICING:         `${API_V1_BASE}/stock-control/contract-pricing/`,
    LOOKUP_KEYS:              `${API_V1_BASE}/stock-control/lookup-keys/`,
    MONTHLY_STATS:            `${API_V1_BASE}/stock-control/monthly-statistics/`,

    // ── Branches (IBT Phase 1) ────────────────────────────────────────────
    BRANCHES:                 `${API_V1_BASE}/stock-control/branches/`,
    BRANCH_STOCK:             `${API_V1_BASE}/stock-control/branch-stock/`,

    // ── Group Orders (Phase 3) ────────────────────────────────────────────
    GROUP_ORDERS:             `${API_V1_BASE}/stock-control/group-orders/`,
    GROUP_ORDER_ITEMS:        `${API_V1_BASE}/stock-control/group-order-items/`,

    // ── Inter-Branch Transfers (IBT Phase 4) ──────────────────────────────
    BRANCH_TRANSFERS:         `${API_V1_BASE}/stock-control/branch-transfers/`,
    BRANCH_TRANSFER_ITEMS:    `${API_V1_BASE}/stock-control/branch-transfer-items/`,

    // ── Inter-Branch Invoices (IBI Phase 5) ───────────────────────────────
    BRANCH_TRANSFER_INVOICES: `${API_V1_BASE}/stock-control/branch-transfer-invoices/`,

    // ── Stock Item dynamic actions ─────────────────────────────────────────
    STOCK_ITEM_DETAIL:          (code: string) => `${API_V1_BASE}/stock-control/stock-items/${code}/`,
    STOCK_ITEM_PRICING:         (code: string) => `${API_V1_BASE}/stock-control/stock-items/${code}/pricing/`,
    STOCK_ITEM_TRANSACTIONS:    (code: string) => `${API_V1_BASE}/stock-control/stock-items/${code}/transactions/`,
    STOCK_ITEM_MONTHLY_STATS:   (code: string) => `${API_V1_BASE}/stock-control/stock-items/${code}/monthly-stats/`,
    STOCK_ITEM_ADJUST_STOCK:    (code: string) => `${API_V1_BASE}/stock-control/stock-items/${code}/adjust-stock/`,
    STOCK_ITEMS_LOW_STOCK:      `${API_V1_BASE}/stock-control/stock-items/low-stock/`,
    STOCK_ITEMS_NEEDS_REORDER:  `${API_V1_BASE}/stock-control/stock-items/needs-reorder/`,

    // ── Special Deals dynamic actions ──────────────────────────────────────
    SPECIAL_DEALS_ACTIVE_TODAY: `${API_V1_BASE}/stock-control/special-deals/active-today/`,

    // ── Future Pricing dynamic actions ─────────────────────────────────────
    FUTURE_PRICING_APPLY:       (id: number) => `${API_V1_BASE}/stock-control/future-pricing/${id}/apply/`,

    // ── Pack Bundle dynamic actions ────────────────────────────────────────
    PACK_BUNDLE_RECALC_COST:    (code: string) => `${API_V1_BASE}/stock-control/pack-bundles/${code}/recalculate-cost/`,

    // ── Stock Take dynamic actions ──────────────────────────────────────────
    STOCK_TAKE_COMPLETE:        (id: number) => `${API_V1_BASE}/stock-control/stock-takes/${id}/complete/`,
    STOCK_TAKE_UPDATE_STOCK:    (id: number) => `${API_V1_BASE}/stock-control/stock-takes/${id}/update-stock/`,
    STOCK_TAKE_VARIANCE_REPORT: (id: number) => `${API_V1_BASE}/stock-control/stock-takes/${id}/variance-report/`,
    STOCK_TAKE_ITEM_COUNT:      (id: number) => `${API_V1_BASE}/stock-control/stock-take-items/${id}/count/`,

    // ── Branch dynamic actions ─────────────────────────────────────────────
    BRANCH_DETAIL:              (code: string) => `${API_V1_BASE}/stock-control/branches/${code}/`,
    BRANCH_STOCK_LEVELS:        (code: string) => `${API_V1_BASE}/stock-control/branches/${code}/stock/`,
    BRANCH_STOCK_LOW:           `${API_V1_BASE}/stock-control/branch-stock/low-stock/`,

    // ── Group Order dynamic actions ────────────────────────────────────────
    GROUP_ORDER_RECALC_TOTAL:   (id: number) => `${API_V1_BASE}/stock-control/group-orders/${id}/recalculate-total/`,

    // ── Branch Transfer dynamic actions ───────────────────────────────────
    TRANSFER_APPROVE:           (id: number) => `${API_V1_BASE}/stock-control/branch-transfers/${id}/approve/`,
    TRANSFER_DISPATCH:          (id: number) => `${API_V1_BASE}/stock-control/branch-transfers/${id}/dispatch/`,
    TRANSFER_RECEIVE:           (id: number) => `${API_V1_BASE}/stock-control/branch-transfers/${id}/receive/`,
    TRANSFER_CANCEL:            (id: number) => `${API_V1_BASE}/stock-control/branch-transfers/${id}/cancel/`,

    // ── Branch Transfer Invoice dynamic actions ────────────────────────────
    INVOICE_ISSUE:              (id: number) => `${API_V1_BASE}/stock-control/branch-transfer-invoices/${id}/issue/`,
    INVOICE_MARK_PAID:          (id: number) => `${API_V1_BASE}/stock-control/branch-transfer-invoices/${id}/mark-paid/`,

    // NOTE: DEPARTMENTS and SALES_AREAS are served by the SETTINGS app.
    // Use SETTINGS.DEPARTMENTS and SETTINGS.SALES_AREAS for those resources.
  },

  // ===== PURCHASE ORDERS =====
  PURCHASE_ORDERS: {
    ORDERS: `${API_V1_BASE}/purchase-orders/orders/`,
    RECEIPTS: `${API_V1_BASE}/purchase-orders/receipts/`,
    BACK_ORDERS: `${API_V1_BASE}/purchase-orders/back-orders/`,
    TEMPLATES: `${API_V1_BASE}/purchase-orders/templates/`,
    REPORTS: `${API_V1_BASE}/purchase-orders/reports/`,
  },

  // ===== POS =====
  POS: {
    CASH_SALES: `${API_V1_BASE}/pos/cash-sales/`,
    LAYBYES: `${API_V1_BASE}/pos/laybyes/`,
    QUOTATIONS: `${API_V1_BASE}/pos/quotations/`,
    PAYOUTS: `${API_V1_BASE}/pos/payouts/`,
    REPAIRS: `${API_V1_BASE}/pos/repairs/`,
    JOB_CARDS: `${API_V1_BASE}/pos/job-cards/`,
    CASH_CONTROL: `${API_V1_BASE}/pos/cash-control/`,
    RECEIPTS_ON_ACCOUNT: `${API_V1_BASE}/pos/receipts-on-account/`,
    CREDIT_NOTES: `${API_V1_BASE}/pos/credit-notes/`,
    CASH_RETURNS: `${API_V1_BASE}/pos/cash-returns/`,
    CASH_A_CHEQUE: `${API_V1_BASE}/pos/cash-a-cheque/`,
    TRANSACTION_QUERIES: `${API_V1_BASE}/pos/transaction-queries/`,
    INVOICES: `${API_V1_BASE}/pos/invoices/`,
  },

  // ===== SETTINGS =====
  SETTINGS: {
    DEPARTMENTS: `${API_V1_BASE}/settings/departments/`,
    SALES_AREAS: `${API_V1_BASE}/settings/sales-areas/`,
    INCOME_CATEGORIES: `${API_V1_BASE}/settings/income-categories/`,
    EXPENSE_CATEGORIES: `${API_V1_BASE}/settings/expense-categories/`,
    TAX_CODES: `${API_V1_BASE}/settings/tax-codes/`,
    COSTING_CATEGORIES: `${API_V1_BASE}/settings/costing-categories/`,
    PAYMENT_METHODS: `${API_V1_BASE}/settings/payment-methods/`,
    CREDIT_TERMS: `${API_V1_BASE}/settings/credit-terms/`,
    SYSTEM_CONFIG: `${API_V1_BASE}/settings/system-config/`,
    DEPARTMENT_STATS: `${API_V1_BASE}/settings/department-stats/`,
    SALES_AREA_STATS: `${API_V1_BASE}/settings/sales-area-stats/`,
    IMPORT: `${API_V1_BASE}/settings/import/`,
  },

  // ===== MESSAGING =====
  MESSAGING: {
    CONVERSATIONS: `${API_V1_BASE}/messaging/conversations/`,
    CONVERSATION_DETAIL: (id: number) => `${API_V1_BASE}/messaging/conversations/${id}/`,
    MESSAGES: (conversationId: number) => `${API_V1_BASE}/messaging/conversations/${conversationId}/messages/`,
    SEND: (conversationId: number) => `${API_V1_BASE}/messaging/conversations/${conversationId}/send/`,
    MARK_READ: (conversationId: number) => `${API_V1_BASE}/messaging/conversations/${conversationId}/mark_read/`,
  },
} as const;

/**
 * Helper function to build API URL
 */
export function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}