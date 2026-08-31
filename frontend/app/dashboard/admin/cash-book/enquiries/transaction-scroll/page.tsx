'use client';

import { useState, useEffect } from 'react';
import { Search, AlertCircle } from 'lucide-react';
import cashBookApi from '@/lib/cashBookApi';
import { TransactionTypeBadge } from '@/components/cash-book';

interface ScrollTransaction {
  id: number;
  transaction_type: string;
  transaction_number: string;
  transaction_date: string;
  value_excl_vat: string | number;
  total_incl_vat: string | number;
  description: string;
  reference?: string;
  account_type: string;
  audit_type: number;
  bank_recon_tag: string;
  is_reconciled: boolean;
  is_receipt: boolean;
  is_payment: boolean;
}

// Transaction Scroll enquiry (manual §5.3): a continuous, ordered scroll of
// every cash book transaction (CBTRAN) — the day-to-day audit trail view,
// distinct from the category/reconciliation-focused enquiries.
export default function TransactionScrollPage() {
  const [transactions, setTransactions] = useState<ScrollTransaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [transactionType, setTransactionType] = useState('');
  const [accountType, setAccountType] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  useEffect(() => {
    fetchData();
  }, [transactionType, accountType, dateFrom, dateTo]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const filters: any = { ordering: '-transaction_date,-transaction_number' };
      if (transactionType) filters.transaction_type = transactionType;
      if (accountType) filters.account_type = accountType;
      if (dateFrom) filters.transaction_date__gte = dateFrom;
      if (dateTo) filters.transaction_date__lte = dateTo;
      if (searchTerm) filters.search = searchTerm;

      const response = await cashBookApi.transactions.list(filters);
      setTransactions((response.results || []) as unknown as ScrollTransaction[]);
    } catch (err) {
      setError('Failed to load transactions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Transaction Scroll</h1>
          <p className="text-gray-600 mt-2">Continuous, ordered scroll of every cash book transaction</p>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <div className="mb-6 bg-white rounded-lg shadow p-4 space-y-4">
          <div className="flex gap-4 flex-wrap">
            <div className="flex-1 min-w-64">
              <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Description, reference, transaction #..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && fetchData()}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Transaction Type</label>
              <select
                value={transactionType}
                onChange={(e) => setTransactionType(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Types</option>
                <option value="RECEIPT">Receipt</option>
                <option value="PAYMENT">Payment</option>
                <option value="DEPOSIT">Deposit</option>
                <option value="WITHDRAWAL">Withdrawal</option>
                <option value="TRANSFER">Transfer</option>
                <option value="BANK_CHARGE">Bank Charge</option>
                <option value="INTEREST">Interest</option>
                <option value="OTHER_INCOME">Other Income</option>
                <option value="OTHER_EXPENSE">Other Expense</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Account</label>
              <select
                value={accountType}
                onChange={(e) => setAccountType(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Accounts</option>
                <option value="CASH">Cash</option>
                <option value="BANK">Bank</option>
              </select>
            </div>
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
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8"><p className="text-gray-500">Loading transactions...</p></div>
        ) : transactions.length === 0 ? (
          <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
            <p className="text-gray-500">No transactions found</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto max-h-[70vh] overflow-y-auto">
              <table className="min-w-full">
                <thead className="bg-gray-100 border-b border-gray-200 sticky top-0">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Tran #</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Date</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Type</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Description</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Reference</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Account</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Value</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Total</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Recon</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((t) => (
                    <tr key={t.id} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-4 py-2 text-sm font-mono text-gray-700">{t.transaction_number}</td>
                      <td className="px-4 py-2 text-sm text-gray-900">
                        {new Date(t.transaction_date).toLocaleDateString('en-ZA')}
                      </td>
                      <td className="px-4 py-2 text-sm">
                        <TransactionTypeBadge type={t.transaction_type as any} />
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-900">{t.description}</td>
                      <td className="px-4 py-2 text-sm text-gray-600">{t.reference || '-'}</td>
                      <td className="px-4 py-2 text-sm text-gray-600">{t.account_type}</td>
                      <td className="px-4 py-2 text-sm text-right text-gray-700">
                        R{Number(t.value_excl_vat).toFixed(2)}
                      </td>
                      <td className={`px-4 py-2 text-sm text-right font-medium ${t.is_receipt ? 'text-green-700' : 'text-red-700'}`}>
                        {t.is_receipt ? '+' : '-'}R{Number(t.total_incl_vat).toFixed(2)}
                      </td>
                      <td className="px-4 py-2 text-sm text-center">
                        {t.is_reconciled ? (
                          <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs font-semibold rounded-full">Reconciled</span>
                        ) : (
                          <span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs font-semibold rounded-full">{t.bank_recon_tag}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="mt-4 text-sm text-gray-500">{transactions.length} transactions</div>
      </div>
    </div>
  );
}
