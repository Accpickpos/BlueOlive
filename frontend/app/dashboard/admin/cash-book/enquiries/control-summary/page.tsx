'use client';

import { useState, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';
import cashBookApi from '@/lib/cashBookApi';
import { BalanceCard } from '@/components/cash-book';

interface AuditTypeRow {
  audit_type: number;
  audit_type_name: string;
  value_excl_vat: string | number;
  tax_amount: string | number;
  total_incl_vat: string | number;
  transaction_count: number;
}

interface ControlSummaryData {
  start_date: string;
  end_date: string;
  by_audit_type: AuditTypeRow[];
  total_value_excl_vat: string | number;
  total_tax: string | number;
  total_incl_vat: string | number;
  transaction_count: number;
  unreconciled_bank_transaction_count: number;
  unpresented_cheques: {
    count: number;
    total_value: string | number;
    by_age: { stale: number; follow_up: number; current: number };
  };
}

// Control Summary enquiry: the reconciling totals a bookkeeper checks the
// cash book against at period end — receipts/payments by audit type, VAT
// totals, unreconciled item counts, and unpresented cheques, all in one
// glance.
export default function ControlSummaryPage() {
  const today = new Date();
  const firstOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
    .toISOString().split('T')[0];
  const todayStr = today.toISOString().split('T')[0];

  const [dateFrom, setDateFrom] = useState(firstOfMonth);
  const [dateTo, setDateTo] = useState(todayStr);
  const [data, setData] = useState<ControlSummaryData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await cashBookApi.transactions.controlSummary(dateFrom, dateTo);
      setData(result);
    } catch (err) {
      setError('Failed to load control summary');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Control Summary</h1>
          <p className="text-gray-600 mt-2">Period-end reconciling totals for the cash book</p>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <div className="mb-6 bg-white rounded-lg shadow p-4 flex gap-4 items-end flex-wrap">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">From Date</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">To Date</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={fetchData}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {loading ? 'Loading...' : 'Run Summary'}
          </button>
        </div>

        {!data ? (
          <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
            <p className="text-gray-500">{loading ? 'Loading...' : 'No data'}</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <BalanceCard title="Total Value (excl. VAT)" amount={Number(data.total_value_excl_vat)} variant="default" />
              <BalanceCard title="Total VAT" amount={Number(data.total_tax)} variant="default" />
              <BalanceCard title="Total (incl. VAT)" amount={Number(data.total_incl_vat)} variant="balance" />
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden mb-8">
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                <h2 className="font-semibold text-gray-900">By Audit Type</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Audit Type</th>
                      <th className="px-4 py-2 text-right text-xs font-semibold text-gray-600">Value</th>
                      <th className="px-4 py-2 text-right text-xs font-semibold text-gray-600">VAT</th>
                      <th className="px-4 py-2 text-right text-xs font-semibold text-gray-600">Total</th>
                      <th className="px-4 py-2 text-right text-xs font-semibold text-gray-600">Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.by_audit_type.map((row) => (
                      <tr key={row.audit_type} className="border-b border-gray-100">
                        <td className="px-4 py-2 text-sm text-gray-900">{row.audit_type_name}</td>
                        <td className="px-4 py-2 text-sm text-right">R{Number(row.value_excl_vat).toFixed(2)}</td>
                        <td className="px-4 py-2 text-sm text-right">R{Number(row.tax_amount).toFixed(2)}</td>
                        <td className="px-4 py-2 text-sm text-right font-medium">R{Number(row.total_incl_vat).toFixed(2)}</td>
                        <td className="px-4 py-2 text-sm text-right">{row.transaction_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="font-semibold text-gray-900 mb-4">Unreconciled Bank Transactions</h2>
                <p className="text-3xl font-bold text-orange-600">{data.unreconciled_bank_transaction_count}</p>
                <p className="text-sm text-gray-500 mt-1">transactions not yet reconciled</p>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="font-semibold text-gray-900 mb-4">Unpresented Cheques</h2>
                <div className="flex items-baseline gap-2 mb-2">
                  <p className="text-3xl font-bold text-orange-600">{data.unpresented_cheques.count}</p>
                  <p className="text-lg text-gray-700">R{Number(data.unpresented_cheques.total_value).toFixed(2)}</p>
                </div>
                <div className="flex gap-4 text-sm text-gray-600 mt-3">
                  <span>Current: {data.unpresented_cheques.by_age.current}</span>
                  <span>Follow-up: {data.unpresented_cheques.by_age.follow_up}</span>
                  <span className="text-red-600 font-medium">Stale: {data.unpresented_cheques.by_age.stale}</span>
                </div>
              </div>
            </div>

            <div className="mt-6 text-sm text-gray-500 text-center">
              {data.transaction_count} total transactions for {data.start_date} to {data.end_date}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
