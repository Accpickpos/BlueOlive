# API Integration Guide

## Overview

This guide documents all available API endpoints and how to use them in the frontend application. All endpoints follow the RESTful pattern and use the base URL: `/api/v1/`

## Configuration

All endpoint URLs are centralized in [lib/api-config.ts](lib/api-config.ts). Import the `ENDPOINTS` object to access any endpoint:

```typescript
import { ENDPOINTS } from './api-config';

// Example usage
const url = ENDPOINTS.DEBTORS.ACCOUNTS;  // /api/v1/debtors/debtors/
```

## API Modules

### 1. Authentication (`authApi.ts`)
**Base URL:** `/api/v1/users/auth/`

```typescript
import { authApi } from './lib/authApi';

// Get CSRF token
await authApi.getCSRFToken();

// Register new user
await authApi.signup({
  email: 'user@example.com',
  password: 'password123',
  password_confirm: 'password123'
});

// Login
await authApi.login({
  email: 'user@example.com',
  password: 'password123'
});

// Get current profile
await authApi.getProfile();

// Logout
await authApi.logout();

// Refresh token
await authApi.refreshToken();
```

**Endpoints:**
- CSRF Token: `/api/v1/users/auth/csrf/`
- Signup: `/api/v1/users/auth/signup/`
- Login: `/api/v1/users/auth/login/`
- Unified Login: `/api/v1/users/auth/unified-login/`
- Logout: `/api/v1/users/auth/logout/`
- Token Refresh: `/api/v1/users/auth/token/refresh/`
- Profile: `/api/v1/users/auth/profile/`

---

### 2. Users
**Base URL:** `/api/v1/users/`

**Endpoints:**
- Users: `/api/v1/users/users/`
- Superusers: `/api/v1/users/admin/superusers/`

---

### 3. Tenants/Shops (`tenantsApi.ts`)
**Base URL:** `/api/v1/tenants/`

```typescript
import { tenantsApi } from './lib/tenantsApi';

// List tenants
await tenantsApi.tenants.list();

// Get current tenant context
await tenantsApi.currentTenant.get();

// List shops
await tenantsApi.shops.list();

// List all available shops
await tenantsApi.allShops.list();
```

**Endpoints:**
- Tenants: `/api/v1/tenants/tenants/`
- Shops: `/api/v1/tenants/shops/`
- Current Tenant: `/api/v1/tenants/current_tenant/`
- Tenant Shops: `/api/v1/tenants/tenant_shops/`
- All Shops: `/api/v1/tenants/all_shops/`

---

### 4. Debtors (`debtorsApi.ts`)
**Base URL:** `/api/v1/debtors/`

```typescript
import { debtorsApi } from './lib/debtorsApi';

// List debtors
const debtors = await debtorsApi.accounts.list({
  search: 'ABC',
  page: 1
});

// Get single debtor
await debtorsApi.accounts.get(123);

// Create debtor
await debtorsApi.accounts.create({
  account_number: 'D001',
  name: 'Customer Name',
  // ... other fields
});

// List transactions
await debtorsApi.transactions.list();

// Get open items
await debtorsApi.openItems.list();

// List post-dated cheques
await debtorsApi.pdcs.list();

// Get sales areas
await debtorsApi.areas.list();

// Get audit trail
await debtorsApi.audit.getDebtorAudit(123);
```

**Endpoints:**
- Accounts: `/api/v1/debtors/debtors/`
- Transactions: `/api/v1/debtors/transactions/`
- Open Items: `/api/v1/debtors/open-items/`
- Post-Dated Cheques: `/api/v1/debtors/post-dated-cheques/`
- Audit: `/api/v1/debtors/audit/`
- Sales Areas: `/api/v1/debtors/sales-areas/`

---

### 5. Creditors (`creditorsApi.ts`)
**Base URL:** `/api/v1/creditors/`

```typescript
import { creditorsApi } from './lib/creditorsApi';

// List creditors
await creditorsApi.accounts.list();

// Create creditor
await creditorsApi.accounts.create({
  account_number: 'C001',
  name: 'Supplier Name'
});

// Get GRNs
await creditorsApi.grn.list();

// Get invoices
await creditorsApi.invoices.list();

// Get payments
await creditorsApi.payments.list();

// Get open items
await creditorsApi.openItems.list();

// Get summary
await creditorsApi.summary.get();
```

**Endpoints:**
- Accounts: `/api/v1/creditors/creditors/`
- GRN: `/api/v1/creditors/grn/`
- Invoices: `/api/v1/creditors/invoices/`
- Payments: `/api/v1/creditors/payments/`
- Journals: `/api/v1/creditors/journals/`
- Open Items: `/api/v1/creditors/open-items/`
- RFC: `/api/v1/creditors/rfc/`
- Expense Categories: `/api/v1/creditors/expense-categories/`
- Summary: `/api/v1/creditors/summary/`

---

### 6. Cash Book (`cashBookApi.ts`)
**Base URL:** `/api/v1/cash-book/`

```typescript
import { cashBookApi } from './lib/cashBookApi';

// Income categories
await cashBookApi.incomeCategories.list();

// Transactions
await cashBookApi.transactions.list();

// Bank deposits
await cashBookApi.deposits.list();

// Bank transfers
await cashBookApi.transfers.list();

// Bank reconciliations
await cashBookApi.reconciliations.list();

// Cash floats
await cashBookApi.floats.list();

// Unpresented cheques
await cashBookApi.unpresentedCheques.list();
```

**Endpoints:**
- Income Categories: `/api/v1/cash-book/income-categories/`
- Transactions: `/api/v1/cash-book/transactions/`
- Other Income: `/api/v1/cash-book/other-income/`
- Other Expenses: `/api/v1/cash-book/other-expenses/`
- Bank Deposits: `/api/v1/cash-book/bank-deposits/`
- Cash Withdrawals: `/api/v1/cash-book/cash-withdrawals/`
- Bank Transfers: `/api/v1/cash-book/bank-transfers/`
- Bank Charges: `/api/v1/cash-book/bank-charges/`
- Interest Received: `/api/v1/cash-book/interest-received/`
- Reconciliations: `/api/v1/cash-book/bank-reconciliations/`
- Cash Floats: `/api/v1/cash-book/cash-floats/`
- Category Balances: `/api/v1/cash-book/expense-category-balances/`
- Unpresented Cheques: `/api/v1/cash-book/unpresented-cheques/`

---

### 7. General Ledger (`generalLedgerApi.ts`)
**Base URL:** `/api/v1/general-ledger/`

```typescript
import { generalLedgerApi } from './lib/generalLedgerApi';

// Master accounts
await generalLedgerApi.masterAccounts.list();

// GL Transactions
await generalLedgerApi.transactions.list();

// Standing journals
await generalLedgerApi.standingJournals.list();

// Spread sheets
await generalLedgerApi.spreadsheets.list();

// Generate trial balance
await generalLedgerApi.trialBalance.generate('2024-01-31');
```

**Endpoints:**
- Master Accounts: `/api/v1/general-ledger/master-accounts/`
- Transactions: `/api/v1/general-ledger/transactions/`
- Standing Journals: `/api/v1/general-ledger/standing-journals/`
- Spread Sheets: `/api/v1/general-ledger/spread-sheets/`

---

### 8. Stock Control (`stockApi.ts`)
**Base URL:** `/api/v1/stock-control/`

```typescript
import {
  getStockItems,
  getStockItem,
  createStockItem,
  recordTransaction,
  getTransactions
} from './lib/stockApi';

// Get all stock items
await getStockItems();

// Get single item
await getStockItem('ITEM001');

// Create stock item
await createStockItem({
  stock_code: 'NEW001',
  description: 'New Item',
  department: 1,
  cost_price: 100,
  // ... other fields
});

// Record transaction
await recordTransaction({
  stock_code: 'ITEM001',
  quantity: 10,
  transaction_type: 'IN'
});

// Get transactions
await getTransactions();
```

**Endpoints:**
- Departments: `/api/v1/stock-control/departments/`
- Sales Areas: `/api/v1/stock-control/sales-areas/`
- Stock Items: `/api/v1/stock-control/stock-items/`
- Special Deals: `/api/v1/stock-control/special-deals/`
- Future Pricing: `/api/v1/stock-control/future-pricing/`
- Shrink Wraps: `/api/v1/stock-control/shrink-wraps/`
- Pack Bundles: `/api/v1/stock-control/pack-bundles/`
- Transactions: `/api/v1/stock-control/stock-transactions/`
- Stock Takes: `/api/v1/stock-control/stock-takes/`
- Contract Pricing: `/api/v1/stock-control/contract-pricing/`
- Lookup Keys: `/api/v1/stock-control/lookup-keys/`
- Monthly Stats: `/api/v1/stock-control/monthly-statistics/`

---

### 9. Purchase Orders (`purchaseOrdersApi.ts`)
**Base URL:** `/api/v1/purchase-orders/`

```typescript
import { purchaseOrdersApi } from './lib/purchaseOrdersApi';

// List orders
await purchaseOrdersApi.orders.list();

// Create order
await purchaseOrdersApi.orders.create({
  order_number: 'PO001',
  supplier_id: 1,
  order_date: '2024-01-15'
});

// Approve order
await purchaseOrdersApi.orders.approve(1);

// Get receipts
await purchaseOrdersApi.receipts.list();

// Get back orders
await purchaseOrdersApi.backOrders.list();

// Get reports
await purchaseOrdersApi.reports.getPendingOrders();
```

**Endpoints:**
- Orders: `/api/v1/purchase-orders/orders/`
- Receipts: `/api/v1/purchase-orders/receipts/`
- Back Orders: `/api/v1/purchase-orders/back-orders/`
- Templates: `/api/v1/purchase-orders/templates/`
- Reports: `/api/v1/purchase-orders/reports/`

---

### 10. POS (`posApi.ts`)
**Base URL:** `/api/v1/pos/`

```typescript
import { posAPI } from './lib/posApi';

// Cash Sales
await posAPI.createCashSale({
  sale_date: '2024-01-15',
  line_items: [],
  tenders: []
});

// Receipts
await posAPI.createReceipt({
  debtor_account_number: 'D001',
  receipt_date: '2024-01-15',
  amount: 1000,
  tenders: []
});

// Laybyes
await posAPI.createLaybye({
  debtor_account_number: 'D001',
  description: 'Laybye Item',
  deposit_amount: 500,
  line_items: []
});

// Quotations
await posAPI.createQuotation({
  debtor_account_number: 'D001',
  quote_date: '2024-01-15',
  expiry_date: '2024-02-15',
  line_items: []
});

// Transaction summary
await posAPI.getTransactionSummary({
  from_date: '2024-01-01',
  to_date: '2024-01-31'
});
```

**Endpoints:**
- Cash Sales: `/api/v1/pos/cash-sales/`
- Laybyes: `/api/v1/pos/laybyes/`
- Quotations: `/api/v1/pos/quotations/`
- Payouts: `/api/v1/pos/payouts/`
- Repairs: `/api/v1/pos/repairs/`
- Job Cards: `/api/v1/pos/job-cards/`
- Cash Control: `/api/v1/pos/cash-control/`
- Receipts on Account: `/api/v1/pos/receipts-on-account/`
- Credit Notes: `/api/v1/pos/credit-notes/`
- Cash Returns: `/api/v1/pos/cash-returns/`
- Cash a Cheque: `/api/v1/pos/cash-a-cheque/`
- Transaction Queries: `/api/v1/pos/transaction-queries/`

---

### 11. Settings (`settingsApi.ts`)
**Base URL:** `/api/v1/settings/`

```typescript
import { settingsApi } from './lib/settingsApi';

// Departments
await settingsApi.departments.list();

// Sales Areas
await settingsApi.salesAreas.list();

// Income Categories
await settingsApi.incomeCategories.list();

// Expense Categories
await settingsApi.expenseCategories.list();

// Tax Codes
await settingsApi.taxCodes.list();

// Payment Methods
await settingsApi.paymentMethods.list();

// Credit Terms
await settingsApi.creditTerms.list();

// System Config
await settingsApi.systemConfig.list();

// Department Stats
await settingsApi.departmentStats.list();

// Sales Area Stats
await settingsApi.salesAreaStats.list();

// Import data
const formData = new FormData();
formData.append('file', file);
await settingsApi.import.importData(file, 'inventory');
```

**Endpoints:**
- Departments: `/api/v1/settings/departments/`
- Sales Areas: `/api/v1/settings/sales-areas/`
- Income Categories: `/api/v1/settings/income-categories/`
- Expense Categories: `/api/v1/settings/expense-categories/`
- Tax Codes: `/api/v1/settings/tax-codes/`
- Costing Categories: `/api/v1/settings/costing-categories/`
- Payment Methods: `/api/v1/settings/payment-methods/`
- Credit Terms: `/api/v1/settings/credit-terms/`
- System Config: `/api/v1/settings/system-config/`
- Department Stats: `/api/v1/settings/department-stats/`
- Sales Area Stats: `/api/v1/settings/sales-area-stats/`
- Import: `/api/v1/settings/import/`

---

## Common Patterns

### Pagination
Most list endpoints support pagination:

```typescript
const response = await debtorsApi.accounts.list({
  page: 1,
  page_size: 20,
  search: 'search_term'
});

console.log(response.results);     // Array of items
console.log(response.count);       // Total count
console.log(response.next);        // URL to next page
console.log(response.previous);    // URL to previous page
```

### Filtering
Most list endpoints support filtering by query parameters:

```typescript
await debtorsApi.accounts.list({
  search: 'John',
  status: 'ACTIVE',
  page: 1
});
```

### CRUD Operations
Standard CRUD operations are available on most resources:

```typescript
// Create
const created = await debtorsApi.accounts.create(data);

// Read
const item = await debtorsApi.accounts.get(id);
const list = await debtorsApi.accounts.list();

// Update
const updated = await debtorsApi.accounts.update(id, data);

// Delete
await debtorsApi.accounts.delete(id);
```

## Error Handling

All API calls use the shared axios instance with automatic error handling:

```typescript
try {
  const result = await debtorsApi.accounts.list();
} catch (error) {
  if (error.response?.status === 404) {
    console.error('Not found');
  } else if (error.response?.status === 401) {
    console.error('Unauthorized');
  } else {
    console.error('Error:', error.message);
  }
}
```

## Authentication

- All requests automatically include credentials (cookies)
- CSRF token is automatically fetched and included for POST/PUT/PATCH/DELETE requests
- Access tokens are stored in secure httpOnly cookies set by the backend

## Best Practices

1. **Always use ENDPOINTS configuration** - Never hardcode URLs
2. **Use the appropriate API module** - e.g., use `debtorsApi` for debtor operations
3. **Handle errors properly** - Wrap API calls in try-catch blocks
4. **Use filters and pagination** - For better performance with large datasets
5. **Type your data** - Use TypeScript interfaces provided by each API module

## Adding New Endpoints

When adding new endpoints:

1. Add the endpoint URL to [lib/api-config.ts](lib/api-config.ts) in the appropriate section
2. Create or update the corresponding API module file
3. Export the API object as default
4. Add helper functions/methods that use the ENDPOINTS configuration
5. Document the new endpoints in this guide
