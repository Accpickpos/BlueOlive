'use client';

import React, { useState, useEffect } from 'react';
import { useDebtorsAPI } from '@/lib/debtorsApi';

interface AgeingBucket {
  period: string;
  amount: number;
  percentage: number;
}

interface OpenItemTransaction {
  id: number;
  transaction_number: string;
  transaction_type: string;
  transaction_date: string;
  amount: number;
  total_amount: number;
  balance_due: number;
  is_allocated: boolean;
  days_outstanding: number;
}

interface DebtorBalanceData {
  debtor_id: number;
  account_category: string;
  current_balance: number;
  opening_balance: number;
  closing_balance: number;
  ageing_buckets?: AgeingBucket[];
  outstanding_transactions?: OpenItemTransaction[];
}

interface DebtorAccountBalanceProps {
  debtorId: number;
  accountCategory: string;
}

export default function DebtorAccountBalance({ debtorId, accountCategory }: DebtorAccountBalanceProps) {
  const [balanceData, setBalanceData] = useState<DebtorBalanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBalanceData();
  }, [debtorId, accountCategory]);

  const fetchBalanceData = async () => {
    try {
      setLoading(true);
      setError(null);
      const api = useDebtorsAPI();
      const response = await api.getDebtorBalanceDetails(debtorId);
      console.log('Balance data:', response);
      setBalanceData(response as any);
    } catch (err: any) {
      console.error('Failed to load balance data:', err);
      setError('Failed to load account balance information');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-4 text-center text-gray-500">Loading balance information...</div>;
  }

  if (error) {
    return <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded">{error}</div>;
  }

  if (!balanceData) {
    return <div className="p-4 text-center text-gray-500">No balance data available</div>;
  }

  const isBalanceForward = accountCategory === '' || accountCategory === 'Balance Forward';

  return (
    <div className="space-y-6">
      {/* Summary Section */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Account Balance Summary</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Opening Balance</p>
              <p className="text-2xl font-bold text-gray-900">
                {balanceData.opening_balance?.toFixed(2) || '0.00'}
              </p>
            </div>
            <div className="border rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Current Balance</p>
              <p className={`text-2xl font-bold ${balanceData.current_balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {balanceData.current_balance?.toFixed(2) || '0.00'}
              </p>
            </div>
            <div className="border rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Closing Balance</p>
              <p className="text-2xl font-bold text-gray-900">
                {balanceData.closing_balance?.toFixed(2) || '0.00'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {isBalanceForward ? (
        // Balance Brought Forward View
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="bg-gray-50 px-6 py-4 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Ageing Analysis (Balance Brought Forward)</h3>
            <p className="text-sm text-gray-600 mt-1">
              Outstanding amount broken down by age, with receipts allocated to relevant periods
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Period</th>
                  <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">Amount</th>
                  <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">Percentage</th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-700">Visual</th>
                </tr>
              </thead>
              <tbody>
                {balanceData.ageing_buckets?.map((bucket, idx) => {
                  const colors = [
                    'bg-green-100',
                    'bg-yellow-100',
                    'bg-orange-100',
                    'bg-red-100',
                    'bg-red-200',
                    'bg-red-300',
                    'bg-red-400',
                  ];
                  return (
                    <tr key={idx} className="border-b hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900 font-medium">{bucket.period}</td>
                      <td className="px-6 py-4 text-sm text-right text-gray-900 font-semibold">
                        {bucket.amount.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-sm text-right text-gray-900">
                        {bucket.percentage.toFixed(1)}%
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${colors[idx] || 'bg-red-500'}`}
                            style={{ width: `${Math.min(bucket.percentage, 100)}%` }}
                          ></div>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        // Open Item View
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="bg-gray-50 px-6 py-4 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Outstanding Transactions (Open Item)</h3>
            <p className="text-sm text-gray-600 mt-1">
              All outstanding and unmatched transactions. Receipts are allocated to specific invoices.
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Invoice #</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Type</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Date</th>
                  <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">Amount</th>
                  <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">Balance Due</th>
                  <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">Days Old</th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-700">Status</th>
                </tr>
              </thead>
              <tbody>
                {balanceData.outstanding_transactions?.length ? (
                  balanceData.outstanding_transactions.map((trans) => {
                    const transDate = new Date(trans.transaction_date);
                    const ageColor =
                      trans.days_outstanding <= 30
                        ? 'text-green-600'
                        : trans.days_outstanding <= 60
                          ? 'text-yellow-600'
                          : trans.days_outstanding <= 90
                            ? 'text-orange-600'
                            : 'text-red-600';

                    return (
                      <tr key={trans.id} className="border-b hover:bg-gray-50">
                        <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                          {trans.transaction_number}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">{trans.transaction_type}</td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {transDate.toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 text-sm text-right text-gray-900 font-semibold">
                          {trans.total_amount.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 text-sm text-right text-gray-900 font-bold">
                          {trans.balance_due.toFixed(2)}
                        </td>
                        <td className={`px-6 py-4 text-sm text-right font-semibold ${ageColor}`}>
                          {trans.days_outstanding} days
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span
                            className={`inline-block px-3 py-1 rounded text-xs font-medium ${
                              trans.is_allocated
                                ? 'bg-green-100 text-green-800'
                                : 'bg-yellow-100 text-yellow-800'
                            }`}
                          >
                            {trans.is_allocated ? 'Allocated' : 'Unallocated'}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                      No outstanding transactions
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
