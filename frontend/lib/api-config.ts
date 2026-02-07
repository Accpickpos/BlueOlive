/**
 * API Configuration
 * Centralized configuration for API endpoints
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
export const POS_API_BASE_URL = process.env.NEXT_PUBLIC_POS_API_BASE || 'http://localhost:8001';

// API endpoint paths
export const ENDPOINTS = {
  // Creditors API
  CREDITORS: {
    BASE: `${API_BASE_URL}/api/creditors`,
    ENQUIRIES: `${API_BASE_URL}/api/creditors/enquiries`,
    INDIVIDUAL_ACCOUNT: `${API_BASE_URL}/api/creditors/enquiries/individual_account`,
    AGE_ANALYSIS: `${API_BASE_URL}/api/creditors/enquiries/age_analysis`,
    CONTROL_ENQUIRY: `${API_BASE_URL}/api/creditors/enquiries/control_enquiry`,
    TRANSACTION_SCROLL: `${API_BASE_URL}/api/creditors/enquiries/transaction_scroll`,
    EXPENDITURE_TOTALS: `${API_BASE_URL}/api/creditors/enquiries/expenditure_totals`,
    EXPENSE_CATEGORY_TOTALS: `${API_BASE_URL}/api/creditors/enquiries/expense_category_totals`,
    EXPENSE_CATEGORY_DETAILS: `${API_BASE_URL}/api/creditors/enquiries/expense_category_details`,
    MONTHLY_EXPENSE_DETAILS: `${API_BASE_URL}/api/creditors/enquiries/monthly_expense_details`,
    PURCHASE_HISTORY: `${API_BASE_URL}/api/creditors/enquiries/purchase_history`,
  },
  // Creditors Reports API
  REPORTS: {
    BASE: `${API_BASE_URL}/api/creditors/reports`,
    ACCOUNT_DETAILS: `${API_BASE_URL}/api/creditors/reports/account_details`,
    AGE_ANALYSIS_REPORT: `${API_BASE_URL}/api/creditors/reports/age_analysis`,
    REMITTANCE_ADVICES: `${API_BASE_URL}/api/creditors/reports/remittance_advices`,
    TRANSACTIONS_REPORT: `${API_BASE_URL}/api/creditors/reports/transactions`,
    EXPENSE_TAX_REPORT: `${API_BASE_URL}/api/creditors/reports/expense_tax`,
    PAYOUTS_REPORT: `${API_BASE_URL}/api/creditors/reports/payouts`,
  },
};
