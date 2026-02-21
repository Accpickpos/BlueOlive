// Quick Reference - Common API Operations

// ============================================================
// AUTHENTICATION
// ============================================================
import { authApi } from '@/lib/authApi';

// Login
await authApi.login({ email: 'user@example.com', password: '...' });

// Logout
await authApi.logout();

// Get current user
await authApi.getProfile();

// Check if authenticated
const isAuth = await authApi.isAuthenticated();


// ============================================================
// DEBTORS
// ============================================================
import { debtorsApi } from '@/lib/debtorsApi';

// List all debtors
await debtorsApi.accounts.list({ page: 1 });

// Get single debtor
await debtorsApi.accounts.get(123);

// Create debtor
await debtorsApi.accounts.create({ account_number: 'D001', name: '...' });

// List debtor transactions
await debtorsApi.transactions.list({ debtor_id: 123 });

// Get open items for debtor
await debtorsApi.openItems.list({ debtor_id: 123 });

// List post-dated cheques
await debtorsApi.pdcs.list({ debtor_id: 123 });


// ============================================================
// CREDITORS
// ============================================================
import { creditorsApi } from '@/lib/creditorsApi';

// List all creditors
await creditorsApi.accounts.list({ page: 1 });

// Get creditor
await creditorsApi.accounts.get('SUPP001');

// List creditor invoices
await creditorsApi.invoices.list();

// Get creditor summary
await creditorsApi.summary.get();

// List open items
await creditorsApi.openItems.list();


// ============================================================
// CASH BOOK
// ============================================================
import { cashBookApi } from '@/lib/cashBookApi';

// Get income categories
await cashBookApi.incomeCategories.list();

// List bank deposits
await cashBookApi.deposits.list({ from_date: '2024-01-01' });

// Create bank deposit
await cashBookApi.deposits.create({ date: '2024-01-15', amount: 5000 });

// List bank reconciliations
await cashBookApi.reconciliations.list();

// Get unpresented cheques
await cashBookApi.unpresentedCheques.list();


// ============================================================
// STOCK CONTROL
// ============================================================
import { 
  getStockItems, 
  getStockItem, 
  createStockItem, 
  recordTransaction 
} from '@/lib/stockApi';

// Get all stock items
await getStockItems({ page: 1 });

// Get single stock item
await getStockItem('ITEM001');

// Create stock item
await createStockItem({ stock_code: 'NEW001', description: '...', cost_price: 100 });

// Record stock transaction
await recordTransaction({ stock_code: 'ITEM001', quantity: 10, transaction_type: 'IN' });


// ============================================================
// PURCHASE ORDERS
// ============================================================
import { purchaseOrdersApi } from '@/lib/purchaseOrdersApi';

// List purchase orders
await purchaseOrdersApi.orders.list();

// Create purchase order
await purchaseOrdersApi.orders.create({ 
  order_number: 'PO001', 
  supplier_id: 1, 
  order_date: '2024-01-15' 
});

// Approve order
await purchaseOrdersApi.orders.approve(1);

// List pending orders report
await purchaseOrdersApi.reports.getPendingOrders();


// ============================================================
// POS (POINT OF SALE)
// ============================================================
import { posAPI } from '@/lib/posApi';

// Create cash sale
await posAPI.createCashSale({
  sale_date: '2024-01-15',
  line_items: [{ item_code: '...', quantity: 1, selling_price: 100 }],
  tenders: [{ tender_type: 'CASH', amount: 100 }]
});

// Create receipt
await posAPI.createReceipt({
  debtor_account_number: 'D001',
  receipt_type: 'BALANCE_FORWARD',
  receipt_date: '2024-01-15',
  amount: 1000,
  tenders: [{ tender_type: 'CASH', amount: 1000 }]
});

// Create quotation
await posAPI.createQuotation({
  debtor_account_number: 'D001',
  quote_date: '2024-01-15',
  expiry_date: '2024-02-15',
  line_items: []
});

// Get transaction summary
await posAPI.getTransactionSummary({ 
  from_date: '2024-01-01', 
  to_date: '2024-01-31' 
});


// ============================================================
// SETTINGS
// ============================================================
import { settingsApi } from '@/lib/settingsApi';

// Get departments
await settingsApi.departments.list();

// Create department
await settingsApi.departments.create({ code: 'IT', name: 'Information Technology' });

// Get expense categories
await settingsApi.expenseCategories.list();

// Get tax codes
await settingsApi.taxCodes.list();

// Get payment methods
await settingsApi.paymentMethods.list();

// Get credit terms
await settingsApi.creditTerms.list();

// Get system configuration
await settingsApi.systemConfig.list();

// Import data - see settingsApi.import.importData() for usage


// ============================================================
// GENERAL LEDGER
// ============================================================
import { generalLedgerApi } from '@/lib/generalLedgerApi';

// List master accounts
await generalLedgerApi.masterAccounts.list();

// Get GL transaction
await generalLedgerApi.transactions.get(123);

// List standing journals
await generalLedgerApi.standingJournals.list();

// Generate trial balance
await generalLedgerApi.trialBalance.generate('2024-01-31');


// ============================================================
// TENANTS/SHOPS
// ============================================================
import { tenantsApi } from '@/lib/tenantsApi';

// Get current tenant context
await tenantsApi.currentTenant.get();

// List tenants
await tenantsApi.tenants.list();

// List shops
await tenantsApi.shops.list();

// List all available shops
await tenantsApi.allShops.list();


// ============================================================
// COMMON PATTERNS
// ============================================================

// Pagination example
const response = await debtorsApi.accounts.list({ 
  page: 2, 
  page_size: 20 
});
console.log(response.results);   // Array of items
console.log(response.count);     // Total count
console.log(response.next);      // URL to next page

// Filtering example
const filtered = await creditorsApi.accounts.list({
  search: 'ABC',
  status: 'ACTIVE'
});

// Error handling
try {
  const debtor = await debtorsApi.accounts.get(999);
} catch (error) {
  if (error.response?.status === 404) {
    console.error('Debtor not found');
  } else if (error.response?.status === 401) {
    console.error('Not authenticated');
  } else {
    console.error('Error:', error.message);
  }
}

// Updating record
const updated = await debtorsApi.accounts.update(123, {
  name: 'New Name',
  status: 'ACTIVE'
});

// Deleting record
await debtorsApi.accounts.delete(123);
