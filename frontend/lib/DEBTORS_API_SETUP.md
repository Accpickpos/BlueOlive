# Debtors API Integration - Complete Setup Guide

## Overview

This integration provides a fully-featured TypeScript/React client for connecting to the BlueOlive Debtors API. It includes:

- ✅ **API Configuration** - Centralized endpoint definitions with all special actions
- ✅ **API Client** - Type-safe DebtorsApiClient class with full error handling  
- ✅ **React Hooks** - Multiple hooks for data fetching and mutations
- ✅ **Examples** - Complete working examples and usage patterns
- ✅ **Documentation** - Comprehensive guides and quick references

## Files Created

### 1. **Frontend Configuration** (`frontend/lib/api-config.ts`)
**Updated** existing config with enhanced Debtors endpoints:
- List/Create/Update/Delete debtors
- Transactions and open items
- Special actions (age analysis, balance details, block/unblock)
- All endpoints follow `/api/v1/debtors/` pattern

### 2. **API Client** (`frontend/lib/api-clients/debtors-api-client.ts`)
Core client class implementing all Debtors API operations:

**Includes:**
- Full CRUD operations (Create, Read, Update, Delete)
- Specialized queries (transactions, open items, aging, etc.)
- Account management (block/unblock)
- Proper authentication (JWT Bearer tokens)
- Tenant isolation (X-Tenant-ID header)
- Comprehensive error handling
- Type-safe interfaces

**Usage:**
```typescript
import { getDebtorsApiClient } from '@/lib/api-clients/debtors-api-client';

// Initialize after login
const client = getDebtorsApiClient(tenantId, accessToken);

// Use the client
const debtors = await client.getDebtors({ search: 'Smith' });
const aging = await client.getAgeAnalysis('DEBTOR001');
```

### 3. **React Hooks** (`frontend/lib/hooks/useDebtorsApi.ts`)
Collection of React hooks for easy component integration:

**Query Hooks:**
- `useDebtors()` - Fetch debtor list
- `useDebtorById()` - Get single debtor  
- `useDebtorTransactions()` - Get debtor transactions
- `useOpenItems()` - Get unpaid invoices
- `useAgeAnalysis()` - Get aging breakdown
- `useBalanceDetails()` - Get balance info
- `useDebtorsSummary()` - Get summary stats

**Mutation Hook:**
- `useDebtorMutation()` - For create, update, delete, block, unblock

**Features:**
- Automatic loading, error, and data state management
- Built-in pagination support
- Automatic refetch on dependency change
- Type-safe responses

**Usage:**
```typescript
import { useDebtors, useDebtorMutation } from '@/lib/hooks/useDebtorsApi';

export function MyComponent() {
  const { data, loading, error } = useDebtors();
  const { createDebtor, loading: creating } = useDebtorMutation();
  
  // Use state and callbacks
}
```

### 4. **Comprehensive Examples** (`frontend/lib/DEBTORS_API_INTEGRATION.md`)
Detailed examples demonstrating:
- API client initialization
- Fetching debtor lists
- Viewing debtor details and transactions
- Aging analysis and balance details
- Creating/updating/deleting debtors
- Blocking/unblocking accounts
- Dashboard implementation
- Error handling patterns
- Direct client usage (advanced)
- Token refresh handling

### 5. **Quick Reference** (`frontend/lib/DEBTORS_API_QUICK_REFERENCE.md`)
Quick lookup guide including:
- File structure
- All endpoints
- Authentication requirements
- Query parameters
- Using React hooks
- Using the client class
- Error codes
- Common patterns
- Best practices

### 6. **Example Component** (`frontend/components/examples/DebtorsDashboard.example.tsx`)
Complete, working dashboard component demonstrating:
- Searching debtors
- List pagination
- Selecting and viewing details
- Age analysis display
- Balance information
- Block/unblock functionality
- Loading and error states
- Modern UI with inline styles

## Quick Start

### Step 1: Configure Your Auth Context

After successful login, initialize the Debtors API client:

```typescript
// In your auth service or context
import { getDebtorsApiClient } from '@/lib/api-clients/debtors-api-client';

export async function loginUser(email: string, password: string) {
  const response = await fetch('/api/v1/users/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  const { access, user } = await response.json();

  // Initialize Debtors API client
  getDebtorsApiClient(user.tenant_id, access);

  return { access, user };
}

// On logout
export function logoutUser() {
  resetDebtorsApiClient();
  // Clear other auth state...
}
```

### Step 2: Use Hooks in Components

```typescript
'use client';

import { useDebtors } from '@/lib/hooks/useDebtorsApi';

export function DebtorsPage() {
  const { data, loading, error, refetch } = useDebtors({
    limit: 20,
    offset: 0,
  });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Debtors</h1>
      <button onClick={() => refetch()}>Refresh</button>
      <ul>
        {data?.results.map((debtor) => (
          <li key={debtor.dno}>{debtor.dname} - ${debtor.dcrnt}</li>
        ))}
      </ul>
    </div>
  );
}
```

### Step 3: Use the Example Component

Copy the DebtorsDashboard example component:

```typescript
import DebtorsDashboard from '@/components/examples/DebtorsDashboard.example';

export default function Page() {
  return <DebtorsDashboard />;
}
```

## API Endpoints Reference

### Base URL
```
/api/v1/debtors/
```

### Main Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/debtors/` | List all debtors |
| POST | `/debtors/` | Create debtor |
| GET | `/debtors/{dno}/` | Get debtor |
| PATCH | `/debtors/{dno}/` | Update debtor |
| DELETE | `/debtors/{dno}/` | Delete debtor |
| GET | `/transactions/` | List transactions |
| GET | `/open-items/` | List unpaid invoices |
| GET | `/post-dated-cheques/` | List PDCs |
| GET | `/audit/` | Get audit trail |
| GET | `/sales-areas/` | Get sales areas |

### Special Actions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/debtors/{dno}/age_analysis/` | Age breakdown |
| GET | `/debtors/{dno}/balance_details/` | Balance info |
| GET | `/debtors/{dno}/transactions/` | Debtor's transactions |
| POST | `/debtors/{dno}/block/` | Block account |
| POST | `/debtors/{dno}/unblock/` | Unblock account |
| GET | `/debtors/summary/` | Summary stats |

## Authentication

All requests require:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
X-Tenant-ID: <tenant_id>
```

Tokens obtained from: `POST /api/v1/users/auth/login/`

## Query Parameters

### Pagination
- `limit=20` - Items per page (default: 20, max: 100)
- `offset=0` - Skip N items

### Search
- `search=text` - Search by debtor name or code

### Sorting
- `ordering=field` - Sort by field
- `ordering=-field` - Reverse sort

**Valid sort fields:** `dno`, `dname`, `dcrnt`, `created_at`

### Filtering
- `dtype=type` - Filter by transaction type

**Valid types:** `IN`, `CN`, `CS`, `CR`, `RCP`, `INT`, `JD`, `JC`

### Example
```
/api/v1/debtors/debtors/?search=smith&ordering=-dcrnt&limit=10&offset=0
```

## Error Handling

The API uses standard HTTP status codes:

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process data |
| 201 | Created | Process new resource |
| 400 | Bad Request | Check validation errors |
| 401 | Unauthorized | Refresh token or login |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Check resource exists |
| 500 | Server Error | Retry or contact support |

### Error Response Format
```json
{
  "status": 400,
  "message": "Validation failed",
  "errors": {
    "dname": ["This field is required"],
    "dcrnt": ["Must be a number"]
  }
}
```

## Type Safety

All types are exported from the API client:

```typescript
import type {
  DebtorAccount,
  DebtorTransaction,
  OpenItem,
  PaginatedResponse,
  ApiError,
  QueryParams,
} from '@/lib/api-clients/debtors-api-client';
```

## Best Practices

### 1. Initialize Once
```typescript
// Do this once after login
getDebtorsApiClient(tenantId, accessToken);

// Then use throughout app
const client = getDebtorsApiClient();
```

### 2. Handle Loading States
```typescript
const { data, loading, error } = useDebtors();

if (loading) return <Spinner />;
if (error) return <ErrorAlert error={error} />;
return <List data={data} />;
```

### 3. Use Pagination
```typescript
const [page, setPage] = useState(0);
const pageSize = 20;

const { data } = useDebtors({
  limit: pageSize,
  offset: page * pageSize,
});
```

### 4. Debounce Search
```typescript
const [search, setSearch] = useState('');
const debouncedSearch = useDebounce(search, 500);

const { data } = useDebtors({ search: debouncedSearch });
```

### 5. Cache Data
```typescript
// Use React Query or SWR for caching
import { useQuery } from '@tanstack/react-query';

const { data } = useQuery({
  queryKey: ['debtors', search],
  queryFn: () => client.getDebtors({ search }),
});
```

### 6. Handle Token Refresh
```typescript
if (error.status === 401) {
  // Refresh token
  const newToken = await refreshToken();
  client.setAccessToken(newToken);
  
  // Retry request
  await refetch();
}
```

## Common Patterns

### Search and Filter
```typescript
const { data } = useDebtors({
  search: 'smith',
  dtype: 'IN', // invoices only
  ordering: '-dcrnt', // high balance first
  limit: 50,
});
```

### Get Debtor with All Details
```typescript
const { data: debtor } = useDebtorById(dno);
const { data: balance } = useBalanceDetails(dno);
const { data: aging } = useAgeAnalysis(dno);

// All loaded in parallel
```

### Create and Refresh
```typescript
const { createDebtor } = useDebtorMutation();
const { refetch } = useDebtors();

const result = await createDebtor({ dname: 'New Debtor' });
await refetch(); // Update list
```

### Pagination
```typescript
const [page, setPage] = useState(0);
const { data } = useDebtors({ 
  offset: page * 20,
  limit: 20 
});

return (
  <>
    <List items={data?.results} />
    <Pagination 
      current={page}
      total={Math.ceil((data?.count || 0) / 20)}
      onChange={setPage}
    />
  </>
);
```

## Testing

```typescript
import { getDebtorsApiClient, resetDebtorsApiClient } from '@/lib/api-clients/debtors-api-client';

describe('DebtorsApiClient', () => {
  afterEach(() => {
    resetDebtorsApiClient();
  });

  it('should fetch debtors', async () => {
    const client = getDebtorsApiClient('tenant-123', 'token-123');
    const result = await client.getDebtors();
    expect(result.results).toBeDefined();
  });
});
```

## Troubleshooting

### "401 Unauthorized"
- Check token is valid
- Check token hasn't expired
- Refresh token and retry

### "403 Forbidden"
- Check user has permissions
- Check tenant_id is correct
- Check API backend permissions

### "404 Not Found"
- Check debtor number exists
- Check endpoint URL
- Check namespace is correct

### "400 Bad Request"
- Check required fields provided
- Check field formats/types
- Check error.errors for details

### No Data Returned
- Check search parameters
- Check API backend status
- Check network tab for errors

## Next Steps

1. **Read the guides:**
   - `DEBTORS_API_INTEGRATION.md` - Detailed examples
   - `DEBTORS_API_QUICK_REFERENCE.md` - Quick lookup

2. **Review the example component:**
   - `components/examples/DebtorsDashboard.example.tsx`

3. **Integrate into your app:**
   - Initialize in auth context
   - Import hooks in components
   - Handle loading/error states

4. **Test thoroughly:**
   - Test with real data
   - Test error scenarios
   - Test pagination
   - Test on different devices

5. **Deploy and monitor:**
   - Deploy to production
   - Monitor API performance
   - Watch error logs
   - Gather user feedback

## Support

For issues or questions:
1. Check DEBTORS_API_QUICK_REFERENCE.md
2. Review DEBTORS_API_INTEGRATION.md examples
3. Check api-clients/debtors-api-client.ts implementation
4. Review hooks/useDebtorsApi.ts for hook patterns

---

**Last Updated:** February 8, 2026  
**Version:** 1.0.0  
**Status:** Ready for integration
