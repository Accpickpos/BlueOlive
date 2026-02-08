'use client';

import { useQuery } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Card } from '@/components/ui/card';
import { Loader, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';

export default function TopAccountsPage() {
  const { data: accounts, isLoading, error } = useQuery({
    queryKey: ['debtors-accounts-list'],
    queryFn: () => debtorsApi.accounts.list({ page_size: 100 }),
    staleTime: 5 * 60 * 1000,
  });

  const sorted = accounts?.results?.sort((a, b) => (b.total_balance || 0) - (a.total_balance || 0)) || [];
  const topAccounts = sorted.slice(0, 20);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Top Debtor Accounts</h1>
        <p className="text-gray-600 mt-1">Accounts ranked by outstanding balance</p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-800">Failed to load accounts</div>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center h-96">
          <Loader className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : topAccounts.length === 0 ? (
        <Card className="p-8 text-center text-gray-600">No accounts found</Card>
      ) : (
        <Card className="p-6 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Rank</th>
                <th className="px-4 py-3 text-left font-semibold">Account</th>
                <th className="px-4 py-3 text-left font-semibold">Name</th>
                <th className="px-4 py-3 text-left font-semibold">Area</th>
                <th className="px-4 py-3 text-right font-semibold">Balance</th>
                <th className="px-4 py-3 text-right font-semibold">Credit Limit</th>
                <th className="px-4 py-3 text-right font-semibold">% Used</th>
                <th className="px-4 py-3 text-center font-semibold">Current</th>
                <th className="px-4 py-3 text-center font-semibold">120+ Days</th>
                <th className="px-4 py-3 text-center font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {topAccounts.map((account, idx) => {
                const percentUsed = account.dclimit ? (account.total_balance! / account.dclimit) * 100 : 0;
                const utilColor = percentUsed > 80 ? 'text-red-600' : percentUsed > 60 ? 'text-orange-600' : 'text-green-600';

                return (
                  <tr key={account.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3 font-bold text-center text-lg">{idx + 1}</td>
                    <td className="px-4 py-3 font-medium">{account.dno}</td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/dashboard/admin/debtors/enquiries/account?id=${account.id}`}
                        className="text-blue-600 hover:underline"
                      >
                        {account.dname}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{account.darea_name || '-'}</td>
                    <td className="px-4 py-3 text-right font-bold text-blue-600">
                      ${account.total_balance?.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                    </td>
                    <td className="px-4 py-3 text-right">${account.dclimit?.toLocaleString()}</td>
                    <td className={`px-4 py-3 text-right font-semibold ${utilColor}`}>
                      {percentUsed.toFixed(0)}%
                    </td>
                    <td className="px-4 py-3 text-center text-sm">
                      ${account.dcrnt?.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                    </td>
                    <td className={`px-4 py-3 text-center font-bold ${account.d180! > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      ${account.d180?.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {account.blockflag ? (
                        <Badge className="bg-red-500">Blocked</Badge>
                      ) : account.is_active ? (
                        <Badge className="bg-green-500">Active</Badge>
                      ) : (
                        <Badge className="bg-gray-500">Inactive</Badge>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
