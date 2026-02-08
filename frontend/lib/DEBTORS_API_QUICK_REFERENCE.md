/**
 * DEBTORS API - QUICK REFERENCE GUIDE
 * For developers integrating with the Debtors API
 */

// ===== FILES CREATED =====
/*
1. frontend/lib/api-config.ts (UPDATED)
   - Enhanced DEBTORS endpoint configuration
   - All special action endpoints added

2. frontend/lib/api-clients/debtors-api-client.ts (NEW)
   - Core DebtorsApiClient class
   - All API methods implemented
   - Full error handling and type safety
   - Singleton pattern for performance

3. frontend/lib/hooks/useDebtorsApi.ts (NEW)
   - React hooks for all operations
   - Automatic loading, error, and data state management
   - useDebtors() - List debtors
   - useDebtorById() - Get single debtor
   - useDebtorTransactions() - Debtor transactions
   - useOpenItems() - Unpaid invoices
   - useAgeAnalysis() - Aging breakdown
   - useBalanceDetails() - Balance info
   - useDebtorsSummary() - Overview stats
   - useDebtorMutation() - Create/Update/Delete/Block/Unblock

4. frontend/lib/DEBTORS_API_INTEGRATION.md (NEW)
   - Comprehensive examples and usage patterns
   - Best practices and error handling
*/

// ===== QUICK START =====

// 1. Initialize after login
import { getDebtorsApiClient } from '@/lib/api-clients/debtors-api-client';

getDebtorsApiClient('tenant-id-here', 'jwt-token-here');

// 2. Use in a React component
import { useDebtors } from '@/lib/hooks/useDebtorsApi';

export function MyComponent() {
  const { data, loading, error } = useDebtors();
  // Use data, loading, error states
}


// ===== API ENDPOINTS =====
/*
Debtor Lists & Details:
  GET    /api/v1/debtors/debtors/           - List all debtors (paginated)
  GET    /api/v1/debtors/debtors/{dno}/     - Get specific debtor
  POST   /api/v1/debtors/debtors/           - Create new debtor
  PATCH  /api/v1/debtors/debtors/{dno}/     - Update debtor
  DELETE /api/v1/debtors/debtors/{dno}/     - Delete debtor

Transactions:
  GET    /api/v1/debtors/transactions/              - All debtor transactions
  GET    /api/v1/debtors/debtors/{dno}/transactions/ - Debtor's transactions

Open Items (Unpaid):
  GET    /api/v1/debtors/open-items/       - Unpaid invoices

Post-Dated Cheques:
  GET    /api/v1/debtors/post-dated-cheques/ - PDC records

Audit Trail:
  GET    /api/v1/debtors/audit/            - Audit logs

Sales Areas:
  GET    /api/v1/debtors/sales-areas/      - Sales area list

Special Actions:
  GET    /api/v1/debtors/debtors/{dno}/age_analysis/      - Age breakdown
  GET    /api/v1/debtors/debtors/{dno}/balance_details/   - Balance info
  POST   /api/v1/debtors/debtors/{dno}/block/             - Block account
  POST   /api/v1/debtors/debtors/{dno}/unblock/           - Unblock account
  GET    /api/v1/debtors/debtors/summary/                 - Summary stats
*/


// ===== AUTHENTICATION =====
/*
All requests require:
  Authorization: Bearer <jwt_token>
  Content-Type: application/json
  Accept: application/json
  X-Tenant-ID: <tenant_id> (optional - inferred from token)

Token obtained from: POST /api/v1/users/auth/login/
Token refresh: POST /api/v1/users/auth/token/refresh/
*/


// ===== QUERY PARAMETERS =====
/*
Common parameters for list endpoints:

Pagination:
  limit=20          - Items per page (default: 20, max: 100)
  offset=0          - Skip N items

Searching:
  search=text       - Search by debtor name or code

Sorting:
  ordering=field    - Sort by field
  ordering=-field   - Reverse sort (- prefix)
  
  Valid fields:
    - dno (debtor number)
    - dname (debtor name)
    - dcrnt (current balance)
    - created_at (creation date)

Filtering:
  dtype=TYPE        - Filter by transaction type
  
  Valid types:
    - IN (Invoice)
    - CN (Credit Note)
    - CS (Cash Sale)
    - CR (Credit)
    - RCP (Receipt)
    - INT (Interest)
    - JD (Journal Debit)
    - JC (Journal Credit)

Example:
  /api/v1/debtors/debtors/?search=smith&ordering=-dcrnt&limit=10&offset=0
*/


// ===== REACT HOOK API =====

// Fetch debtors list
import { useDebtors } from '@/lib/hooks/useDebtorsApi';
const { data, loading, error, refetch } = useDebtors(
  { search: 'text', limit: 20, offset: 0 },
  true // enabled
);

// Fetch single debtor
import { useDebtorById } from '@/lib/hooks/useDebtorsApi';
const { data: debtor, loading, error } = useDebtorById('DEBTOR001');

// Fetch debtor transactions
import { useDebtorTransactions } from '@/lib/hooks/useDebtorsApi';
const { data: transactions } = useDebtorTransactions('DEBTOR001', { limit: 10 });

// Fetch open items
import { useOpenItems } from '@/lib/hooks/useDebtorsApi';
const { data: openItems } = useOpenItems({ limit: 50 });

// Fetch age analysis
import { useAgeAnalysis } from '@/lib/hooks/useDebtorsApi';
const { data: aging } = useAgeAnalysis('DEBTOR001');

// Fetch balance details
import { useBalanceDetails } from '@/lib/hooks/useDebtorsApi';
const { data: balance } = useBalanceDetails('DEBTOR001');

// Fetch summary
import { useDebtorsSummary } from '@/lib/hooks/useDebtorsApi';
const { data: summary } = useDebtorsSummary();

// Mutations (create/update/delete/block/unblock)
import { useDebtorMutation } from '@/lib/hooks/useDebtorsApi';
const {
  createDebtor,  // (data) => Promise
  updateDebtor,  // (dno, data) => Promise
  deleteDebtor,  // (dno) => Promise
  blockDebtor,   // (dno, reason?) => Promise
  unblockDebtor, // (dno, reason?) => Promise
  loading,       // boolean
  error,         // ApiError | null
  reset          // () => void
} = useDebtorMutation();


// ===== CLIENT CLASS API =====

import { DebtorsApiClient } from '@/lib/api-clients/debtors-api-client';

const client = new DebtorsApiClient('tenant-id', 'jwt-token');

// Core methods
await client.getDebtors(params);              // List debtors
await client.getDebtorById(dno);              // Get one debtor
await client.createDebtor(data);              // Create
await client.updateDebtor(dno, data);         // Update
await client.deleteDebtor(dno);               // Delete

// Related data
await client.getTransactions(params);         // All transactions
await client.getDebtorTransactions(dno, params); // Debtor's transactions
await client.getOpenItems(params);            // Unpaid invoices
await client.getPostDatedCheques(params);     // PDC records
await client.getAuditTrail(params);           // Audit logs
await client.getSalesAreas();                 // Sales areas

// Special actions
await client.getAgeAnalysis(dno);             // Age breakdown
await client.getBalanceDetails(dno);          // Balance info
await client.blockDebtor(dno, reason?);       // Block account
await client.unblockDebtor(dno, reason?);     // Unblock account
await client.getSummary();                    // Stats

// Setters
client.setTenantId(tenantId);                 // Change tenant
client.setAccessToken(token);                 // Update token


// ===== ERROR HANDLING =====

try {
  const debtor = await client.getDebtorById('INVALID');
} catch (error) {
  error.status         // HTTP status (401, 403, 404, 500, etc.)
  error.message        // Error message
  error.errors         // Validation errors object (if 400)
}

// Common error statuses
/*
200 - Success
201 - Created
400 - Bad Request (validation errors)
401 - Unauthorized (token missing/expired/invalid)
403 - Forbidden (insufficient permissions)
404 - Not Found (debtor doesn't exist)
500 - Server Error
*/


// ===== CONFIGURATION =====

// API base URL (from environment)
import { API_BASE_URL, buildApiUrl } from '@/lib/api-config';

API_BASE_URL  // http://localhost:8000 (or production URL)

// All endpoints
import { ENDPOINTS } from '@/lib/api-config';
ENDPOINTS.DEBTORS.ACCOUNTS
ENDPOINTS.DEBTORS.TRANSACTIONS
ENDPOINTS.DEBTORS.OPEN_ITEMS
// ... etc


// ===== BEST PRACTICES =====

/*
1. Initialize client once after login
   - Use singleton: getDebtorsApiClient(tenant, token)
   - Update token on refresh: client.setAccessToken(newToken)

2. Use hooks in React components
   - Automatic state management
   - Automatic refetch on dependency changes
   - Proper cleanup

3. Handle loading/error states
   - Show spinners/loaders while loading
   - Display error messages to users
   - Provide retry functionality

4. Paginate large datasets
   - Use limit and offset parameters
   - Implement pagination UI
   - Cache frequently accessed data

5. Tenant isolation
   - Always set tenant ID after login
   - Data is automatically scoped to tenant
   - Prevents cross-tenant data access

6. Token refresh
   - Handle 401 errors gracefully
   - Refresh token and retry request
   - Redirect to login if refresh fails

7. Error messages
   - Display user-friendly messages
   - Log detailed errors for debugging
   - Handle different error statuses

8. Type safety
   - Use provided types (DebtorAccount, etc.)
   - Check data null before accessing
   - Use proper TypeScript practices
*/


// ===== DATA TYPES =====

interface DebtorAccount {
  dno: string;           // Debtor number
  dname: string;         // Debtor name
  dcrnt: number;         // Current balance
  dtype: 'IN'|'CN'|...;  // Type
  created_at: string;    // ISO date
  [key: string]: any;    // Other fields
}

interface DebtorTransaction {
  id: string;
  dno: string;
  dtype: string;
  amount: number;
  date: string;
  [key: string]: any;
}

interface OpenItem {
  id: string;
  dno: string;
  amount: number;
  due_date: string;
  [key: string]: any;
}

interface PaginatedResponse<T> {
  count: number;          // Total items
  next: string | null;    // Next page URL
  previous: string | null; // Previous page URL
  results: T[];           // Items
}

interface ApiError {
  status: number;
  message: string;
  errors?: Record<string, string[]>;
}


// ===== COMMON PATTERNS =====

// Search debtors by name
const { data: results } = useDebtors({ search: 'Smith' });

// Get high-balance debtors sorted by balance
const { data: highBalance } = useDebtors({
  ordering: '-dcrnt',
  limit: 10
});

// Paginate through all debtors
const pageSize = 50;
const { data: page1 } = useDebtors({ limit: pageSize, offset: 0 });
const { data: page2 } = useDebtors({ limit: pageSize, offset: pageSize });

// Track state across multiple operations
const { createDebtor, updateDebtor, loading, error } = useDebtorMutation();

// Load detail page data
const { data: debtor } = useDebtorById(id);
const { data: balance } = useBalanceDetails(id);
const { data: aging } = useAgeAnalysis(id);


// ===== NEXT STEPS =====

/*
1. Read DEBTORS_API_INTEGRATION.md for detailed examples
2. Import the hooks in your components
3. Initialize client in your auth context/layout
4. Handle loading/error states properly
5. Test with real data
6. Deploy and monitor
*/
