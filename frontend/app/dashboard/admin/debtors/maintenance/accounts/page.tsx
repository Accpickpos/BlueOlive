'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, Search, AlertCircle, Edit2, Trash2, Eye } from 'lucide-react';
import type { DebtorAccount } from '@/lib/types/debtors';

export default function AccountsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    blocked: false as boolean | undefined,
    is_active: true,
  });
  const [page, setPage] = useState(1);

  const { data: response, isLoading, error } = useQuery({
    queryKey: ['debtors-accounts', searchTerm, filters, page],
    queryFn: () =>
      debtorsApi.accounts.list({
        search: searchTerm || undefined,
        is_active: filters.is_active,
        blocked: filters.blocked,
        page,
        page_size: 20,
      }),
    staleTime: 2 * 60 * 1000,
  });

  const accounts = response?.results || [];
  const total = response?.count || 0;
  const totalPages = Math.ceil(total / 20);

  const handleDelete = async (id: number, name: string) => {
    if (window.confirm(`Delete ${name}?`)) {
      try {
        await debtorsApi.accounts.delete(id);
        // Refetch would happen via react-query invalidation
      } catch (err) {
        console.error('Delete failed:', err);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Debtor Accounts</h1>
          <p className="text-gray-600 mt-1">Manage customer accounts and credit settings</p>
        </div>
        <Link href="/dashboard/admin/debtors/maintenance/new">
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Plus className="w-4 h-4 mr-2" />
            New Account
          </Button>
        </Link>
      </div>

      {/* Search & Filters */}
      <Card className="p-4">
        <div className="space-y-4">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="Search by name, number, or email..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setPage(1);
                }}
                className="flex-1 pl-10"
              />
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant={!filters.blocked ? 'default' : 'outline'}
              onClick={() => {
                setFilters({ ...filters, blocked: false });
                setPage(1);
              }}
            >
              Active
            </Button>
            <Button
              variant={filters.blocked ? 'default' : 'outline'}
              onClick={() => {
                setFilters({ ...filters, blocked: true });
                setPage(1);
              }}
            >
              Blocked
            </Button>
            {(searchTerm || filters.blocked) && (
              <Button
                variant="outline"
                onClick={() => {
                  setSearchTerm('');
                  setFilters({ blocked: false, is_active: true });
                  setPage(1);
                }}
              >
                Clear Filters
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Table */}
      <Card className="p-4 overflow-x-auto">
        {isLoading ? (
          <div className="py-8 text-center text-gray-600">Loading accounts...</div>
        ) : error ? (
          <div className="py-8 px-4 bg-red-50 border border-red-200 rounded-lg flex gap-2">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-red-800">Failed to load accounts</div>
          </div>
        ) : accounts.length === 0 ? (
          <div className="py-8 text-center text-gray-600">No accounts found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Account #</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Name</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Contact</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Sales Area</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Balance</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Credit Limit</th>
                  <th className="px-4 py-3 text-center font-semibold text-gray-700">Status</th>
                  <th className="px-4 py-3 text-center font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((account: DebtorAccount) => (
                  <tr key={account.id} className="border-b hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium">{account.dno}</td>
                    <td className="px-4 py-3">{account.dname}</td>
                    <td className="px-4 py-3 text-gray-600">{account.dcontact || '-'}</td>
                    <td className="px-4 py-3 text-gray-600">{account.darea_name || '-'}</td>
                    <td className="px-4 py-3 text-right font-semibold text-blue-600">
                      ${account.total_balance?.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-right">${account.dclimit?.toLocaleString()}</td>
                    <td className="px-4 py-3 text-center">
                      {account.blockflag ? (
                        <Badge className="bg-red-500">Blocked</Badge>
                      ) : account.is_active ? (
                        <Badge className="bg-green-500">Active</Badge>
                      ) : (
                        <Badge className="bg-gray-500">Inactive</Badge>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex justify-center gap-2">
                        <Link href={`/dashboard/admin/debtors/maintenance/${account.id}`}>
                          <Button variant="outline" size="sm">
                            <Edit2 className="w-4 h-4" />
                          </Button>
                        </Link>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(account.id!, account.dname)}
                        >
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
            <Button
              key={p}
              variant={page === p ? 'default' : 'outline'}
              onClick={() => setPage(p)}
            >
              {p}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
