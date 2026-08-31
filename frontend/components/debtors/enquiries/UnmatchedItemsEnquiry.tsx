'use client';

import { useState, useEffect } from 'react';
import debtorsApi from '@/lib/debtorsApi';

interface UnmatchedItem {
  id: number;
  debtor_id: number;
  debtor_name: string;
  transaction_type: string;
  transaction_number: string;
  transaction_date: string;
  amount: number;
  balance_due: number;
  days_overdue: number;
}

const TYPE_LABELS: Record<string, string> = {
  IN: 'Invoice',
  CN: 'Credit Note',
  PY: 'Payment',
  RCP: 'Receipt',
  INT: 'Interest Charge',
  JD: 'Journal Debit',
  JC: 'Journal Credit',
  DM: 'Debit Memo',
  CM: 'Credit Memo',
};

const TYPE_COLORS: Record<string, string> = {
  IN: 'bg-red-100 text-red-800',
  CN: 'bg-yellow-100 text-yellow-800',
  PY: 'bg-green-100 text-green-800',
  RCP: 'bg-green-100 text-green-800',
  INT: 'bg-purple-100 text-purple-800',
  JD: 'bg-blue-100 text-blue-800',
  JC: 'bg-blue-100 text-blue-800',
};

export default function UnmatchedItemsEnquiry() {
  const [unmatchedItems, setUnmatchedItems] = useState<UnmatchedItem[]>([]);
  const [viewMode, setViewMode] = useState<'ageing' | 'balance'>('ageing');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedDebtor, setSelectedDebtor] = useState<string>('');

  useEffect(() => {
    loadUnmatchedItems();
  }, []);

  const loadUnmatchedItems = async () => {
    try {
      // DebteopenViewSet.outstanding() lists every Open Item account's
      // unmatched/partially-allocated transactions (balancedue > 0,
      // posted='Y') directly off the Debtopen model — the same open-item
      // ledger receipt allocation posts against — rather than re-deriving
      // "unmatched" from DebtorTransaction client-side. debtor_name comes
      // straight off DebteopenSerializer (item.dno is Debtor's internal pk,
      // not its account number, so it can't be correlated against a
      // separately-loaded debtor list).
      const itemsResponse = await debtorsApi.openItems.outstanding();
      const items = ((itemsResponse as any).results || itemsResponse || []) as any[];
      const today = new Date();

      const allUnmatched: UnmatchedItem[] = items.map((item) => {
        const txDate = new Date(item.date);
        const daysOverdue = Math.max(
          0,
          Math.floor((today.getTime() - txDate.getTime()) / (1000 * 60 * 60 * 24))
        );
        return {
          id: item.id,
          debtor_id: item.debtor_account_number,
          debtor_name: item.debtor_name || `Debtor ${item.debtor_account_number}`,
          transaction_type: item.type,
          transaction_number: item.dtrano,
          transaction_date: item.date,
          amount: parseFloat(item.total),
          balance_due: parseFloat(item.balancedue),
          days_overdue: daysOverdue,
        };
      });

      setUnmatchedItems(allUnmatched);
    } catch (err) {
      setError('Failed to load unmatched items');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getTransactionTypeDisplay = (type: string) => TYPE_LABELS[type] || type;
  const getTypeColor = (type: string) => TYPE_COLORS[type] || 'bg-gray-100 text-gray-800';

  const getAgeingColor = (days: number) => {
    if (days > 180) return 'text-red-700';
    if (days > 120) return 'text-orange-700';
    if (days > 60) return 'text-yellow-700';
    return 'text-green-700';
  };

  const uniqueDebtors = [...new Set(unmatchedItems.map(item => item.debtor_name))];
  const filteredItems = selectedDebtor
    ? unmatchedItems.filter(item => item.debtor_name === selectedDebtor)
    : unmatchedItems;

  const totalBalance = filteredItems.reduce((sum, item) => sum + item.balance_due, 0);

  if (loading) {
    return <div className="p-6 text-center text-gray-500">Loading unmatched items...</div>;
  }

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-gray-900">Unmatched Open Item Transactions</h2>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
          <p className="text-xs text-blue-700 font-medium">Total Unmatched</p>
          <p className="text-2xl font-bold text-blue-900">{filteredItems.length}</p>
        </div>

        <div className="bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-lg border border-red-200">
          <p className="text-xs text-red-700 font-medium">Total Balance Due</p>
          <p className="text-2xl font-bold text-red-900">R{totalBalance.toFixed(2)}</p>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
          <p className="text-xs text-purple-700 font-medium">Debtors with Items</p>
          <p className="text-2xl font-bold text-purple-900">{uniqueDebtors.length}</p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex gap-4 items-center bg-gray-50 p-4 rounded-lg border border-gray-200">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Debtor</label>
          <select
            value={selectedDebtor}
            onChange={(e) => setSelectedDebtor(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Debtors</option>
            {uniqueDebtors.map(debtor => (
              <option key={debtor} value={debtor}>{debtor}</option>
            ))}
          </select>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('ageing')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              viewMode === 'ageing'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            View by Ageing
          </button>
          <button
            onClick={() => setViewMode('balance')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              viewMode === 'balance'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            View by Balance Due
          </button>
        </div>

        <button
          onClick={() => window.print()}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium"
        >
          Print
        </button>
      </div>

      {/* Transactions Table */}
      {filteredItems.length > 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-100 border-b border-gray-200">
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Debtor</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Type</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Transaction #</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Date</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">
                    {viewMode === 'balance' ? 'Balance Due' : 'Amount'}
                  </th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Ageing (Days)</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems
                  .sort((a, b) =>
                    viewMode === 'balance'
                      ? b.balance_due - a.balance_due
                      : b.days_overdue - a.days_overdue
                  )
                  .map(item => (
                    <tr key={item.id} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{item.debtor_name}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getTypeColor(item.transaction_type)}`}>
                          {getTransactionTypeDisplay(item.transaction_type)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-900">{item.transaction_number}</td>
                      <td className="px-4 py-3 text-gray-600">
                        {new Date(item.transaction_date).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-gray-900">
                        R{item.balance_due.toFixed(2)}
                      </td>
                      <td className={`px-4 py-3 text-right font-semibold ${getAgeingColor(item.days_overdue)}`}>
                        {item.days_overdue} days
                      </td>
                    </tr>
                  ))}
              </tbody>
              <tfoot>
                <tr className="bg-gray-100 border-t-2 border-gray-300">
                  <td colSpan={4} className="px-4 py-3 font-semibold text-gray-900">Total</td>
                  <td className="px-4 py-3 text-right font-bold text-gray-900">
                    R{filteredItems.reduce((sum, item) => sum + item.balance_due, 0).toFixed(2)}
                  </td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      ) : (
        <div className="p-8 bg-gray-50 border border-gray-200 rounded-lg text-center text-gray-600">
          <p className="text-lg">✓ No unmatched items found</p>
          <p className="text-sm mt-2">All Open Item transactions have been matched.</p>
        </div>
      )}

      {/* Ageing Summary */}
      {viewMode === 'ageing' && filteredItems.length > 0 && (
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 space-y-3">
          <h4 className="font-semibold text-gray-900">Ageing Summary</h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            {[
              { label: 'Current (0-30)', min: 0, max: 30 },
              { label: '31-60 Days', min: 31, max: 60 },
              { label: '61-120 Days', min: 61, max: 120 },
              { label: '120+ Days', min: 121, max: Infinity },
            ].map(period => {
              const items = filteredItems.filter(
                item => item.days_overdue >= period.min && item.days_overdue <= period.max
              );
              const total = items.reduce((sum, item) => sum + item.balance_due, 0);
              return (
                <div key={period.label} className="bg-white p-3 rounded border border-gray-200">
                  <p className="text-gray-600 font-medium text-xs">{period.label}</p>
                  <p className="text-lg font-bold text-gray-900">R{total.toFixed(2)}</p>
                  <p className="text-xs text-gray-500">{items.length} items</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
