'use client';

import { useState, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';
import cashBookApi from '@/lib/cashBookApi';
import { BalanceCard, CategoryBadge } from '@/components/cash-book';

interface CategoryRow {
  category_id: number;
  category_name: string;
  category_code: number | string;
  value_excl_vat: string | number;
  tax_amount: string | number;
  total_incl_vat: string | number;
  transaction_count: number;
}

// Category & Tax Analysis enquiry: per-category income/expense totals for a
// period, each split into value-excl-VAT and VAT — used to check category
// totals against the VAT return for the same period.
export default function CategoryTaxAnalysisPage() {
  const today = new Date();
  const firstOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
    .toISOString().split('T')[0];
  const todayStr = today.toISOString().split('T')[0];

  const [dateFrom, setDateFrom] = useState(firstOfMonth);
  const [dateTo, setDateTo] = useState(todayStr);
  const [income, setIncome] = useState<CategoryRow[]>([]);
  const [expense, setExpense] = useState<CategoryRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await cashBookApi.transactions.categoryTaxAnalysis(dateFrom, dateTo);
      setIncome(data.income || []);
      setExpense(data.expense || []);
    } catch (err) {
      setError('Failed to load category & tax analysis');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const sum = (rows: CategoryRow[], field: keyof CategoryRow) =>
    rows.reduce((acc, r) => acc + (Number(r[field]) || 0), 0);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Category & Tax Analysis</h1>
          <p className="text-gray-600 mt-2">Income/expense by category, split by value and VAT</p>
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
            {loading ? 'Loading...' : 'Run Analysis'}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <BalanceCard title="Total Income (excl. VAT)" amount={sum(income, 'value_excl_vat')} variant="income" />
          <BalanceCard title="Total Expense (excl. VAT)" amount={sum(expense, 'value_excl_vat')} variant="expense" />
          <BalanceCard
            title="Net VAT (Output - Input)"
            amount={sum(income, 'tax_amount') - sum(expense, 'tax_amount')}
            variant="balance"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-4 py-3 bg-green-50 border-b border-green-200">
              <h2 className="font-semibold text-green-900">Income Categories</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Category</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-gray-600">Value</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-gray-600">VAT</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-gray-600">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {income.length === 0 ? (
                    <tr><td colSpan={4} className="px-4 py-6 text-center text-gray-500 text-sm">No income for this period</td></tr>
                  ) : income.map((row) => (
                    <tr key={row.category_id} className="border-b border-gray-100">
                      <td className="px-4 py-2 text-sm">
                        <CategoryBadge categoryName={row.category_name} categoryCode={String(row.category_code)} type="INCOME" />
                      </td>
                      <td className="px-4 py-2 text-sm text-right">R{Number(row.value_excl_vat).toFixed(2)}</td>
                      <td className="px-4 py-2 text-sm text-right">R{Number(row.tax_amount).toFixed(2)}</td>
                      <td className="px-4 py-2 text-sm text-right font-medium">R{Number(row.total_incl_vat).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-4 py-3 bg-red-50 border-b border-red-200">
              <h2 className="font-semibold text-red-900">Expense Categories</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Category</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-gray-600">Value</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-gray-600">VAT</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-gray-600">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {expense.length === 0 ? (
                    <tr><td colSpan={4} className="px-4 py-6 text-center text-gray-500 text-sm">No expenses for this period</td></tr>
                  ) : expense.map((row) => (
                    <tr key={row.category_id} className="border-b border-gray-100">
                      <td className="px-4 py-2 text-sm">
                        <CategoryBadge categoryName={row.category_name} categoryCode={String(row.category_code)} type="EXPENSE" />
                      </td>
                      <td className="px-4 py-2 text-sm text-right">R{Number(row.value_excl_vat).toFixed(2)}</td>
                      <td className="px-4 py-2 text-sm text-right">R{Number(row.tax_amount).toFixed(2)}</td>
                      <td className="px-4 py-2 text-sm text-right font-medium">R{Number(row.total_incl_vat).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
