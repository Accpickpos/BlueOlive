'use client';

import { useState, useEffect } from 'react';
import { Search, Download, AlertCircle } from 'lucide-react';
import cashBookApi from '@/lib/cashBookApi';
import { BankingAccountEnquiry, CashBookTransaction } from '@/lib/types/cashBook';
import { BalanceCard, ReconciliationStatus, TransactionTypeBadge } from '@/components/cash-book';

// The real per-transaction figures this enquiry needs (running_balance_bank,
// is_receipt/is_payment, total_incl_vat, transaction_type) only exist on
// CashBookTransactionSerializer's shape — not the generic frontend
// `Transaction` type cashBookApi.transactions.list() is typed to return.
interface RealTransaction {
  id: number;
  transaction_date: string;
  transaction_type: string;
  description: string;
  reference?: string;
  total_incl_vat: string | number;
  is_receipt: boolean;
  is_payment: boolean;
  running_balance_bank: string | number;
  account_type: string;
  bank_account_number: string;
}

export default function BankingAccountEnquiryPage() {
  const [transactions, setTransactions] = useState<RealTransaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [bankAccountNumber, setBankAccountNumber] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [openingBalance, setOpeningBalance] = useState(0);

  useEffect(() => {
    if (bankAccountNumber) fetchData();
  }, [bankAccountNumber, dateFrom, dateTo]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const filters: any = {
        account_type: 'BANK',
        bank_account_number: bankAccountNumber,
        ordering: 'transaction_date,transaction_number',
      };
      if (dateFrom) filters.transaction_date__gte = dateFrom;
      if (dateTo) filters.transaction_date__lte = dateTo;

      const response = await cashBookApi.transactions.list(filters);
      const trans = (response.results || []) as unknown as RealTransaction[];
      setTransactions(trans);

      // Real opening balance: the running_balance_bank carried by the last
      // transaction on this account strictly before the period started —
      // not a hardcoded 0.
      if (dateFrom) {
        const priorResponse = await cashBookApi.transactions.list({
          account_type: 'BANK',
          bank_account_number: bankAccountNumber,
          transaction_date__lt: dateFrom,
          ordering: '-transaction_date,-transaction_number',
          page_size: 1,
        });
        const prior = (priorResponse.results || [])[0] as unknown as RealTransaction | undefined;
        setOpeningBalance(prior ? Number(prior.running_balance_bank) : 0);
      } else {
        setOpeningBalance(0);
      }
    } catch (err) {
      setError('Failed to load transactions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Real classification: is_receipt/is_payment come from the transaction's
  // actual type (RECEIPT/DEPOSIT/INTEREST/OTHER_INCOME are debits;
  // PAYMENT/WITHDRAWAL/TRANSFER/BANK_CHARGE/OTHER_EXPENSE are credits) —
  // not "assume everything is a deposit".
  const totals = transactions.reduce(
    (acc, t) => {
      const amount = Number(t.total_incl_vat) || 0;
      if (t.transaction_type === 'INTEREST') acc.interestReceived += amount;
      else if (t.transaction_type === 'BANK_CHARGE') acc.totalCharges += amount;
      else if (t.is_receipt) acc.totalDeposits += amount;
      else if (t.is_payment) acc.totalWithdrawals += amount;
      return acc;
    },
    { totalDeposits: 0, totalWithdrawals: 0, totalCharges: 0, interestReceived: 0 }
  );

  const closingBalance = transactions.length
    ? Number(transactions[transactions.length - 1].running_balance_bank)
    : openingBalance;

  const summary: Partial<BankingAccountEnquiry> = {
    opening_balance: openingBalance,
    closing_balance: closingBalance,
    total_deposits: totals.totalDeposits,
    total_withdrawals: totals.totalWithdrawals,
    total_charges: totals.totalCharges,
    interest_received: totals.interestReceived,
    reconciliation_status: 'PENDING',
  };

  const filteredTransactions = transactions.filter(t =>
    t.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.reference?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Banking Account Enquiry</h1>
          <p className="text-gray-600 mt-2">View transaction history and running balance</p>
        </div>

        {/* Messages */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Account & Filters */}
        <div className="mb-6 bg-white rounded-lg shadow p-4 space-y-4">
          <div className="flex gap-4 flex-wrap">
            <div className="flex-1 min-w-64">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Bank Account Number
              </label>
              <input
                type="text"
                placeholder="Enter bank account number..."
                value={bankAccountNumber}
                onChange={(e) => setBankAccountNumber(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                From Date
              </label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                To Date
              </label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex-1 min-w-64">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search Description/Reference
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search transactions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <button className="flex items-center gap-2 px-4 py-2 mt-7 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
        </div>

        {!bankAccountNumber ? (
          <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
            <p className="text-gray-500">Enter a bank account number to view its enquiry</p>
          </div>
        ) : (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              <BalanceCard title="Opening Balance" amount={summary.opening_balance || 0} variant="balance" />
              <BalanceCard title="Total Deposits" amount={summary.total_deposits || 0} variant="income" />
              <BalanceCard title="Total Withdrawals" amount={summary.total_withdrawals || 0} variant="expense" />
              <BalanceCard title="Bank Charges" amount={summary.total_charges || 0} variant="expense" />
              <BalanceCard title="Interest Received" amount={summary.interest_received || 0} variant="income" />
              <BalanceCard title="Closing Balance" amount={summary.closing_balance || 0} variant="balance" />
            </div>

            <div className="mb-8">
              <ReconciliationStatus
                status={summary.reconciliation_status as 'RECONCILED' | 'PENDING' | 'VARIANCE'}
              />
            </div>

            {/* Transactions List */}
            {loading ? (
              <div className="text-center py-8">
                <p className="text-gray-500">Loading transactions...</p>
              </div>
            ) : filteredTransactions.length === 0 ? (
              <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
                <p className="text-gray-500">No transactions found</p>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead className="bg-gray-100 border-b border-gray-200">
                      <tr>
                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Date</th>
                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Description</th>
                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Reference</th>
                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Type</th>
                        <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">Amount</th>
                        <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">Running Balance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTransactions.map((trans) => (
                        <tr key={trans.id} className="border-b border-gray-200 hover:bg-gray-50">
                          <td className="px-6 py-3 text-sm text-gray-900">
                            {new Date(trans.transaction_date).toLocaleDateString('en-ZA')}
                          </td>
                          <td className="px-6 py-3 text-sm text-gray-900">{trans.description}</td>
                          <td className="px-6 py-3 text-sm text-gray-600">{trans.reference || '-'}</td>
                          <td className="px-6 py-3 text-sm">
                            <TransactionTypeBadge type={trans.transaction_type as any} />
                          </td>
                          <td className={`px-6 py-3 text-sm text-right font-medium ${trans.is_receipt ? 'text-green-700' : 'text-red-700'}`}>
                            {trans.is_receipt ? '+' : '-'}R{Number(trans.total_incl_vat).toFixed(2)}
                          </td>
                          <td className="px-6 py-3 text-sm text-right font-semibold text-blue-600">
                            R{Number(trans.running_balance_bank).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Summary Footer */}
            <div className="mt-8 grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <p className="text-xs text-blue-600 font-semibold">TOTAL ITEMS</p>
                <p className="text-2xl font-bold text-blue-900 mt-1">{filteredTransactions.length}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                <p className="text-xs text-green-600 font-semibold">OPENING BALANCE</p>
                <p className="text-2xl font-bold text-green-900 mt-1">R{(summary.opening_balance || 0).toFixed(2)}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                <p className="text-xs text-green-600 font-semibold">TOTAL DEPOSITS</p>
                <p className="text-2xl font-bold text-green-900 mt-1">R{(summary.total_deposits || 0).toFixed(2)}</p>
              </div>
              <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                <p className="text-xs text-red-600 font-semibold">TOTAL WITHDRAWALS</p>
                <p className="text-2xl font-bold text-red-900 mt-1">R{(summary.total_withdrawals || 0).toFixed(2)}</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <p className="text-xs text-blue-600 font-semibold">CLOSING BALANCE</p>
                <p className="text-2xl font-bold text-blue-900 mt-1">R{(summary.closing_balance || 0).toFixed(2)}</p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
