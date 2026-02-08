# Debtors API Integration - Index & Navigation

## 📚 Documentation Index

### For Getting Started
1. **[DEBTORS_API_SETUP.md](./DEBTORS_API_SETUP.md)** ⭐ START HERE
   - Complete overview of all components
   - Quick start instructions
   - Full API reference
   - Troubleshooting guide

### For Implementation Details
2. **[DEBTORS_API_INTEGRATION.md](./DEBTORS_API_INTEGRATION.md)**
   - 7 detailed code examples
   - Setup & initialization
   - Error handling patterns
   - Advanced usage patterns
   - Token refresh guide

### For Quick Reference
3. **[DEBTORS_API_QUICK_REFERENCE.md](./DEBTORS_API_QUICK_REFERENCE.md)**
   - Files summary
   - All endpoints (2 mins read)
   - Hook API reference
   - Client API reference
   - Common patterns

---

## 🛠️ Code Files Created

### Core API Infrastructure
```
frontend/
├── lib/
│   ├── api-config.ts ✏️ UPDATED
│   │   └── Enhanced DEBTORS endpoint configuration
│   │
│   ├── api-clients/
│   │   └── debtors-api-client.ts ✨ NEW
│   │       └── DebtorsApiClient class with all methods
│   │
│   └── hooks/
│       └── useDebtorsApi.ts ✨ NEW
│           └── 8 React hooks for all operations
│
└── components/
    └── examples/
        └── DebtorsDashboard.example.tsx ✨ NEW
            └── Complete, working example component
```

---

## 🚀 Quick Start (5 minutes)

### 1. Initialize Client
```typescript
// After login, in your auth context
import { getDebtorsApiClient } from '@/lib/api-clients/debtors-api-client';

getDebtorsApiClient('tenant-id', 'jwt-token');
```

### 2. Use in Component
```typescript
'use client';
import { useDebtors } from '@/lib/hooks/useDebtorsApi';

export function DebtorsPage() {
  const { data, loading, error } = useDebtors();
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <div>
      <h1>Debtors</h1>
      {data?.results.map(d => (
        <div key={d.dno}>{d.dname} - ${d.dcrnt}</div>
      ))}
    </div>
  );
}
```

### 3. Copy Example Component
```bash
cp frontend/components/examples/DebtorsDashboard.example.tsx \
   frontend/components/DebtorsDashboard.tsx
```

---

## 📖 What's Available

### Query Hooks (Fetch Data)
```typescript
// List debtors with search/pagination/sorting
useDebtors(params)

// Get single debtor
useDebtorById(dno)

// Get debtor transactions
useDebtorTransactions(dno, params)

// Get unpaid invoices
useOpenItems(params)

// Get age breakdown
useAgeAnalysis(dno)

// Get balance details
useBalanceDetails(dno)

// Get summary stats
useDebtorsSummary()
```

### Mutation Hook (Modify Data)
```typescript
// Create/Update/Delete/Block/Unblock
const {
  createDebtor,    // (data) => Promise
  updateDebtor,    // (dno, data) => Promise
  deleteDebtor,    // (dno) => Promise
  blockDebtor,     // (dno, reason?) => Promise
  unblockDebtor,   // (dno, reason?) => Promise
  loading,         // boolean
  error,           // ApiError | null
} = useDebtorMutation();
```

### Client Class (Advanced)
```typescript
import { DebtorsApiClient } from '@/lib/api-clients/debtors-api-client';

const client = new DebtorsApiClient('tenant', 'token');
await client.getDebtors(params);
await client.createDebtor(data);
// ... etc
```

---

## 🔌 API Endpoints Reference

### Debtor Accounts
```
GET    /api/v1/debtors/debtors/              List debtors
POST   /api/v1/debtors/debtors/              Create debtor
GET    /api/v1/debtors/debtors/{dno}/        Get debtor
PATCH  /api/v1/debtors/debtors/{dno}/        Update debtor
DELETE /api/v1/debtors/debtors/{dno}/        Delete debtor
```

### Transactions & Items
```
GET    /api/v1/debtors/transactions/                     All transactions
GET    /api/v1/debtors/debtors/{dno}/transactions/       Debtor's transactions
GET    /api/v1/debtors/open-items/                       Unpaid invoices
GET    /api/v1/debtors/post-dated-cheques/               PDC records
GET    /api/v1/debtors/audit/                            Audit trail
GET    /api/v1/debtors/sales-areas/                      Sales areas list
```

### Special Actions
```
GET    /api/v1/debtors/debtors/{dno}/age_analysis/       Age breakdown
GET    /api/v1/debtors/debtors/{dno}/balance_details/    Balance info
POST   /api/v1/debtors/debtors/{dno}/block/              Block account
POST   /api/v1/debtors/debtors/{dno}/unblock/            Unblock account
GET    /api/v1/debtors/debtors/summary/                  Summary stats
```

---

## 🔐 Authentication

All requests automatically include:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
X-Tenant-ID: <tenant_id>
```

---

## 📊 Example Usages

### Search Debtors
```typescript
const { data } = useDebtors({
  search: 'smith',
  limit: 10,
});
```

### Get Debtor Details
```typescript
const { data: debtor } = useDebtorById('DEBTOR001');
const { data: balance } = useBalanceDetails('DEBTOR001');
const { data: aging } = useAgeAnalysis('DEBTOR001');
```

### Create Debtor
```typescript
const { createDebtor, loading, error } = useDebtorMutation();

await createDebtor({
  dname: 'Smith Ltd',
  dtype: 'CN',
});
```

### Block Account
```typescript
const { blockDebtor } = useDebtorMutation();

await blockDebtor('DEBTOR001', 'Non-payment');
```

### Paginate
```typescript
const [page, setPage] = useState(0);

const { data } = useDebtors({
  limit: 20,
  offset: page * 20,
});
```

---

## 🎯 Features at a Glance

| Feature | Implemented | Hook | Client |
|---------|-------------|------|--------|
| List debtors | ✅ | `useDebtors` | `getDebtors()` |
| Get debtor | ✅ | `useDebtorById` | `getDebtorById()` |
| Create debtor | ✅ | `useDebtorMutation` | `createDebtor()` |
| Update debtor | ✅ | `useDebtorMutation` | `updateDebtor()` |
| Delete debtor | ✅ | `useDebtorMutation` | `deleteDebtor()` |
| Get transactions | ✅ | `useDebtorTransactions` | `getDebtorTransactions()` |
| Get open items | ✅ | `useOpenItems` | `getOpenItems()` |
| Age analysis | ✅ | `useAgeAnalysis` | `getAgeAnalysis()` |
| Balance details | ✅ | `useBalanceDetails` | `getBalanceDetails()` |
| Block account | ✅ | `useDebtorMutation` | `blockDebtor()` |
| Unblock account | ✅ | `useDebtorMutation` | `unblockDebtor()` |
| Get summary | ✅ | `useDebtorsSummary` | `getSummary()` |
| Search | ✅ | params | params |
| Pagination | ✅ | params | params |
| Sorting | ✅ | params | params |
| Error handling | ✅ | ✅ | ✅ |
| Type safety | ✅ | ✅ | ✅ |

---

## 🔍 File Location Guide

| Purpose | File | Type |
|---------|------|------|
| Getting started | `DEBTORS_API_SETUP.md` | 📖 Guide |
| Detailed examples | `DEBTORS_API_INTEGRATION.md` | 📖 Guide |
| Quick lookup | `DEBTORS_API_QUICK_REFERENCE.md` | 📖 Guide |
| API endpoints | `lib/api-config.ts` | 🔧 Code |
| Client class | `lib/api-clients/debtors-api-client.ts` | 🔧 Code |
| React hooks | `lib/hooks/useDebtorsApi.ts` | 🔧 Code |
| Example component | `components/examples/DebtorsDashboard.example.tsx` | 🔧 Code |

---

## 🎓 Learning Path

1. **5 min**: Read this file (overview)
2. **10 min**: Skim `DEBTORS_API_QUICK_REFERENCE.md`
3. **15 min**: Read `DEBTORS_API_SETUP.md` 
4. **20 min**: Review `DebtorsDashboard.example.tsx`
5. **20 min**: Read relevant sections in `DEBTORS_API_INTEGRATION.md`
6. **30 min**: Implement in your app
7. **20 min**: Test and debug

**Total: ~2 hours** to full implementation

---

## ❓ Common Questions

**Q: How do I use this in my component?**
A: Import the hook, initialize client after login, use it like any React hook.
See: `DEBTORS_API_INTEGRATION.md` → "EXAMPLE 1"

**Q: How do I handle errors?**
A: Check the `error` property from hooks, catch exceptions from client.
See: `DEBTORS_API_SETUP.md` → "Error Handling"

**Q: How do I search/filter/sort?**
A: Pass parameters to the hooks.
See: `DEBTORS_API_QUICK_REFERENCE.md` → "Query Parameters"

**Q: How does authentication work?**
A: Initialize once after login with token and tenant ID.
See: `DEBTORS_API_INTEGRATION.md` → "Setup & Initialization"

**Q: Can I use the client directly?**
A: Yes, for advanced use cases.
See: `DEBTORS_API_INTEGRATION.md` → "EXAMPLE 7"

---

## 📞 Support & Debugging

**For issues:**
1. Check `DEBTORS_API_SETUP.md` → "Troubleshooting"
2. Review `DEBTORS_API_QUICK_REFERENCE.md` → "Error Codes"
3. Look at appropriate example in `DEBTORS_API_INTEGRATION.md`
4. Check browser console and network tab
5. Verify token and tenant ID are set

---

## ✅ Integration Checklist

- [ ] Read setup documentation
- [ ] Initialize client after login
- [ ] Test API connectivity
- [ ] Implement in first component
- [ ] Handle loading/error states
- [ ] Test with real data
- [ ] Test pagination
- [ ] Test search/filter
- [ ] Test mutations
- [ ] Deploy to staging
- [ ] Deploy to production

---

## 🎉 You're Ready!

Everything is set up and ready to use. Start with:

**→ [DEBTORS_API_SETUP.md](./DEBTORS_API_SETUP.md)**

---

**Created:** February 8, 2026  
**Version:** 1.0.0  
**Status:** Production Ready ✅
