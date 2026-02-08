/**
 * DEBTORS API INTEGRATION GUIDE
 * 
 * This file provides comprehensive examples of how to use the Debtors API
 * in your React components and services.
 */

// ===== SETUP & INITIALIZATION =====

/**
 * 1. INITIALIZE THE API CLIENT
 * 
 * The client requires JWT authentication and tenant isolation.
 * Initialize it in your app root or auth context:
 */

import { getDebtorsApiClient, resetDebtorsApiClient } from '@/lib/api-clients/debtors-api-client';

// After successful login, initialize the client with token and tenant ID
function initializeDebtorsApi(accessToken: string, tenantId: string) {
  const client = getDebtorsApiClient(tenantId, accessToken);
  // Client is now ready for use
}

// On logout, reset the client
function logoutUser() {
  resetDebtorsApiClient();
  // Clear other auth state...
}


// ===== EXAMPLE 1: FETCH DEBTOR LIST IN A COMPONENT =====

'use client';

import { useDebtors } from '@/lib/hooks/useDebtorsApi';

export function DebtorsList() {
  // Fetch debtors with pagination and search
  const { data, loading, error, refetch } = useDebtors({
    limit: 20,
    offset: 0,
    search: '', // Search by name or code
    ordering: 'dname', // Sort by debtor name
  });

  if (loading) return <div>Loading debtors...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h2>Debtors</h2>
      <button onClick={() => refetch()}>Refresh</button>
      <ul>
        {data?.results.map((debtor) => (
          <li key={debtor.dno}>
            {debtor.dname} - Balance: {debtor.dcrnt}
          </li>
        ))}
      </ul>
      <div>
        <p>Total: {data?.count} debtors</p>
      </div>
    </div>
  );
}


// ===== EXAMPLE 2: VIEW DEBTOR DETAILS & TRANSACTIONS =====

import { useDebtorById, useDebtorTransactions } from '@/lib/hooks/useDebtorsApi';

interface DebtorDetailProps {
  debtorNumber: string;
}

export function DebtorDetail({ debtorNumber }: DebtorDetailProps) {
  // Get debtor information
  const { data: debtor, loading: debtorLoading, error: debtorError } = useDebtorById(debtorNumber);

  // Get debtor transactions
  const { data: transactions, loading: transLoading, error: transError } = useDebtorTransactions(
    debtorNumber,
    {
      limit: 10,
      ordering: '-date', // Most recent first
    }
  );

  if (debtorLoading) return <div>Loading debtor...</div>;
  if (debtorError) return <div>Error loading debtor</div>;

  return (
    <div>
      <h2>{debtor?.dname}</h2>
      <p>Debtor Number: {debtor?.dno}</p>
      <p>Current Balance: ${debtor?.dcrnt}</p>

      <h3>Recent Transactions</h3>
      {transLoading ? (
        <div>Loading transactions...</div>
      ) : (
        <ul>
          {transactions?.results.map((trans) => (
            <li key={trans.id}>
              {trans.dtype} - ${trans.amount} ({trans.date})
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}


// ===== EXAMPLE 3: AGING ANALYSIS & BALANCE DETAILS =====

import { useAgeAnalysis, useBalanceDetails } from '@/lib/hooks/useDebtorsApi';

export function DebtorAging({ debtorNumber }: { debtorNumber: string }) {
  // Get aging breakdown
  const { data: aging, loading, error } = useAgeAnalysis(debtorNumber);

  // Get detailed balance
  const { data: balance } = useBalanceDetails(debtorNumber);

  if (loading) return <div>Loading aging analysis...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h3>Aging Analysis</h3>
      <table>
        <thead>
          <tr>
            <th>Period</th>
            <th>Amount</th>
            <th>Days</th>
          </tr>
        </thead>
        <tbody>
          {aging?.aging_buckets?.map((bucket: any) => (
            <tr key={bucket.days}>
              <td>{bucket.label}</td>
              <td>${bucket.amount}</td>
              <td>{bucket.days} days</td>
            </tr>
          ))}
        </tbody>
      </table>

      {balance && (
        <div>
          <h4>Balance Summary</h4>
          <p>Total Outstanding: ${balance.total_outstanding}</p>
          <p>Credit Limit: ${balance.credit_limit}</p>
          <p>Available Credit: ${balance.available_credit}</p>
        </div>
      )}
    </div>
  );
}


// ===== EXAMPLE 4: CREATE/UPDATE/DELETE DEBTOR =====

'use client';

import { useState } from 'react';
import { useDebtorMutation } from '@/lib/hooks/useDebtorsApi';
import type { DebtorAccount } from '@/lib/api-clients/debtors-api-client';

export function DebtorForm({ initialData }: { initialData?: DebtorAccount }) {
  const { createDebtor, updateDebtor, loading, error } = useDebtorMutation();
  const [formData, setFormData] = useState<Partial<DebtorAccount>>(
    initialData || { dname: '', dtype: 'CN' }
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (initialData?.dno) {
        // Update existing debtor
        await updateDebtor(initialData.dno, formData);
        alert('Debtor updated successfully!');
      } else {
        // Create new debtor
        await createDebtor(formData);
        alert('Debtor created successfully!');
        setFormData({ dname: '', dtype: 'CN' });
      }
    } catch (err) {
      console.error('Error:', err);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Debtor Name</label>
        <input
          type="text"
          value={formData.dname || ''}
          onChange={(e) => setFormData({ ...formData, dname: e.target.value })}
          required
        />
      </div>

      <div>
        <label>Type</label>
        <select
          value={formData.dtype || 'CN'}
          onChange={(e) => setFormData({ ...formData, dtype: e.target.value as any })}
        >
          <option value="IN">Invoice</option>
          <option value="CN">Credit Note</option>
          <option value="CS">Cash Sale</option>
          <option value="CR">Credit</option>
        </select>
      </div>

      {error && <div style={{ color: 'red' }}>Error: {error.message}</div>}

      <button type="submit" disabled={loading}>
        {loading ? 'Saving...' : 'Save Debtor'}
      </button>
    </form>
  );
}


// ===== EXAMPLE 5: BLOCK/UNBLOCK DEBTOR =====

import { useDebtorMutation } from '@/lib/hooks/useDebtorsApi';

export function BlockDebtorAction({ debtorNumber, isBlocked }: { debtorNumber: string; isBlocked: boolean }) {
  const { blockDebtor, unblockDebtor, loading, error } = useDebtorMutation();

  const handleToggleBlock = async () => {
    try {
      if (isBlocked) {
        await unblockDebtor(debtorNumber, 'Account unblocked');
      } else {
        await blockDebtor(debtorNumber, 'Account blocked due to non-payment');
      }
      alert('Action completed successfully!');
    } catch (err) {
      console.error('Error:', err);
    }
  };

  return (
    <div>
      <button onClick={handleToggleBlock} disabled={loading}>
        {loading ? 'Processing...' : isBlocked ? 'Unblock Debtor' : 'Block Debtor'}
      </button>
      {error && <p style={{ color: 'red' }}>Error: {error.message}</p>}
    </div>
  );
}


// ===== EXAMPLE 6: DEBTOR SUMMARY DASHBOARD =====

import { useDebtorsSummary, useOpenItems } from '@/lib/hooks/useDebtorsApi';

export function DebtorsDashboard() {
  const { data: summary, loading: summaryLoading } = useDebtorsSummary();
  const { data: openItems, loading: openItemsLoading } = useOpenItems({ limit: 5 });

  if (summaryLoading) return <div>Loading dashboard...</div>;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
      {/* Stats Card */}
      <div style={{ border: '1px solid #ccc', padding: '20px' }}>
        <h3>Summary</h3>
        <p>Total Debtors: {summary?.total_debtors}</p>
        <p>Total Balance: ${summary?.total_balance}</p>
        <p>Total Overdue: ${summary?.total_overdue}</p>
        <p>Blocked Accounts: {summary?.blocked_count}</p>
      </div>

      {/* Open Items Card */}
      <div style={{ border: '1px solid #ccc', padding: '20px' }}>
        <h3>Open Items</h3>
        {openItemsLoading ? (
          <p>Loading...</p>
        ) : (
          <ul>
            {openItems?.results.slice(0, 5).map((item) => (
              <li key={item.id}>
                Debtor {item.dno}: ${item.amount} due {item.due_date}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}


// ===== EXAMPLE 7: DIRECT API CLIENT USAGE (ADVANCED) =====

import { DebtorsApiClient } from '@/lib/api-clients/debtors-api-client';

async function customDebtorLogic() {
  const client = new DebtorsApiClient('tenant-123', 'jwt-token-here');

  try {
    // Get all debtors
    const debtors = await client.getDebtors({
      search: 'Smith',
      limit: 50,
    });

    // Process debtors
    for (const debtor of debtors.results) {
      console.log(`${debtor.dname} (${debtor.dno}): $${debtor.dcrnt}`);

      // Get age analysis for high balance debtors
      if (debtor.dcrnt > 10000) {
        const aging = await client.getAgeAnalysis(debtor.dno);
        console.log(`Aging: ${aging}`);
      }
    }
  } catch (error: any) {
    console.error('API Error:', error.message);
    if (error.errors) {
      console.error('Validation Errors:', error.errors);
    }
  }
}


// ===== ERROR HANDLING BEST PRACTICES =====

/**
 * Guide for handling different error scenarios:
 */

function handleDebtorsApiError(error: any) {
  if (error.status === 401) {
    // Unauthorized - token expired or missing
    console.error('Authentication failed. Please login again.');
    // Redirect to login
  } else if (error.status === 403) {
    // Forbidden - insufficient permissions
    console.error('You do not have permission to access this resource.');
  } else if (error.status === 404) {
    // Not found
    console.error('Debtor not found.');
  } else if (error.status === 400) {
    // Bad request - validation errors
    console.error('Validation errors:', error.errors);
  } else if (error.status >= 500) {
    // Server error
    console.error('Server error. Please try again later.');
  } else {
    console.error('Unknown error:', error.message);
  }
}


// ===== QUERY PARAMETERS REFERENCE =====

/**
 * Common query parameters for GET endpoints:
 * 
 * search=value          - Search by debtor name or code
 * ordering=field        - Sort by field (prefix - for descending)
 *                        Fields: dno, dname, dcrnt, created_at
 * limit=number          - Results per page (default: 20, max: 100)
 * offset=number         - Pagination offset
 * dtype=type           - Filter by type: IN, CN, CS, CR, RCP, INT, JD, JC
 * 
 * Example:
 * /api/v1/debtors/debtors/?search=smith&ordering=-dcrnt&limit=10&offset=0
 */

// ===== TENANT ISOLATION =====

/**
 * Tenant isolation is handled automatically:
 * 
 * 1. Initialize client with tenant ID:
 *    const client = getDebtorsApiClient(tenantId, accessToken);
 * 
 * 2. The X-Tenant-ID header is automatically added to all requests
 * 
 * 3. All data returned is scoped to the authenticated tenant
 * 
 * User can only access their own tenant's data
 */

// ===== AUTHENTICATION TOKEN REFRESH =====

/**
 * Handle token refresh automatically:
 */

import { getDebtorsApiClient } from '@/lib/api-clients/debtors-api-client';

async function refreshAndRetry(originalFn: () => Promise<any>) {
  try {
    return await originalFn();
  } catch (error: any) {
    if (error.status === 401) {
      // Token expired - refresh it
      try {
        const response = await fetch('/api/v1/users/auth/token/refresh/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh: localStorage.getItem('refreshToken') }),
        });

        const { access } = await response.json();

        // Update client with new token
        const client = getDebtorsApiClient();
        client.setAccessToken(access);

        // Retry original request
        return await originalFn();
      } catch (refreshError) {
        // Refresh failed - redirect to login
        throw new Error('Session expired. Please login again.');
      }
    }
    throw error;
  }
}
