'use client';

import { useState, useEffect } from 'react';
import { Search, AlertCircle, CheckCircle2 } from 'lucide-react';
import cashBookApi from '@/lib/cashBookApi';
import { getApiErrorMessage } from '@/lib/api';

interface PdcCheque {
  id: number;
  cheque_number: string;
  cheque_date: string;
  value: string | number;
  total: string | number;
  tag: 'R' | 'P' | 'D' | 'U';
  is_presented: boolean;
  presented_date?: string;
  month_end_date: string;
}

const TAG_LABELS: Record<string, string> = {
  R: 'Reconciled', P: 'Pending', D: 'Disputed', U: 'Unreconciled',
};

// PDC (Post-Dated Cheque) Listing enquiry: cheques issued but not yet
// presented at the bank (UnpresentedCheque / spec CBCHEQ) — the same
// register the Bank Reconciliation's outstanding-cheque total is derived
// from (see BankReconciliationViewSet.outstanding_summary).
export default function PdcListingPage() {
  const [cheques, setCheques] = useState<PdcCheque[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showPresented, setShowPresented] = useState(false);

  useEffect(() => {
    fetchData();
  }, [showPresented]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const filters: any = { ordering: '-cheque_date' };
      if (!showPresented) filters.is_presented = false;
      const response = await cashBookApi.unpresentedCheques.list(filters);
      setCheques((response.results || []) as unknown as PdcCheque[]);
    } catch (err) {
      setError('Failed to load PDC listing');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const markPresented = async (id: number) => {
    setError('');
    setSuccess('');
    try {
      await cashBookApi.unpresentedCheques.markPresented(id);
      setSuccess('Cheque marked as presented');
      await fetchData();
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to mark cheque as presented'));
    }
  };

  const filtered = cheques.filter(c =>
    c.cheque_number.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalOutstanding = filtered
    .filter(c => !c.is_presented)
    .reduce((sum, c) => sum + (Number(c.total) || 0), 0);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">PDC Listing</h1>
          <p className="text-gray-600 mt-2">Cheques issued but not yet presented at the bank</p>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}
        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            <p className="text-green-800">{success}</p>
          </div>
        )}

        <div className="mb-6 bg-white rounded-lg shadow p-4 flex gap-4 items-end flex-wrap">
          <div className="flex-1 min-w-64">
            <label className="block text-sm font-medium text-gray-700 mb-1">Search Cheque #</label>
            <div className="relative">
              <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Cheque number..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <label className="flex items-center gap-2 pb-2">
            <input
              type="checkbox"
              checked={showPresented}
              onChange={(e) => setShowPresented(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm text-gray-700">Include presented cheques</span>
          </label>
        </div>

        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-xs text-blue-600 font-semibold">TOTAL OUTSTANDING</p>
          <p className="text-2xl font-bold text-blue-900 mt-1">R{totalOutstanding.toFixed(2)}</p>
        </div>

        {loading ? (
          <div className="text-center py-8"><p className="text-gray-500">Loading...</p></div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
            <p className="text-gray-500">No outstanding cheques found</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-100 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Cheque #</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Date</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Value</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Total</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Tag</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((c) => (
                    <tr key={c.id} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-4 py-2 text-sm font-mono text-gray-900">{c.cheque_number}</td>
                      <td className="px-4 py-2 text-sm text-gray-700">
                        {new Date(c.cheque_date).toLocaleDateString('en-ZA')}
                      </td>
                      <td className="px-4 py-2 text-sm text-right">R{Number(c.value).toFixed(2)}</td>
                      <td className="px-4 py-2 text-sm text-right font-medium">R{Number(c.total).toFixed(2)}</td>
                      <td className="px-4 py-2 text-sm">
                        <span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs font-semibold rounded-full">
                          {TAG_LABELS[c.tag] || c.tag}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-sm">
                        {c.is_presented ? (
                          <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs font-semibold rounded-full">Presented</span>
                        ) : (
                          <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded-full">Outstanding</span>
                        )}
                      </td>
                      <td className="px-4 py-2 text-sm text-right">
                        {!c.is_presented && (
                          <button
                            onClick={() => markPresented(c.id)}
                            className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-xs font-medium"
                          >
                            Mark Presented
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
