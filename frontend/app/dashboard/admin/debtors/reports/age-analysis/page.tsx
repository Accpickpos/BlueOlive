'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import type { DebtorAccount } from '@/lib/types/debtors';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader } from 'lucide-react';
import AgingChart from '@/components/debtors/enquiries/AgingChart';

export default function AgeAnalysisReportPage() {
  const [dateRange, setDateRange] = useState({
    from: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
    to: new Date().toISOString().split('T')[0],
  });

  const { data: summary, isLoading } = useQuery({
    queryKey: ['age-analysis-report', dateRange],
    queryFn: () => debtorsApi.summary.get(dateRange.to),
    staleTime: 5 * 60 * 1000,
  });

  const { data: accounts } = useQuery({
    queryKey: ['debtors-all-accounts'],
    queryFn: () => debtorsApi.accounts.list({ page_size: 500 }),
  });

  const sortedByAge = accounts?.results
    ?.sort((a: DebtorAccount, b: DebtorAccount) => (b.d180 || 0) - (a.d180 || 0))
    .slice(0, 20) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Age Analysis Report</h1>
        <p className="text-gray-600 mt-1">Aging breakdown of all receivables</p>
      </div>

      {/* Date Filter */}
      <Card className="p-4">
        <div className="flex gap-4 items-end">
          <div>
            <label className="block text-sm font-medium mb-1">Cutoff Date</label>
            <Input
              type="date"
              value={dateRange.to}
              onChange={(e) => setDateRange({ ...dateRange, to: e.target.value })}
            />
          </div>
          <Button className="bg-blue-600 hover:bg-blue-700">Generate</Button>
        </div>
      </Card>

      {isLoading ? (
        <div className="flex items-center justify-center h-96">
          <Loader className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : summary ? (
        <div className="space-y-6">
          {/* Chart */}
          <AgingChart summary={summary} />

          {/* Summary Box */}
          <Card className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Debtors</p>
              <p className="text-2xl font-bold">{summary.total_debtors}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Balance</p>
              <p className="text-2xl font-bold text-blue-600">
                ${summary.total_receivable?.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-600 uppercase">Avg DSO</p>
              <p className="text-2xl font-bold text-orange-600">{summary.average_dso?.toFixed(1)} days</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 uppercase">Critical (120+)</p>
              <p className="text-2xl font-bold text-red-600">
                ${summary.critical_aging?.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </p>
            </div>
          </Card>

          {/* Accounts with Overdue */}
          {sortedByAge.length > 0 && (
            <Card className="p-6">
              <h2 className="text-lg font-bold mb-4">Top Accounts with 120+ Days Overdue</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold">Account</th>
                      <th className="px-4 py-3 text-left font-semibold">Name</th>
                      <th className="px-4 py-3 text-right font-semibold">180+ Days</th>
                      <th className="px-4 py-3 text-right font-semibold">150-180 Days</th>
                      <th className="px-4 py-3 text-right font-semibold">Total Overdue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedByAge.map((account: DebtorAccount) => {
                      const overdue = (account.d120 || 0) + (account.d150 || 0) + (account.d180 || 0);
                      return (
                        <tr key={account.id} className="border-b">
                          <td className="px-4 py-3 font-medium">{account.dno}</td>
                          <td className="px-4 py-3">{account.dname}</td>
                          <td className="px-4 py-3 text-right font-bold text-red-600">
                            ${account.d180?.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                          </td>
                          <td className="px-4 py-3 text-right">${account.d150?.toLocaleString('en-US', { maximumFractionDigits: 0 })}</td>
                          <td className="px-4 py-3 text-right font-bold text-red-700">
                            ${overdue.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Export Options */}
          <div className="flex gap-2">
            <Button className="bg-blue-600 hover:bg-blue-700">Export to Excel</Button>
            <Button className="bg-green-600 hover:bg-green-700">Export to PDF</Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
