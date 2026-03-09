'use client';

import { useState } from 'react';
import { apiRequest } from '@/lib/api';

interface PDCData {
  id: number;
  cheque_number: string;
  account_number: string;
  account_name: string;
  bank: string;
  post_date: string;
  amount: number;
  status: string;
}

type SortOrder = 'account' | 'date';

export default function PostDatedChequeListingEnquiry() {
  const [sortBy, setSortBy] = useState<SortOrder>('date');
  const [pdcList, setPDCList] = useState<PDCData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const generateListing = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.append('sort', sortBy === 'account' ? 'account_number' : 'post_date');
      const response = await apiRequest(`/api/v1/debtors/post-dated-cheques/?${params}`);
      const responseData = (response as any).data || (response as any);
      const pdcs = responseData.results || responseData;
      if (Array.isArray(pdcs)) {
        setPDCList(pdcs);
      }
    } catch (err) {
      setError('Failed to load PDC listing');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-gray-900">Post Dated Cheque Listing</h2>

      {/* Sort Options */}
      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 space-y-4">
        <h3 className="font-semibold text-gray-900">Display Options</h3>
        
        <div className="flex gap-4">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              checked={sortBy === 'account'}
              onChange={() => setSortBy('account')}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Order by Account</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              checked={sortBy === 'date'}
              onChange={() => setSortBy('date')}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Order by Date</span>
          </label>
        </div>

        <button 
          onClick={generateListing}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium"
        >
          {loading ? 'Loading...' : 'Generate Listing'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
          <p className="text-xs text-blue-700 font-medium">Total PDCs</p>
          <p className="text-2xl font-bold text-blue-900">{pdcList.length}</p>
        </div>
        <div className="bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-lg border border-red-200">
          <p className="text-xs text-red-700 font-medium">Total Amount</p>
          <p className="text-2xl font-bold text-red-900">R{pdcList.reduce((sum, pdc) => sum + pdc.amount, 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
          <p className="text-xs text-green-700 font-medium">Pending PDCs</p>
          <p className="text-2xl font-bold text-green-900">{pdcList.filter(p => p.status === 'pending').length}</p>
        </div>
      </div>

      {/* PDC Listing Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Account #</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Debtor Name</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Cheque #</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Bank</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Post Date</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Amount</th>
                <th className="px-4 py-3 text-center font-semibold text-gray-700">Status</th>
              </tr>
            </thead>
            <tbody>
              {pdcList.length > 0 ? (
                pdcList.map((pdc) => (
                  <tr key={pdc.id} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{pdc.account_number}</td>
                    <td className="px-4 py-3 text-gray-700">{pdc.account_name}</td>
                    <td className="px-4 py-3 text-gray-700">{pdc.cheque_number}</td>
                    <td className="px-4 py-3 text-gray-700">{pdc.bank}</td>
                    <td className="px-4 py-3 text-gray-700">{new Date(pdc.post_date).toLocaleDateString('en-ZA')}</td>
                    <td className="px-4 py-3 text-right font-medium">R{pdc.amount.toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        pdc.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {pdc.status}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr className="border-b border-gray-200 hover:bg-gray-50">
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    No Post Dated Cheques to display
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="flex gap-2 justify-end">
        <button className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium">
          Print Listing
        </button>
      </div>
    </div>
  );
}
