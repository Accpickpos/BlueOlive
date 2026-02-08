'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import type { CreditorAccount } from '@/lib/types/creditors';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader } from 'lucide-react';

export default function AgeAnalysisPage() {
  const [dateRange, setDateRange] = useState({
    from: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
    to: new Date().toISOString().split('T')[0],
  });

  const { data: summary, isLoading } = useQuery({
    queryKey: ['creditors-age-analysis', dateRange],
    queryFn: () => creditorsApi.summary.get({ cutoff_date: dateRange.to }),
    staleTime: 5 * 60 * 1000,
  });

  const { data: accounts } = useQuery({
    queryKey: ['creditors-all-accounts-age'],
    queryFn: () => creditorsApi.accounts.list({ page_size: 500 }),
  });

  const sortedByAge = accounts?.results
    ?.sort((a: CreditorAccount, b: CreditorAccount) => (b.d120 || 0) - (a.d120 || 0))
    .slice(0, 20) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Age Analysis Report</h1>
        <p className="text-gray-600 mt-1">Aging breakdown of all payables to suppliers</p>
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
          {/* Summary Cards */}
          <Card className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Creditors</p>
              <p className="text-2xl font-bold">{summary.total_creditors}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Payable</p>
              <p className="text-2xl font-bold text-red-600">
                R {summary.total_payable?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-600 uppercase">Avg DPO</p>
              <p className="text-2xl font-bold text-orange-600">{summary.average_dpo?.toFixed(1)} days</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 uppercase">Critical (120+)</p>
              <p className="text-2xl font-bold text-red-600">
                R {summary.critical_aging?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </p>
            </div>
          </Card>

          {/* Aging Breakdown */}
          <Card className="p-6">
            <h2 className="text-lg font-bold mb-4">Aging Breakdown</h2>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div className="p-4 bg-green-50 rounded border border-green-200">
                <p className="text-xs text-green-600 font-medium">Current</p>
                <p className="text-2xl font-bold text-green-700">
                  R {summary.current_aging?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
                </p>
                <p className="text-xs text-green-600 mt-1">
                  {((summary.current_aging || 0) / (summary.total_payable || 1) * 100).toFixed(1)}%
                </p>
              </div>
              <div className="p-4 bg-amber-50 rounded border border-amber-200">
                <p className="text-xs text-amber-600 font-medium">30-60 Days</p>
                <p className="text-2xl font-bold text-amber-700">
                  R {((summary.d30 || 0) + (summary.d60 || 0))?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
                </p>
                <p className="text-xs text-amber-600 mt-1">
                  {(((summary.d30 || 0) + (summary.d60 || 0)) / (summary.total_payable || 1) * 100).toFixed(1)}%
                </p>
              </div>
              <div className="p-4 bg-orange-50 rounded border border-orange-200">
                <p className="text-xs text-orange-600 font-medium">60-90 Days</p>
                <p className="text-2xl font-bold text-orange-700">
                  R {(summary.d60 || 0)?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
                </p>
                <p className="text-xs text-orange-600 mt-1">
                  {((summary.d60 || 0) / (summary.total_payable || 1) * 100).toFixed(1)}%
                </p>
              </div>
              <div className="p-4 bg-red-50 rounded border border-red-200">
                <p className="text-xs text-red-600 font-medium">90-120 Days</p>
                <p className="text-2xl font-bold text-red-700">
                  R {(summary.d90 || 0)?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
                </p>
                <p className="text-xs text-red-600 mt-1">
                  {((summary.d90 || 0) / (summary.total_payable || 1) * 100).toFixed(1)}%
                </p>
              </div>
              <div className="p-4 bg-red-100 rounded border border-red-300">
                <p className="text-xs text-red-900 font-medium">120+ Days</p>
                <p className="text-2xl font-bold text-red-900">
                  R {summary.critical_aging?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
                </p>
                <p className="text-xs text-red-900 mt-1">
                  {((summary.critical_aging || 0) / (summary.total_payable || 1) * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </Card>

          {/* Top Accounts with Overdue */}
          {sortedByAge.length > 0 && (
            <Card className="p-6">
              <h2 className="text-lg font-bold mb-4">Top Suppliers with 120+ Days Overdue</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold">Account</th>
                      <th className="px-4 py-3 text-left font-semibold">Name</th>
                      <th className="px-4 py-3 text-right font-semibold">120+ Days</th>
                      <th className="px-4 py-3 text-right font-semibold">90-120 Days</th>
                      <th className="px-4 py-3 text-right font-semibold">Total Overdue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedByAge.map((account: CreditorAccount) => {
                      const overdue = (account.d90 || 0) + (account.d120 || 0);
                      return (
                        <tr key={account.id} className="border-b">
                          <td className="px-4 py-3 font-medium">{account.account_number}</td>
                          <td className="px-4 py-3">{account.name}</td>
                          <td className="px-4 py-3 text-right font-bold text-red-600">
                            R {account.d120?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
                          </td>
                          <td className="px-4 py-3 text-right">R {account.d90?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                          <td className="px-4 py-3 text-right font-bold text-red-700">
                            R {overdue.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
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
