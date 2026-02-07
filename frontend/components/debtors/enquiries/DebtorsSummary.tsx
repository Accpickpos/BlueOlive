'use client';

import { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';

interface DebtorSummaryData {
  id: number;
  name: string;
  account_number: string;
  current_balance: number;
  age_current: number;
  age_30: number;
  age_60: number;
  age_90: number;
  age_120: number;
  age_150: number;
  age_180: number;
}

type SortBy = 'name' | 'account' | 'balance';
type ViewType = 'weekly' | 'monthly' | 'summary' | 'period' | 'inactive';

export default function DebtorsSummary() {
  const [debtors, setDebtors] = useState<DebtorSummaryData[]>([]);
  const [filteredDebtors, setFilteredDebtors] = useState<DebtorSummaryData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);
  const [sortBy, setSortBy] = useState<SortBy>('name');
  const [areaSalesman, setAreaSalesman] = useState('');
  const [includeZeroBalance, setIncludeZeroBalance] = useState(false);
  const [viewType, setViewType] = useState<ViewType>('weekly');

  useEffect(() => {
    loadDebtors();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [debtors, sortBy, includeZeroBalance, areaSalesman]);

  const loadDebtors = async () => {
    try {
      const response = await apiRequest('/api/debtors/');
      if ((response as any).results) {
        setDebtors((response as any).results);
      } else if (Array.isArray(response)) {
        setDebtors(response);
      }
    } catch (err) {
      setError('Failed to load debtors');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...debtors];

    // Filter by zero balance
    if (!includeZeroBalance) {
      filtered = filtered.filter(d => d.current_balance > 0);
    }

    // Filter by area/salesman (if implemented in backend)
    if (areaSalesman) {
      // This would require additional backend field
      // filtered = filtered.filter(d => d.area_salesman === areaSalesman);
    }

    // Sort
    if (sortBy === 'name') {
      filtered.sort((a, b) => a.name.localeCompare(b.name));
    } else if (sortBy === 'account') {
      filtered.sort((a, b) => a.account_number.localeCompare(b.account_number));
    } else if (sortBy === 'balance') {
      filtered.sort((a, b) => b.current_balance - a.current_balance);
    }

    setFilteredDebtors(filtered);
  };

  const getTotalBalance = () => {
    return filteredDebtors.reduce((sum, d) => sum + d.current_balance, 0);
  };

  const getAgeAnalysisTotals = () => {
    return {
      current: filteredDebtors.reduce((sum, d) => sum + d.age_current, 0),
      age_30: filteredDebtors.reduce((sum, d) => sum + d.age_30, 0),
      age_60: filteredDebtors.reduce((sum, d) => sum + d.age_60, 0),
      age_90: filteredDebtors.reduce((sum, d) => sum + d.age_90, 0),
      age_120: filteredDebtors.reduce((sum, d) => sum + d.age_120, 0),
      age_150: filteredDebtors.reduce((sum, d) => sum + d.age_150, 0),
      age_180: filteredDebtors.reduce((sum, d) => sum + d.age_180, 0),
    };
  };

  const getInactiveDebtors = () => {
    return filteredDebtors.filter(d => d.current_balance === 0);
  };

  if (loading) {
    return <div className="p-6 text-center text-gray-500">Loading debtors data...</div>;
  }

  const totals = getAgeAnalysisTotals();
  const inactiveCount = getInactiveDebtors().length;

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-gray-900">Total Debtors Summary</h2>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Filter Controls */}
      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 space-y-4">
        <h3 className="font-semibold text-gray-900">Report Options</h3>
        
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Report Date</label>
            <input
              type="date"
              value={reportDate}
              onChange={(e) => setReportDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sequence</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortBy)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="name">A - Alphabetically by Name</option>
              <option value="account">N - Numerically by Account #</option>
              <option value="balance">Balance (High to Low)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Area/Salesman</label>
            <input
              type="text"
              value={areaSalesman}
              onChange={(e) => setAreaSalesman(e.target.value)}
              placeholder="Optional"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex items-end">
            <label className="flex items-center gap-2 w-full">
              <input
                type="checkbox"
                checked={includeZeroBalance}
                onChange={(e) => setIncludeZeroBalance(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm text-gray-700">Include Zero Balance</span>
            </label>
          </div>
        </div>
      </div>

      {/* View Type Selector */}
      <div className="flex flex-wrap gap-2 border-b border-gray-200">
        <button
          onClick={() => setViewType('weekly')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            viewType === 'weekly'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Weekly Age Analysis
        </button>
        <button
          onClick={() => setViewType('monthly')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            viewType === 'monthly'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Monthly Age Analysis
        </button>
        <button
          onClick={() => setViewType('summary')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            viewType === 'summary'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Debtor Summary
        </button>
        <button
          onClick={() => setViewType('period')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            viewType === 'period'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Age Period Totals
        </button>
        <button
          onClick={() => setViewType('inactive')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            viewType === 'inactive'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Inactive Debtors ({inactiveCount})
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-3 rounded-lg border border-blue-200">
          <p className="text-xs text-blue-700 font-medium">Total Debtors</p>
          <p className="text-2xl font-bold text-blue-900">{filteredDebtors.length}</p>
        </div>
        <div className="bg-gradient-to-br from-red-50 to-red-100 p-3 rounded-lg border border-red-200">
          <p className="text-xs text-red-700 font-medium">Total Due</p>
          <p className="text-2xl font-bold text-red-900">R{getTotalBalance().toFixed(2)}</p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 p-3 rounded-lg border border-green-200">
          <p className="text-xs text-green-700 font-medium">Current</p>
          <p className="text-2xl font-bold text-green-900">R{totals.current.toFixed(2)}</p>
        </div>
        <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 p-3 rounded-lg border border-yellow-200">
          <p className="text-xs text-yellow-700 font-medium">30-60 Days</p>
          <p className="text-2xl font-bold text-yellow-900">R{(totals.age_30 + totals.age_60).toFixed(2)}</p>
        </div>
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-3 rounded-lg border border-orange-200">
          <p className="text-xs text-orange-700 font-medium">90+ Days</p>
          <p className="text-2xl font-bold text-orange-900">R{(totals.age_90 + totals.age_120 + totals.age_150 + totals.age_180).toFixed(2)}</p>
        </div>
      </div>

      {/* View Content */}
      {viewType === 'weekly' && (
        <WeeklyAgeAnalysis debtors={filteredDebtors} reportDate={reportDate} />
      )}

      {viewType === 'monthly' && (
        <MonthlyAgeAnalysis debtors={filteredDebtors} reportDate={reportDate} />
      )}

      {viewType === 'summary' && (
        <DebtorSummaryView debtors={filteredDebtors} />
      )}

      {viewType === 'period' && (
        <AgePeriodTotals totals={totals} totalDebtors={filteredDebtors.length} />
      )}

      {viewType === 'inactive' && (
        <InactiveDebtors debtors={getInactiveDebtors()} />
      )}

      {/* Footer Actions */}
      <div className="flex gap-3 justify-between pt-4 border-t border-gray-200">
        <button
          onClick={() => window.print()}
          className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium"
        >
          Print Report
        </button>
      </div>
    </div>
  );
}

// Weekly Age Analysis Component
function WeeklyAgeAnalysis({ debtors, reportDate }: { debtors: DebtorSummaryData[]; reportDate: string }) {
  const reportDateObj = new Date(reportDate);
  const weekNumber = Math.ceil((reportDateObj.getDate() - reportDateObj.getDay()) / 7);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">
        Weekly Age Analysis - Week {weekNumber} of {reportDate}
      </h3>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Account</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Debtor</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Current</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">1-2 Weeks</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Total</th>
              </tr>
            </thead>
            <tbody>
              {debtors.map(debtor => (
                <tr key={debtor.id} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{debtor.account_number}</td>
                  <td className="px-4 py-3 text-gray-700">{debtor.name}</td>
                  <td className="px-4 py-3 text-right text-gray-900">R{debtor.age_current.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right text-gray-900">R{(debtor.age_30 * 0.5).toFixed(2)}</td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-900">R{debtor.current_balance.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Monthly Age Analysis Component
function MonthlyAgeAnalysis({ debtors, reportDate }: { debtors: DebtorSummaryData[]; reportDate: string }) {
  const reportMonth = new Date(reportDate).toLocaleString('default', { month: 'long', year: 'numeric' });

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Monthly Age Analysis - {reportMonth}</h3>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Account</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Debtor</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Current</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">30 Days</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">60 Days</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">90+ Days</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Total</th>
              </tr>
            </thead>
            <tbody>
              {debtors.map(debtor => (
                <tr key={debtor.id} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{debtor.account_number}</td>
                  <td className="px-4 py-3 text-gray-700">{debtor.name}</td>
                  <td className="px-4 py-3 text-right text-gray-900">R{debtor.age_current.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right text-gray-900">R{debtor.age_30.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right text-gray-900">R{debtor.age_60.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right text-gray-900">
                    R{(debtor.age_90 + debtor.age_120 + debtor.age_150 + debtor.age_180).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-900">R{debtor.current_balance.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Debtor Summary View Component
function DebtorSummaryView({ debtors }: { debtors: DebtorSummaryData[] }) {
  const [sortView, setSortView] = useState<'account' | 'name' | 'balance'>('name');

  const sortedDebtors = [...debtors].sort((a, b) => {
    if (sortView === 'account') return a.account_number.localeCompare(b.account_number);
    if (sortView === 'name') return a.name.localeCompare(b.name);
    if (sortView === 'balance') return b.current_balance - a.current_balance;
    return 0;
  });

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button
          onClick={() => setSortView('account')}
          className={`px-3 py-2 rounded text-sm font-medium ${
            sortView === 'account'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          By Account #
        </button>
        <button
          onClick={() => setSortView('name')}
          className={`px-3 py-2 rounded text-sm font-medium ${
            sortView === 'name'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          By Name
        </button>
        <button
          onClick={() => setSortView('balance')}
          className={`px-3 py-2 rounded text-sm font-medium ${
            sortView === 'balance'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          By Total Due
        </button>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Account #</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Debtor Name</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Total Due</th>
              </tr>
            </thead>
            <tbody>
              {sortedDebtors.map(debtor => (
                <tr key={debtor.id} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{debtor.account_number}</td>
                  <td className="px-4 py-3 text-gray-700">{debtor.name}</td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-900">R{debtor.current_balance.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Age Period Totals Component
function AgePeriodTotals({
  totals,
  totalDebtors,
}: {
  totals: Record<string, number>;
  totalDebtors: number;
}) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Total Due by Ageing Period</h3>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Current', key: 'current', color: 'green' },
          { label: '30 Days', key: 'age_30', color: 'yellow' },
          { label: '60 Days', key: 'age_60', color: 'orange' },
          { label: '90+ Days', key: 'age_90', color: 'red' },
        ].map(period => (
          <div
            key={period.key}
            className={`bg-gradient-to-br from-${period.color}-50 to-${period.color}-100 p-4 rounded-lg border border-${period.color}-200`}
          >
            <p className={`text-xs text-${period.color}-700 font-medium`}>{period.label}</p>
            <p className={`text-2xl font-bold text-${period.color}-900`}>
              R{totals[period.key]?.toFixed(2) || '0.00'}
            </p>
          </div>
        ))}
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="space-y-3">
          <div className="flex justify-between border-b border-gray-200 pb-2">
            <span className="text-gray-700">Total Debtors:</span>
            <span className="font-semibold text-gray-900">{totalDebtors}</span>
          </div>
          <div className="flex justify-between border-b border-gray-200 pb-2">
            <span className="text-gray-700">Total Amount Due:</span>
            <span className="text-lg font-bold text-gray-900">
              R{Object.values(totals).reduce((a, b) => a + b, 0).toFixed(2)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// Inactive Debtors Component
function InactiveDebtors({ debtors }: { debtors: DebtorSummaryData[] }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Inactive Debtors (Zero Balance)</h3>

      {debtors.length > 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-100 border-b border-gray-200">
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Account #</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Debtor Name</th>
                  <th className="px-4 py-3 text-center font-semibold text-gray-700">Status</th>
                </tr>
              </thead>
              <tbody>
                {debtors.map(debtor => (
                  <tr key={debtor.id} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{debtor.account_number}</td>
                    <td className="px-4 py-3 text-gray-700">{debtor.name}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">
                        Inactive
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="p-6 bg-gray-50 border border-gray-200 rounded-lg text-center text-gray-600">
          No inactive debtors found
        </div>
      )}
    </div>
  );
}
