'use client';

import { useState } from 'react';
import { apiRequest } from '@/lib/api';

interface SalesTransaction {
  id: number;
  date: string;
  description: string;
  quantity: number;
  cost_price: number;
  selling_price: number;
  gross_profit: number;
}

interface AccountData {
  account_number: string;
  account_name: string;
  sales_transactions: SalesTransaction[];
}

export default function AccountSalesHistoryEnquiry() {
  const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [accountNumber, setAccountNumber] = useState('');
  const [accountData, setAccountData] = useState<AccountData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    if (!accountNumber) {
      setError('Please enter an account number');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.append('start_date', startDate);
      params.append('end_date', endDate);
      const response = await apiRequest(`/api/debtors/${accountNumber}/sales-history/?${params}`);
      const responseData = (response as any).data || (response as any);
      setAccountData(responseData);
    } catch (err) {
      setError('Account not found or no sales history available');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-gray-900">Account Sales History</h2>

      {/* Date and Account Selection */}
      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 space-y-4">
        <h3 className="font-semibold text-gray-900">Selection Criteria</h3>
        
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Account Number</label>
            <input
              type="text"
              value={accountNumber}
              onChange={(e) => setAccountNumber(e.target.value)}
              placeholder="Enter account #"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium"
          >
            {loading ? 'Loading...' : 'Generate Report'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Account Info Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
          <p className="text-xs text-blue-700 font-medium">Account #</p>
          <p className="text-lg font-bold text-blue-900">{accountData?.account_number || '-'}</p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
          <p className="text-xs text-green-700 font-medium">Debtor Name</p>
          <p className="text-lg font-bold text-green-900">{accountData?.account_name || '-'}</p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
          <p className="text-xs text-purple-700 font-medium">Period Sales</p>
          <p className="text-lg font-bold text-purple-900">R{accountData ? accountData.sales_transactions.reduce((sum, t) => sum + (t.selling_price * t.quantity), 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}</p>
        </div>
        <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 p-4 rounded-lg border border-yellow-200">
          <p className="text-xs text-yellow-700 font-medium">Gross Profit</p>
          <p className="text-lg font-bold text-yellow-900">R{accountData ? accountData.sales_transactions.reduce((sum, t) => sum + t.gross_profit, 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}</p>
        </div>
      </div>

      {/* Sales Transactions Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Date</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Description</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Quantity</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Cost Price</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Selling Price</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Gross Profit</th>
              </tr>
            </thead>
            <tbody>
              {accountData && accountData.sales_transactions.length > 0 ? (
                accountData.sales_transactions.map((transaction) => (
                  <tr key={transaction.id} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-700">{new Date(transaction.date).toLocaleDateString('en-ZA')}</td>
                    <td className="px-4 py-3 text-gray-700">{transaction.description}</td>
                    <td className="px-4 py-3 text-right">{transaction.quantity}</td>
                    <td className="px-4 py-3 text-right">R{transaction.cost_price.toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td className="px-4 py-3 text-right">R{transaction.selling_price.toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td className="px-4 py-3 text-right font-medium">R{transaction.gross_profit.toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                  </tr>
                ))
              ) : (
                <tr className="border-b border-gray-200 hover:bg-gray-50">
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                    {accountData ? 'No sales transactions found for this period' : 'Select an account and click "Generate Report" to view sales history'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Navigation and Print Options */}
      <div className="flex flex-wrap gap-2 justify-between pt-4 border-t border-gray-200">
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium">
            ← Previous
          </button>
          <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium">
            Next →
          </button>
        </div>

        <div className="flex gap-2">
          <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium">
            View Totals
          </button>
          <button className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium">
            Print Listing
          </button>
        </div>
      </div>
    </div>
  );
}
