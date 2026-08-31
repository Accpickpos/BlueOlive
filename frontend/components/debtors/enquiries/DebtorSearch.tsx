'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { ENDPOINTS } from '@/lib/api-config';
import { SearchCombobox, type SearchComboboxResults } from '@/components/ui/search-combobox';

interface Debtor {
  id: number;
  name: string;
  account_number: string;
  acctype: string;
  balance: number;
}

interface DebtorSearchProps {
  onSelect: (debtor: Debtor) => void;
}

/**
 * Debtor lookup for enquiry flows — same SearchCombobox every other
 * debtor/stock/creditor picker uses, with a "Recent Debtors" quick-pick
 * panel shown while the search box is empty.
 */
export default function DebtorSearch({ onSelect }: DebtorSearchProps) {
  const [recentDebtors, setRecentDebtors] = useState<Debtor[]>([]);

  useEffect(() => {
    api.get<{ results: Debtor[] }>(`${ENDPOINTS.DEBTORS.ACCOUNTS}lookup/`, { params: { limit: 6 } })
      .then((response) => setRecentDebtors(response.data?.results || []))
      .catch((err) => console.error('Failed to load recent debtors', err));
  }, []);

  const search = async (query: string, offset: number): Promise<SearchComboboxResults<Debtor>> => {
    const response = await api.get<{ results: Debtor[]; count: number; has_more: boolean }>(
      `${ENDPOINTS.DEBTORS.ACCOUNTS}lookup/`,
      { params: { search: query, limit: 20, offset } }
    );
    return {
      results: response.data?.results || [],
      count: response.data?.count,
      hasMore: response.data?.has_more || false,
    };
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Select Debtor Account</h2>

      <SearchCombobox<Debtor>
        queryKeyPrefix="debtor-enquiry-lookup"
        searchFn={search}
        getId={(debtor) => debtor.id}
        getLabel={(debtor) => debtor.name}
        onSelect={onSelect}
        label="Enter Account Number or Debtor Name"
        placeholder="Search by account number or name..."
        renderOption={(debtor) => (
          <>
            <div className="font-medium text-gray-900">{debtor.name}</div>
            <div className="text-sm text-gray-600">
              Account: {debtor.account_number} | Balance: R{Number(debtor.balance || 0).toFixed(2)}
            </div>
          </>
        )}
        emptyQuerySlot={
          recentDebtors.length > 0 ? (
            <div>
              <h3 className="font-semibold text-blue-900 mb-3">Recent Debtors</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {recentDebtors.slice(0, 6).map((debtor) => (
                  <button
                    key={debtor.id}
                    type="button"
                    onClick={() => onSelect(debtor)}
                    className="text-left p-3 rounded-lg bg-white hover:bg-blue-100 border border-blue-100 hover:border-blue-300 transition-colors"
                  >
                    <div className="font-medium text-sm text-gray-900">{debtor.name}</div>
                    <div className="text-xs text-gray-600">{debtor.account_number}</div>
                  </button>
                ))}
              </div>
            </div>
          ) : null
        }
      />
    </div>
  );
}
