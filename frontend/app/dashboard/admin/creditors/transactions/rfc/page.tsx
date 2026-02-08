'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader, Plus, Edit, Eye } from 'lucide-react';
import Link from 'next/link';

export default function RFCPage() {
  const [page, setPage] = useState(1);
  const [filterStatus, setFilterStatus] = useState('all');

  const { data: rfcs, isLoading } = useQuery({
    queryKey: ['rfc-transactions', page, filterStatus],
    queryFn: () =>
      creditorsApi.transactions.list({
        transaction_type: 'RFC',
        page,
        page_size: 25,
        status: filterStatus !== 'all' ? filterStatus : undefined,
        ordering: '-transaction_date',
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
          <h1 className="text-3xl font-bold">Returns for Credit (RFC)</h1>
          <p className="text-gray-600 mt-1">Manage supplier returns and credit tracking</p>
        </div>
        <Link href="/dashboard/admin/creditors/transactions/rfc/new">
          <Button className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New RFC
          </Button>
        </Link>
      </div>

      {/* Filter */}
      <Card className="p-4">
        <div className="flex gap-2">
          {['all', 'pending', 'approved', 'credited', 'replaced'].map((status) => (
            <Button
              key={status}
              variant={filterStatus === status ? 'default' : 'outline'}
              className="capitalize"
              onClick={() => {
                setFilterStatus(status);
                setPage(1);
              }}
            >
              {status === 'all' ? 'All RFC' : status}
            </Button>
          ))}
        </div>
      </Card>

      {/* RFC List */}
      <Card className="p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">RFC #</th>
                <th className="px-4 py-3 text-left font-semibold">Supplier</th>
                <th className="px-4 py-3 text-left font-semibold">Date</th>
                <th className="px-4 py-3 text-left font-semibold">Items</th>
                <th className="px-4 py-3 text-right font-semibold">Value</th>
                <th className="px-4 py-3 text-left font-semibold">Status</th>
                <th className="px-4 py-3 text-center font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rfcs?.results?.map((rfc: any) => (
                <tr key={rfc.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{rfc.reference_number}</td>
                  <td className="px-4 py-3">{rfc.supplier_name}</td>
                  <td className="px-4 py-3 text-sm">
                    {new Date(rfc.transaction_date).toLocaleDateString('en-ZA')}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-600">
                    {rfc.item_count || 0} item(s)
                  </td>
                  <td className="px-4 py-3 text-right font-bold">
                    R {rfc.amount?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 text-xs rounded font-medium capitalize ${
                      rfc.status === 'credited' ? 'bg-green-100 text-green-800' :
                      rfc.status === 'replaced' ? 'bg-blue-100 text-blue-800' :
                      rfc.status === 'approved' ? 'bg-amber-100 text-amber-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {rfc.status || 'Pending'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <Link href={`/dashboard/admin/creditors/transactions/rfc/${rfc.id}`}>
                        <Button size="sm" variant="outline" className="w-8 h-8 p-0">
                          <Eye className="w-4 h-4" />
                        </Button>
                      </Link>
                      {rfc.status !== 'credited' && rfc.status !== 'replaced' && (
                        <Link href={`/dashboard/admin/creditors/transactions/rfc/${rfc.id}/edit`}>
                          <Button size="sm" variant="outline" className="w-8 h-8 p-0">
                            <Edit className="w-4 h-4" />
                          </Button>
                        </Link>
                      )}
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
            Showing {rfcs?.results?.length || 0} of {rfcs?.count || 0} RFC items
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={!rfcs?.previous}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={!rfcs?.next}
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
