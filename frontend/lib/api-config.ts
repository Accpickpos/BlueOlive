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
    ACCOUNTS: `${API_V1_BASE}/creditors/creditors/`,
    TRANSACTIONS: `${API_V1_BASE}/creditors/transactions/`,
    CREDIT_TERMS: `${API_V1_BASE}/creditors/credit-terms/`,
    GRN: `${API_V1_BASE}/creditors/grn/`,
    INVOICES: `${API_V1_BASE}/creditors/invoices/`,
    PAYMENTS: `${API_V1_BASE}/creditors/payments/`,
    JOURNALS: `${API_V1_BASE}/creditors/journals/`,
    OPEN_ITEMS: `${API_V1_BASE}/creditors/open-items/`,
    RFC: `${API_V1_BASE}/creditors/rfc/`,
    SUMMARY: `${API_V1_BASE}/creditors/summary/`,
    // Dynamic endpoints for specific creditor actions
    AGING_ANALYSIS: (id: string | number) => `${API_V1_BASE}/creditors/creditors/${id}/aging-analysis/`,
    OUTSTANDING_ITEMS: (id: string | number) => `${API_V1_BASE}/creditors/creditors/${id}/outstanding-items/`,
    OUTSTANDING_BALANCE: `${API_V1_BASE}/creditors/open-items/`,
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
    DEPARTMENTS: `${API_V1_BASE}/stock-control/departments/`,
    SALES_AREAS: `${API_V1_BASE}/stock-control/sales-areas/`,
    STOCK_ITEMS: `${API_V1_BASE}/stock-control/stock-items/`,
    SPECIAL_DEALS: `${API_V1_BASE}/stock-control/special-deals/`,
    FUTURE_PRICING: `${API_V1_BASE}/stock-control/future-pricing/`,
    SHRINK_WRAPS: `${API_V1_BASE}/stock-control/shrink-wraps/`,
    PACK_BUNDLES: `${API_V1_BASE}/stock-control/pack-bundles/`,
    TRANSACTIONS: `${API_V1_BASE}/stock-control/stock-transactions/`,
    STOCK_TAKES: `${API_V1_BASE}/stock-control/stock-takes/`,
    CONTRACT_PRICING: `${API_V1_BASE}/stock-control/contract-pricing/`,
    LOOKUP_KEYS: `${API_V1_BASE}/stock-control/lookup-keys/`,
    MONTHLY_STATS: `${API_V1_BASE}/stock-control/monthly-statistics/`,
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
