'use client';

import { useState, useEffect } from 'react';
import { AlertCircle, Download } from 'lucide-react';
import cashBookApi from '@/lib/cashBookApi';
import { MonthlyAnalysis } from '@/lib/types/cashBook';
import { BalanceCard, CategoryBadge } from '@/components/cash-book';

interface MonthData {
  month: string;
  monthNumber: number;
  year: number;
  totalIncome: number;
  totalExpense: number;
  netPosition: number;
  transactionCount: number;
  categoryBreakdown: Array<{
    categoryName: string;
    categoryCode: string;
    amount: number;
    count: number;
    type: 'INCOME' | 'EXPENSE';
  }>;
}

export default function MonthlyAnalysisPage() {
  const [monthlyData, setMonthlyData] = useState<MonthData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedMonth, setSelectedMonth] = useState<MonthData | null>(null);
  const [categoryLoading, setCategoryLoading] = useState(false);

  const [summary, setSummary] = useState({
    yearToDateIncome: 0,
    yearToDateExpense: 0,
    yearToDateNet: 0,
    averageMonthlyIncome: 0,
    averageMonthlyExpense: 0,
  });

  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  useEffect(() => {
    fetchData();
  }, [selectedYear]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      // Real per-month totals, computed server-side from posted
      // transactions (CashBookReportService.get_monthly_category_series) —
      // replaces the former Math.random() placeholder.
      const series: Array<{
        month: number;
        total_income: string | number;
        total_expense: string | number;
        transaction_count: number;
      }> = await cashBookApi.transactions.monthlyCategorySeries(selectedYear);

      const monthlyBreakdown: MonthData[] = series
        .sort((a, b) => a.month - b.month)
        .map((row) => {
          const totalIncome = Number(row.total_income) || 0;
          const totalExpense = Number(row.total_expense) || 0;
          return {
            month: months[row.month - 1],
            monthNumber: row.month,
            year: selectedYear,
            totalIncome,
            totalExpense,
            netPosition: totalIncome - totalExpense,
            transactionCount: row.transaction_count,
            // Populated on-demand per month when clicked — see
            // handleSelectMonth (a whole-year breakdown would misrepresent
            // itself as this specific month's numbers).
            categoryBreakdown: [],
          };
        });

      setMonthlyData(monthlyBreakdown);
      setSelectedMonth(null);

      const ytdIncome = monthlyBreakdown.reduce((sum, m) => sum + m.totalIncome, 0);
      const ytdExpense = monthlyBreakdown.reduce((sum, m) => sum + m.totalExpense, 0);
      const activeMonths = monthlyBreakdown.filter(m => m.totalIncome > 0 || m.totalExpense > 0).length;

      setSummary({
        yearToDateIncome: ytdIncome,
        yearToDateExpense: ytdExpense,
        yearToDateNet: ytdIncome - ytdExpense,
        averageMonthlyIncome: activeMonths > 0 ? ytdIncome / activeMonths : 0,
        averageMonthlyExpense: activeMonths > 0 ? ytdExpense / activeMonths : 0,
      });
    } catch (err) {
      setError('Failed to load analysis data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getMonthColor = (month: MonthData) => {
    if (month.netPosition > 0) return 'border-green-500 bg-green-50 hover:bg-green-100';
    if (month.netPosition < 0) return 'border-red-500 bg-red-50 hover:bg-red-100';
    return 'border-gray-300 bg-gray-50 hover:bg-gray-100';
  };

  const getMonthStatus = (month: MonthData) => {
    if (month.netPosition > 0) return 'Surplus';
    if (month.netPosition < 0) return 'Deficit';
    return 'Break-even';
  };

  const handleSelectMonth = async (month: MonthData) => {
    setSelectedMonth(month);
    if (month.categoryBreakdown.length > 0) return;

    setCategoryLoading(true);
    try {
      const lastDay = new Date(month.year, month.monthNumber, 0).getDate();
      const startDate = `${month.year}-${String(month.monthNumber).padStart(2, '0')}-01`;
      const endDate = `${month.year}-${String(month.monthNumber).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;
      const analysis = await cashBookApi.transactions.categoryTaxAnalysis(startDate, endDate);

      const categoryBreakdown = [
        ...(analysis.income || []).map((c: any) => ({
          categoryName: c.category_name,
          categoryCode: String(c.category_code),
          amount: Number(c.value_excl_vat) || 0,
          count: c.transaction_count,
          type: 'INCOME' as const,
        })),
        ...(analysis.expense || []).map((c: any) => ({
          categoryName: c.category_name,
          categoryCode: String(c.category_code),
          amount: Number(c.value_excl_vat) || 0,
          count: c.transaction_count,
          type: 'EXPENSE' as const,
        })),
      ];

      setMonthlyData(prev =>
        prev.map(m => (m.monthNumber === month.monthNumber ? { ...m, categoryBreakdown } : m))
      );
      setSelectedMonth({ ...month, categoryBreakdown });
    } catch (err) {
      setError('Failed to load category breakdown');
      console.error(err);
    } finally {
      setCategoryLoading(false);
    }
  };

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Monthly Category Analysis</h1>
          <p className="text-gray-600 mt-2">Year-to-date income and expense analysis by category</p>
        </div>

        {/* Messages */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Year Selector */}
        <div className="mb-6 flex gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Year
            </label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {years.map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium flex items-center gap-2">
            <Download className="w-4 h-4" />
            Export Report
          </button>
        </div>

        {/* YTD Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <BalanceCard
            title="Year-to-Date Income"
            amount={summary.yearToDateIncome}
            variant="income"
          />
          <BalanceCard
            title="Year-to-Date Expenses"
            amount={summary.yearToDateExpense}
            variant="expense"
          />
          <BalanceCard
            title="Year-to-Date Net"
            amount={summary.yearToDateNet}
            variant={summary.yearToDateNet >= 0 ? 'income' : 'expense'}
          />
        </div>

        {/* Monthly Calendar View */}
        {loading ? (
          <div className="text-center py-8">
            <p className="text-gray-500">Loading analysis data...</p>
          </div>
        ) : (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Monthly Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {monthlyData.map((month, idx) => (
                <div
                  key={idx}
                  onClick={() => handleSelectMonth(month)}
                  className={`p-6 rounded-lg border-2 cursor-pointer transition ${getMonthColor(month)}`}
                >
                  <h3 className="text-lg font-bold text-gray-900 mb-1">
                    {month.month} {month.year}
                  </h3>

                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between items-center">
                      <p className="text-sm text-gray-600">Income:</p>
                      <p className="text-sm font-semibold text-green-700">
                        R{month.totalIncome.toFixed(0)}
                      </p>
                    </div>
                    <div className="flex justify-between items-center">
                      <p className="text-sm text-gray-600">Expenses:</p>
                      <p className="text-sm font-semibold text-red-700">
                        R{month.totalExpense.toFixed(0)}
                      </p>
                    </div>
                  </div>

                  <div className="border-t border-gray-200 pt-3">
                    <div className="flex justify-between items-center mb-2">
                      <p className="text-sm font-semibold text-gray-700">Net Position</p>
                      <p className={`text-lg font-bold ${month.netPosition >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                        R{month.netPosition.toFixed(0)}
                      </p>
                    </div>
                    <p className="text-xs text-gray-600">
                      {month.transactionCount} transactions
                    </p>
                  </div>

                  <div className="mt-3 px-2 py-1 rounded text-xs font-medium text-center" style={{
                    backgroundColor: month.netPosition > 0 ? '#dcfce7' : month.netPosition < 0 ? '#fee2e2' : '#f3f4f6',
                    color: month.netPosition > 0 ? '#15803d' : month.netPosition < 0 ? '#b91c1c' : '#374151'
                  }}>
                    {getMonthStatus(month)}
                  </div>
                </div>
              ))}
            </div>

            {/* Category Breakdown Section */}
            {selectedMonth && (
              <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  {selectedMonth.month} {selectedMonth.year} - Category Breakdown
                </h2>

                {categoryLoading ? (
                  <p className="text-gray-500 text-sm">Loading category breakdown...</p>
                ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {/* Income Categories */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Income Categories</h3>
                    <div className="space-y-3">
                      {selectedMonth.categoryBreakdown
                        .filter(c => c.type === 'INCOME')
                        .map((cat, idx) => (
                          <div key={idx} className="p-3 bg-green-50 rounded border border-green-200">
                            <div className="flex items-start justify-between mb-2">
                              <CategoryBadge
                                categoryName={cat.categoryName}
                                categoryCode={cat.categoryCode}
                                type="INCOME"
                              />
                              <p className="font-semibold text-green-900">
                                R{cat.amount.toFixed(2)}
                              </p>
                            </div>
                            <p className="text-xs text-gray-600">{cat.count} transactions</p>
                          </div>
                        ))}
                      {selectedMonth.categoryBreakdown.filter(c => c.type === 'INCOME').length === 0 && (
                        <p className="text-gray-500 text-sm">No income transactions</p>
                      )}
                    </div>
                  </div>

                  {/* Expense Categories */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Expense Categories</h3>
                    <div className="space-y-3">
                      {selectedMonth.categoryBreakdown
                        .filter(c => c.type === 'EXPENSE')
                        .map((cat, idx) => (
                          <div key={idx} className="p-3 bg-red-50 rounded border border-red-200">
                            <div className="flex items-start justify-between mb-2">
                              <CategoryBadge
                                categoryName={cat.categoryName}
                                categoryCode={cat.categoryCode}
                                type="EXPENSE"
                              />
                              <p className="font-semibold text-red-900">
                                R{cat.amount.toFixed(2)}
                              </p>
                            </div>
                            <p className="text-xs text-gray-600">{cat.count} transactions</p>
                          </div>
                        ))}
                      {selectedMonth.categoryBreakdown.filter(c => c.type === 'EXPENSE').length === 0 && (
                        <p className="text-gray-500 text-sm">No expense transactions</p>
                      )}
                    </div>
                  </div>
                </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
