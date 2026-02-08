'use client';

/**
 * EXAMPLE: Complete Debtors Dashboard Component
 * 
 * This demonstrates:
 * - Fetching debtors list with search and pagination
 * - Displaying individual debtor details
 * - Showing age analysis
 * - Managing debtor operations (block/unblock)
 * - Error handling
 * - Loading states
 */

import { useState, useCallback } from 'react';
import {
  useDebtors,
  useDebtorById,
  useAgeAnalysis,
  useBalanceDetails,
  useDebtorMutation,
} from '@/lib/hooks/useDebtorsApi';

interface DebtorsDashboardProps {
  defaultSearch?: string;
}

export function DebtorsDashboard({ defaultSearch = '' }: DebtorsDashboardProps) {
  const [search, setSearch] = useState(defaultSearch);
  const [selectedDebtorNo, setSelectedDebtorNo] = useState<string | null>(null);
  const [pageSize] = useState(10);
  const [currentPage, setCurrentPage] = useState(0);

  // List view
  const {
    data: debtorsPage,
    loading: debtorsLoading,
    error: debtorsError,
    refetch: refetchDebtors,
  } = useDebtors({
    search,
    limit: pageSize,
    offset: currentPage * pageSize,
    ordering: '-dcrnt', // Sort by balance descending
  });

  // Detail view
  const {
    data: selectedDebtor,
    loading: debtorLoading,
    error: debtorError,
  } = useDebtorById(selectedDebtorNo || '');

  // Aging
  const {
    data: aging,
    loading: agingLoading,
    error: agingError,
  } = useAgeAnalysis(selectedDebtorNo || '');

  // Balance details
  const {
    data: balance,
    loading: balanceLoading,
    error: balanceError,
  } = useBalanceDetails(selectedDebtorNo || '');

  // Mutations
  const {
    blockDebtor,
    unblockDebtor,
    loading: mutationLoading,
    error: mutationError,
  } = useDebtorMutation();

  const handleSearch = useCallback((value: string) => {
    setSearch(value);
    setCurrentPage(0);
  }, []);

  const handleSelectDebtor = useCallback((dno: string) => {
    setSelectedDebtorNo(dno);
  }, []);

  const handleBlockDebtor = useCallback(async () => {
    if (!selectedDebtorNo) return;
    try {
      await blockDebtor(selectedDebtorNo, 'Blocked due to non-payment');
      alert('Debtor blocked successfully');
      await refetchDebtors();
    } catch (err) {
      console.error('Failed to block debtor:', err);
    }
  }, [selectedDebtorNo, blockDebtor, refetchDebtors]);

  const handleUnblockDebtor = useCallback(async () => {
    if (!selectedDebtorNo) return;
    try {
      await unblockDebtor(selectedDebtorNo, 'Account unblocked');
      alert('Debtor unblocked successfully');
      await refetchDebtors();
    } catch (err) {
      console.error('Failed to unblock debtor:', err);
    }
  }, [selectedDebtorNo, unblockDebtor, refetchDebtors]);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '2fr 3fr', gap: '20px', padding: '20px' }}>
      {/* LEFT PANEL: DEBTOR LIST */}
      <div style={{ border: '1px solid #e0e0e0', borderRadius: '8px', padding: '16px' }}>
        <h2>Debtors</h2>

        {/* Search Input */}
        <div style={{ marginBottom: '16px' }}>
          <input
            type="text"
            placeholder="Search by name or code..."
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid #ccc',
              fontSize: '14px',
            }}
          />
        </div>

        {/* Error Display */}
        {debtorsError && (
          <div style={{ color: '#d32f2f', marginBottom: '16px', padding: '8px', backgroundColor: '#ffebee', borderRadius: '4px' }}>
            Error loading debtors: {debtorsError.message}
          </div>
        )}

        {/* Loading State */}
        {debtorsLoading ? (
          <div style={{ textAlign: 'center', padding: '32px' }}>Loading debtors...</div>
        ) : (
          <>
            {/* Debtors List */}
            <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
              {debtorsPage?.results?.length ?? 0 > 0 ? (
                <ul style={{ listStyle: 'none', padding: 0 }}>
                  {debtorsPage!.results.map((debtor) => (
                    <li
                      key={debtor.dno}
                      onClick={() => handleSelectDebtor(debtor.dno)}
                      style={{
                        padding: '12px',
                        marginBottom: '8px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        backgroundColor: selectedDebtorNo === debtor.dno ? '#e3f2fd' : '#f5f5f5',
                        border: selectedDebtorNo === debtor.dno ? '2px solid #1976d2' : '1px solid #ddd',
                      }}
                    >
                      <div style={{ fontWeight: 'bold', fontSize: '14px' }}>{debtor.dname}</div>
                      <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                        {debtor.dno} • Balance: ${debtor.dcrnt?.toFixed(2) ?? '0.00'}
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <div style={{ textAlign: 'center', color: '#999', padding: '32px' }}>No debtors found</div>
              )}
            </div>

            {/* Pagination */}
            {debtorsPage && debtorsPage.count > 0 && (
              <div style={{ marginTop: '16px', display: 'flex', gap: '8px', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                  onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                  disabled={currentPage === 0}
                  style={{ padding: '6px 12px', cursor: currentPage === 0 ? 'default' : 'pointer' }}
                >
                  ← Previous
                </button>
                <span style={{ fontSize: '12px', color: '#666' }}>
                  Page {currentPage + 1} of {Math.ceil(debtorsPage.count / pageSize)}
                </span>
                <button
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={!debtorsPage.next}
                  style={{ padding: '6px 12px', cursor: debtorsPage.next ? 'pointer' : 'default' }}
                >
                  Next →
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* RIGHT PANEL: DEBTOR DETAILS */}
      <div style={{ border: '1px solid #e0e0e0', borderRadius: '8px', padding: '16px' }}>
        {selectedDebtorNo ? (
          <>
            <h2>Debtor Details</h2>

            {/* Error Display */}
            {(debtorError || balanceError || agingError || mutationError) && (
              <div style={{ color: '#d32f2f', marginBottom: '16px', padding: '8px', backgroundColor: '#ffebee', borderRadius: '4px' }}>
                Error: {debtorError?.message || balanceError?.message || agingError?.message || mutationError?.message}
              </div>
            )}

            {/* Main Info */}
            {debtorLoading ? (
              <div>Loading debtor details...</div>
            ) : selectedDebtor ? (
              <>
                <div style={{ marginBottom: '24px' }}>
                  <h3 style={{ margin: '0 0 12px' }}>{selectedDebtor.dname}</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <tbody>
                      <tr>
                        <td style={{ padding: '8px', fontWeight: 'bold', width: '40%' }}>Debtor No:</td>
                        <td style={{ padding: '8px' }}>{selectedDebtor.dno}</td>
                      </tr>
                      <tr style={{ backgroundColor: '#f9f9f9' }}>
                        <td style={{ padding: '8px', fontWeight: 'bold' }}>Type:</td>
                        <td style={{ padding: '8px' }}>{selectedDebtor.debtor_type || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td style={{ padding: '8px', fontWeight: 'bold' }}>Created:</td>
                        <td style={{ padding: '8px' }}>{selectedDebtor.created_at ? new Date(selectedDebtor.created_at).toLocaleDateString() : 'N/A'}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Balance Info */}
                {balanceLoading ? (
                  <div>Loading balance...</div>
                ) : balance ? (
                  <div style={{ marginBottom: '24px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                    <h4 style={{ marginTop: 0 }}>Balance Information</h4>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <tbody>
                        <tr>
                          <td style={{ padding: '6px', fontWeight: 'bold' }}>Outstanding:</td>
                          <td style={{ padding: '6px', color: '#d32f2f' }}>
                            ${balance.total_outstanding?.toFixed(2) ?? '0.00'}
                          </td>
                        </tr>
                        <tr style={{ backgroundColor: 'white' }}>
                          <td style={{ padding: '6px', fontWeight: 'bold' }}>Credit Limit:</td>
                          <td style={{ padding: '6px' }}>${balance.credit_limit?.toFixed(2) ?? '0.00'}</td>
                        </tr>
                        <tr>
                          <td style={{ padding: '6px', fontWeight: 'bold' }}>Available:</td>
                          <td style={{ padding: '6px', color: '#4caf50' }}>
                            ${balance.available_credit?.toFixed(2) ?? '0.00'}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                ) : null}

                {/* Age Analysis */}
                {agingLoading ? (
                  <div>Loading age analysis...</div>
                ) : aging?.aging_buckets ? (
                  <div style={{ marginBottom: '24px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                    <h4 style={{ marginTop: 0 }}>Aging Analysis</h4>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                      <thead>
                        <tr style={{ borderBottom: '2px solid #ddd' }}>
                          <th style={{ padding: '6px', textAlign: 'left', fontWeight: 'bold' }}>Period</th>
                          <th style={{ padding: '6px', textAlign: 'right', fontWeight: 'bold' }}>Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        {aging.aging_buckets.map((bucket: any, idx: number) => (
                          <tr key={idx} style={{ borderBottom: '1px solid #eee', backgroundColor: idx % 2 === 0 ? 'white' : '#fafafa' }}>
                            <td style={{ padding: '6px' }}>{bucket.label || `${bucket.days} days`}</td>
                            <td style={{ padding: '6px', textAlign: 'right', fontWeight: 'bold' }}>
                              ${bucket.amount?.toFixed(2) ?? '0.00'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : null}

                {/* Actions */}
                <div style={{ display: 'flex', gap: '8px', paddingTop: '16px', borderTop: '1px solid #eee' }}>
                  <button
                    onClick={handleBlockDebtor}
                    disabled={mutationLoading}
                    style={{
                      flex: 1,
                      padding: '10px',
                      backgroundColor: '#d32f2f',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: mutationLoading ? 'default' : 'pointer',
                      fontWeight: 'bold',
                    }}
                  >
                    {mutationLoading ? 'Processing...' : 'Block Account'}
                  </button>
                  <button
                    onClick={handleUnblockDebtor}
                    disabled={mutationLoading}
                    style={{
                      flex: 1,
                      padding: '10px',
                      backgroundColor: '#4caf50',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: mutationLoading ? 'default' : 'pointer',
                      fontWeight: 'bold',
                    }}
                  >
                    {mutationLoading ? 'Processing...' : 'Unblock Account'}
                  </button>
                </div>
              </>
            ) : (
              <div>No debtor selected</div>
            )}
          </>
        ) : (
          <div style={{ textAlign: 'center', color: '#999', padding: '64px 32px', fontSize: '16px' }}>
            Select a debtor to view details
          </div>
        )}
      </div>
    </div>
  );
}

export default DebtorsDashboard;
