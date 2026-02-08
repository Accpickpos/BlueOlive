'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader, Plus, Edit, Printer } from 'lucide-react';
import Link from 'next/link';

export default function ExpenseInvoicesPage() {
  const [page, setPage] = useState(1);

  const { data: invoices, isLoading } = useQuery({
    queryKey: ['expense-invoices', page],
    queryFn: () =>
      creditorsApi.transactions.list({
        transaction_type: 'INVOICE_EXPENSE',
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
          <h1 className="text-3xl font-bold">Expense Invoices</h1>
          <p className="text-gray-600 mt-1">Record expense invoices from suppliers</p>
        </div>
        <Link href="/dashboard/admin/creditors/transactions/invoices/expense/new">
          <Button className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Invoice
          </Button>
        </Link>
      </div>

      {/* Invoices Table */}
      <Card className="p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Reference</th>
                <th className="px-4 py-3 text-left font-semibold">Supplier</th>
                <th className="px-4 py-3 text-left font-semibold">Invoice #</th>
                <th className="px-4 py-3 text-left font-semibold">Date</th>
                <th className="px-4 py-3 text-left font-semibold">Category</th>
                <th className="px-4 py-3 text-right font-semibold">Amount</th>
                <th className="px-4 py-3 text-left font-semibold">Due Date</th>
                <th className="px-4 py-3 text-center font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices?.results?.map((invoice: any) => (
                <tr key={invoice.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{invoice.reference_number}</td>
                  <td className="px-4 py-3">{invoice.supplier_name}</td>
                  <td className="px-4 py-3 text-gray-600">{invoice.invoice_number}</td>
                  <td className="px-4 py-3 text-sm">
                    {new Date(invoice.transaction_date).toLocaleDateString('en-ZA')}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-600">{invoice.category_name}</td>
                  <td className="px-4 py-3 text-right font-bold">
                    R {invoice.amount?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {invoice.due_date ? new Date(invoice.due_date).toLocaleDateString('en-ZA') : 'N/A'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <Link href={`/dashboard/admin/creditors/transactions/invoices/expense/${invoice.id}`}>
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
            Showing {invoices?.results?.length || 0} of {invoices?.count || 0} invoices
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={!invoices?.previous}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={!invoices?.next}
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
