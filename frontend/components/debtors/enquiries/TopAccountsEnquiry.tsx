'use client';

import { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';

interface TopAccount {
  id: number;
  account_number: string;
  name: string;
  salesman?: string;
  ytd_sales: number;
  current_due: number;
  performance_percentage: number;
}

export default function TopAccountsEnquiry() {
  const [salesman, setSalesman] = useState('');
  const [area, setArea] = useState('');
  const [limit, setLimit] = useState(10);
  const [topAccounts, setTopAccounts] = useState<TopAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const generateReport = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.append('limit', limit.toString());
      if (salesman) params.append('salesman', salesman);
      if (area) params.append('area', area);

      const response = await apiRequest(`/api/v1/debtors/top-accounts/?${params}`);
      const responseData = (response as any).data || (response as any);
      const accounts = responseData.results || responseData;
      
      if (Array.isArray(accounts)) {
        setTopAccounts(accounts);
      }
    } catch (err) {
      setError('Failed to load top accounts');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-gray-900">Top Accounts - Account Performance Report</h2>

      {/* Filters */}
      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 space-y-4">
        <h3 className="font-semibold text-gray-900">Report Filters</h3>
        
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Salesman</label>
            <input
              type="text"
              value={salesman}
              onChange={(e) => setSalesman(e.target.value)}
              placeholder="Enter salesman name"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sales Area</label>
            <input
              type="text"
              value={area}
              onChange={(e) => setArea(e.target.value)}
              placeholder="Enter area code"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Top Accounts</label>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
              <option value={20}>Top 20</option>
              <option value={50}>Top 50</option>
            </select>
          </div>
        </div>

        <button 
          onClick={generateReport}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Generate Report'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Results Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Rank</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Account #</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Account Name</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Salesman</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">YTD Sales</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Current Due</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Performance %</th>
              </tr>
            </thead>
            <tbody>
              {topAccounts.length > 0 ? (
                topAccounts.map((account, index) => (
                  <tr key={account.id} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{index + 1}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">{account.account_number}</td>
                    <td className="px-4 py-3 text-gray-700">{account.name}</td>
                    <td className="px-4 py-3 text-gray-700">{account.salesman || '-'}</td>
                    <td className="px-4 py-3 text-right text-gray-900">R{account.ytd_sales.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right text-gray-900">R{account.current_due.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right font-semibold text-gray-900">{account.performance_percentage.toFixed(1)}%</td>
                  </tr>
                ))
              ) : (
                <tr className="border-b border-gray-200 hover:bg-gray-50">
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    {loading ? 'Loading...' : 'Select filters and click "Generate Report" to view top accounts'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
