'use client';

import { useState, useEffect } from 'react';
import { ArrowRight, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import cashBookApi from '@/lib/cashBookApi';
import { BalanceCard, ReconciliationStatus, TransactionTypeBadge, CategoryBadge } from '@/components/cash-book';
import { CashBookTransaction } from '@/lib/types/cashBook';

interface DashboardData {
  totalIncome: number;
  totalExpense: number;
  netPosition: number;
  bankBalance: number;
  cashBalance: number;
  outstandingCheques: number;
  reconciliationStatus: 'RECONCILED' | 'PENDING' | 'VARIANCE';
  recentTransactions: CashBookTransaction[];
}

const QuickActionButton = ({ 
  icon: Icon, 
  label, 
  href, 
  color 
}: { 
  icon: React.ReactNode, 
  label: string, 
  href: string, 
  color: string 
}) => (
  <Link href={href}>
    <div className={`p-6 rounded-lg border-2 hover:shadow-lg transition cursor-pointer ${color}`}>
      <div className="mb-3 text-2xl">{Icon}</div>
      <p className="font-semibold text-gray-900">{label}</p>
      <p className="text-xs text-gray-600 mt-1">Manage →</p>
    </div>
  </Link>
);

export default function CashBookDashboardPage() {
  const [data, setData] = useState<Partial<DashboardData>>({
    totalIncome: 0,
    totalExpense: 0,
    netPosition: 0,
    bankBalance: 0,
    cashBalance: 0,
    outstandingCheques: 0,
    reconciliationStatus: 'PENDING',
    recentTransactions: [],
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Fetch multiple data sources in parallel
      const [incomeRes, expenseRes, transRes, reconcRes, chequesRes] = await Promise.all([
        cashBookApi.otherIncome.list({ page_size: 1 }).catch(() => ({ results: [] })),
        cashBookApi.otherExpenses.list({ page_size: 1 }).catch(() => ({ results: [] })),
        cashBookApi.transactions.list({ page_size: 5 }).catch(() => ({ results: [] })),
        cashBookApi.reconciliations.list({ page_size: 1 }).catch(() => ({ results: [] })),
        cashBookApi.unpresentedCheques.list({status: 'OUTSTANDING'}).catch(() => ({ results: [] })),
      ]);

      // Calculate totals from recent transactions
      const transactions = transRes.results || [];
      const totalIncome = transactions
        .filter((t: any) => t.amount > 0)
        .reduce((sum: number, t: any) => sum + t.amount, 0);
      const totalExpense = transactions
        .filter((t: any) => t.amount < 0)
        .reduce((sum: number, t: any) => sum + Math.abs(t.amount), 0);

      const lastReconciliation = reconcRes.results?.[0];
      
      setData({
        totalIncome,
        totalExpense,
        netPosition: totalIncome - totalExpense,
        bankBalance: lastReconciliation?.bank_statement_balance || 0,
        cashBalance: lastReconciliation?.system_balance || 0,
        outstandingCheques: chequesRes.results?.length || 0,
        reconciliationStatus: lastReconciliation?.variance === 0 ? 'RECONCILED' : 'PENDING',
        recentTransactions: transactions,
      });
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <p className="text-gray-500">Loading dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Cash Book Management</h1>
          <p className="text-gray-600 mt-2">Monitor your financial position and manage cash transactions</p>
        </div>

        {/* Error Messages */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Main Balance Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <BalanceCard
            title="Total Income"
            amount={data.totalIncome || 0}
            variant="income"
            trend={5}
          />
          <BalanceCard
            title="Total Expenses"
            amount={data.totalExpense || 0}
            variant="expense"
            trend={-3}
          />
          <BalanceCard
            title="Bank Balance"
            amount={data.bankBalance || 0}
            variant="balance"
          />
          <BalanceCard
            title="Net Position"
            amount={data.netPosition || 0}
            variant={data.netPosition! >= 0 ? 'income' : 'expense'}
            trend={data.netPosition! >= 0 ? 12 : -8}
          />
        </div>

        {/* Reconciliation Status */}
        <div className="mb-8">
          <ReconciliationStatus
            status={data.reconciliationStatus as 'RECONCILED' | 'PENDING' | 'VARIANCE'}
            varianceAmount={0}
          />
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <QuickActionButton
              icon="🏷️"
              label="Income Categories"
              href="/dashboard/cash-book/maintenance/income-categories"
              color="border-green-300 bg-green-50 hover:bg-green-100"
            />
            <QuickActionButton
              icon="🏷️"
              label="Expense Categories"
              href="/dashboard/cash-book/maintenance/expense-categories"
              color="border-orange-300 bg-orange-50 hover:bg-orange-100"
            />
            <QuickActionButton
              icon="💰"
              label="Other Income"
              href="/dashboard/cash-book/transactions/other-income"
              color="border-green-300 bg-green-50 hover:bg-green-100"
            />
            <QuickActionButton
              icon="💸"
              label="Other Expenses"
              href="/dashboard/cash-book/transactions/other-expenses"
              color="border-red-300 bg-red-50 hover:bg-red-100"
            />
            <QuickActionButton
              icon="🏦"
              label="Bank Reconciliation"
              href="/dashboard/cash-book/transactions/reconciliation"
              color="border-blue-300 bg-blue-50 hover:bg-blue-100"
            />
            <QuickActionButton
              icon="📊"
              label="Banking Enquiry"
              href="/dashboard/cash-book/enquiries/banking-account"
              color="border-purple-300 bg-purple-50 hover:bg-purple-100"
            />
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-sm text-gray-600 font-semibold">Cash Balance</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  R{(data.cashBalance || 0).toFixed(2)}
                </p>
              </div>
              <div className="text-blue-600">💵</div>
            </div>
            <p className="text-xs text-gray-600">Current cash position</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-orange-500">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-sm text-gray-600 font-semibold">Outstanding Cheques</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {data.outstandingCheques || 0}
                </p>
              </div>
              <div className="text-orange-600">📋</div>
            </div>
            <p className="text-xs text-gray-600">Awaiting presentation</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-sm text-gray-600 font-semibold">Net Surplus</p>
                <p className="text-3xl font-bold text-green-600 mt-2">
                  R{(data.netPosition || 0).toFixed(2)}
                </p>
              </div>
              <div className="text-green-600">📈</div>
            </div>
            <p className="text-xs text-gray-600">Period to date</p>
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">Recent Transactions</h2>
              <Link
                href="/dashboard/cash-book/enquiries/banking-account"
                className="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-2"
              >
                View All
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {data.recentTransactions && data.recentTransactions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-100 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Date</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Description</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Reference</th>
                    <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recentTransactions.slice(0, 5).map((trans, idx) => (
                    <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {new Date(trans.date).toLocaleDateString('en-ZA')}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">{trans.description}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{trans.reference || '-'}</td>
                      <td className="px-6 py-4 text-sm text-right font-semibold text-gray-900">
                        R{trans.amount.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500">No recent transactions</p>
            </div>
          )}
        </div>

        {/* Help Section */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-bold text-blue-900 mb-3">📚 Getting Started</h3>
          <ul className="space-y-2 text-blue-800 text-sm">
            <li>• <strong>Set up Categories:</strong> Define income and expense categories before entering transactions</li>
            <li>• <strong>Record Transactions:</strong> Use Other Income and Other Expenses to record miscellaneous transactions</li>
            <li>• <strong>Reconcile:</strong> Regularly reconcile your bank statement with system balances</li>
            <li>• <strong>Analyze:</strong> Review monthly analysis to understand your financial trends</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
