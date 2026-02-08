'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import type { CreditorAccount } from '@/lib/types/creditors';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader, Plus, Edit, Trash2, Search } from 'lucide-react';
import Link from 'next/link';

export default function CreditorAccountsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);

  const { data: accounts, isLoading } = useQuery({
    queryKey: ['creditor-accounts', searchTerm, page],
    queryFn: () =>
      creditorsApi.accounts.list({
        page,
        page_size: 25,
        search: searchTerm || undefined,
      }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Creditor Accounts</h1>
          <p className="text-gray-600 mt-1">Add, edit, and manage supplier accounts</p>
        </div>
        <Link href="/dashboard/admin/creditors/maintenance/accounts/new">
          <Button className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Account
          </Button>
        </Link>
      </div>

      {/* Search Bar */}
      <Card className="p-4">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search by account number, name, or contact person..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="pl-10"
            />
          </div>
          <Button variant="outline">Search</Button>
        </div>
      </Card>

      {/* Accounts Table */}
      <Card className="p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Account #</th>
                <th className="px-4 py-3 text-left font-semibold">Name</th>
                <th className="px-4 py-3 text-left font-semibold">Type</th>
                <th className="px-4 py-3 text-left font-semibold">Contact</th>
                <th className="px-4 py-3 text-right font-semibold">Balance</th>
                <th className="px-4 py-3 text-left font-semibold">Last Payment</th>
                <th className="px-4 py-3 text-center font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {accounts?.results?.map((account: CreditorAccount) => (
                <tr key={account.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{account.account_number}</td>
                  <td className="px-4 py-3">{account.name}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        account.account_type === 'BBF'
                          ? 'bg-purple-100 text-purple-800'
                          : 'bg-violet-100 text-violet-800'
                      }`}
                    >
                      {account.account_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-600">{account.contact_person}</td>
                  <td className="px-4 py-3 text-right font-bold">
                    R {account.balance?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-600">
                    {account.last_payment_date
                      ? new Date(account.last_payment_date).toLocaleDateString('en-ZA')
                      : 'N/A'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <Link href={`/dashboard/admin/creditors/maintenance/accounts/${account.id}`}>
                        <Button size="sm" variant="outline" className="w-8 h-8 p-0">
                          <Edit className="w-4 h-4" />
                        </Button>
                      </Link>
                      <Button
                        size="sm"
                        variant="destructive"
                        className="w-8 h-8 p-0"
                        onClick={() => {
                          // TODO: Implement delete handler
                          console.log('Delete:', account.id);
                        }}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t">
          <p className="text-sm text-gray-600">
            Showing {accounts?.results?.length || 0} of {accounts?.count || 0} accounts
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={!accounts?.previous}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={!accounts?.next}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
