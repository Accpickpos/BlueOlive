'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader, Plus, Edit, Printer } from 'lucide-react';
import Link from 'next/link';

export default function ExpenseReturnsPage() {
  const [page, setPage] = useState(1);

  const { data: returns, isLoading } = useQuery({
    queryKey: ['expense-returns', page],
    queryFn: () =>
      creditorsApi.transactions.list({
        transaction_type: 'RETURN_EXPENSE',
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
          <h1 className="text-3xl font-bold">Expense Credit Notes</h1>
          <p className="text-gray-600 mt-1">Record expense/credit note returns from suppliers</p>
        </div>
        <Link href="/dashboard/admin/creditors/transactions/returns/expense/new">
          <Button className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Credit Note
          </Button>
        </Link>
      </div>

      {/* Returns Table */}
      <Card className="p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Reference</th>
                <th className="px-4 py-3 text-left font-semibold">Supplier</th>
                <th className="px-4 py-3 text-left font-semibold">Date</th>
                <th className="px-4 py-3 text-left font-semibold">Category</th>
                <th className="px-4 py-3 text-right font-semibold">Amount</th>
                <th className="px-4 py-3 text-left font-semibold">Status</th>
                <th className="px-4 py-3 text-center font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {returns?.results?.map((ret: any) => (
                <tr key={ret.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{ret.reference_number}</td>
                  <td className="px-4 py-3">{ret.supplier_name}</td>
                  <td className="px-4 py-3 text-sm">
                    {new Date(ret.transaction_date).toLocaleDateString('en-ZA')}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-600">{ret.category_name}</td>
                  <td className="px-4 py-3 text-right font-bold">
                    R {ret.amount?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded font-medium">
                      {ret.status || 'Posted'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <Link href={`/dashboard/admin/creditors/transactions/returns/expense/${ret.id}`}>
                        <Button size="sm" variant="outline" className="w-8 h-8 p-0">
                          <Edit className="w-4 h-4" />
                        </Button>
                      </Link>
                      <Button
                        size="sm"
                        variant="outline"
                        className="w-8 h-8 p-0"
                        onClick={() => window.print()}
                      >
                        <Printer className="w-4 h-4" />
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
            Showing {returns?.results?.length || 0} of {returns?.count || 0} credit notes
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={!returns?.previous}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={!returns?.next}
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
