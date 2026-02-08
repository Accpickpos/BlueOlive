'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader, Plus, Edit } from 'lucide-react';
import Link from 'next/link';

export default function JournalEntriesPage() {
  const [page, setPage] = useState(1);

  const { data: journals, isLoading } = useQuery({
    queryKey: ['journal-entries', page],
    queryFn: () =>
      creditorsApi.transactions.list({
        transaction_type: 'JOURNAL',
        page,
        page_size: 25,
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
          <h1 className="text-3xl font-bold">Journal Entries</h1>
          <p className="text-gray-600 mt-1">Record adjustments and corrections to creditor accounts</p>
        </div>
        <Link href="/dashboard/admin/creditors/transactions/journals/new">
          <Button className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Entry
          </Button>
        </Link>
      </div>

      {/* Journal Entries Table */}
      <Card className="p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Reference</th>
                <th className="px-4 py-3 text-left font-semibold">Account</th>
                <th className="px-4 py-3 text-left font-semibold">Date</th>
                <th className="px-4 py-3 text-left font-semibold">Description</th>
                <th className="px-4 py-3 text-right font-semibold">Amount</th>
                <th className="px-4 py-3 text-left font-semibold">Type</th>
                <th className="px-4 py-3 text-center font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {journals?.results?.map((entry: any) => (
                <tr key={entry.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{entry.reference_number}</td>
                  <td className="px-4 py-3">{entry.supplier_name}</td>
                  <td className="px-4 py-3 text-sm">
                    {new Date(entry.transaction_date).toLocaleDateString('en-ZA')}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-600">{entry.description}</td>
                  <td className="px-4 py-3 text-right font-bold">
                    R {entry.amount?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 text-xs rounded font-medium ${
                      entry.entry_type === 'DEBIT' 
                        ? 'bg-red-100 text-red-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {entry.entry_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <Link href={`/dashboard/admin/creditors/transactions/journals/${entry.id}`}>
                        <Button size="sm" variant="outline" className="w-8 h-8 p-0">
                          <Edit className="w-4 h-4" />
                        </Button>
                      </Link>
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
            Showing {journals?.results?.length || 0} of {journals?.count || 0} entries
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={!journals?.previous}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={!journals?.next}
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
