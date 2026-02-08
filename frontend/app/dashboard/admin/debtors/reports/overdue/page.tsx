'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import type { DebtorAccount } from '@/lib/types/debtors';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Loader, AlertCircle } from 'lucide-react';

export default function OverdueReportPage() {
  const [minOverdue, setMinOverdue] = useState(0);

  const { data: accounts, isLoading } = useQuery({
    queryKey: ['debtors-accounts-list'],
    queryFn: () => debtorsApi.accounts.list({ page_size: 500 }),
    staleTime: 5 * 60 * 1000,
  });

  const overdue = accounts?.results?.filter((a: DebtorAccount) => {
    const total = (a.d120 || 0) + (a.d150 || 0) + (a.d180 || 0);
    return total > minOverdue;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Overdue Accounts Report</h1>
        <p className="text-gray-600 mt-1">Accounts with balances over 120 days old</p>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex gap-4 items-end">
          <div>
            <label className="block text-sm font-medium mb-1">Minimum Amount</label>
            <Input
              type="number"
              value={minOverdue}
              onChange={(e) => setMinOverdue(parseFloat(e.target.value) || 0)}
              placeholder="0.00"
            />
          </div>
          <Button className="bg-blue-600 hover:bg-blue-700">Apply Filter</Button>
        </div>
      </Card>

      {/* Results */}
      {isLoading ? (
        <div className="flex items-center justify-center h-96">
          <Loader className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : overdue.length === 0 ? (
        <Card className="p-8 text-center text-gray-600">No overdue accounts found</Card>
      ) : (
        <Card className="p-6 overflow-x-auto">
          <div className="mb-4 text-sm">
            <p>Found <strong>{overdue.length}</strong> accounts with overdue balances</p>
          </div>
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Account</th>
                <th className="px-4 py-3 text-left font-semibold">Name</th>
                <th className="px-4 py-3 text-right font-semibold">120-150 Days</th>
                <th className="px-4 py-3 text-right font-semibold">150-180 Days</th>
                <th className="px-4 py-3 text-right font-semibold">180+ Days</th>
                <th className="px-4 py-3 text-right font-semibold">Total Overdue</th>
                <th className="px-4 py-3 text-center font-semibold">Days</th>
                <th className="px-4 py-3 text-center font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {overdue
                .sort((a: DebtorAccount, b: DebtorAccount) => (b.d180 || 0) - (a.d180 || 0))
                .map((account: DebtorAccount) => {
                  const total = (account.d120 || 0) + (account.d150 || 0) + (account.d180 || 0);
                  const daysOverdue = account.d180 && account.d180 > 0 ? '180+' : account.d150 && account.d150 > 0 ? '150-180' : '120-150';
                  return (
                    <tr key={account.id} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{account.dno}</td>
                      <td className="px-4 py-3">{account.dname}</td>
                      <td className="px-4 py-3 text-right">${account.d120?.toLocaleString('en-US', { maximumFractionDigits: 0 })}</td>
                      <td className="px-4 py-3 text-right">${account.d150?.toLocaleString('en-US', { maximumFractionDigits: 0 })}</td>
                      <td className="px-4 py-3 text-right font-bold text-red-600">${account.d180?.toLocaleString('en-US', { maximumFractionDigits: 0 })}</td>
                      <td className="px-4 py-3 text-right font-bold">${total.toLocaleString('en-US', { maximumFractionDigits: 0 })}</td>
                      <td className="px-4 py-3 text-center text-sm">{daysOverdue}</td>
                      <td className="px-4 py-3 text-center">
                        <Badge className="bg-red-500">Overdue</Badge>
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </Card>
      )}

      {/* Export Options */}
      <div className="flex gap-2">
        <Button className="bg-blue-600 hover:bg-blue-700">Export to Excel</Button>
        <Button className="bg-green-600 hover:bg-green-700">Export to PDF</Button>
        <Button variant="outline">Email Report</Button>
      </div>
    </div>
  );
}
