'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import type { CreditorAccount } from '@/lib/types/creditors';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader, Plus, Edit, Trash2, Printer } from 'lucide-react';
import Link from 'next/link';

export default function StockReceiptsPage() {
  const queryClient = useQueryClient();
  const [selectedSupplier, setSelectedSupplier] = useState<CreditorAccount | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);

  const { data: suppliers } = useQuery({
    queryKey: ['creditors-suppliers', searchTerm],
    queryFn: () =>
      creditorsApi.accounts.list({
        search: searchTerm || undefined,
        page_size: 50,
      }),
  });

  const { data: grns, isLoading } = useQuery({
    queryKey: ['stock-receipts-grn', page],
    queryFn: () =>
      creditorsApi.transactions.list({
        transaction_type: 'GRN',
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
          <h1 className="text-3xl font-bold">Stock Receipts (GRN)</h1>
          <p className="text-gray-600 mt-1">Record goods received from suppliers</p>
        </div>
        <Link href="/dashboard/admin/creditors/transactions/stock-receipts/new">
          <Button className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Receipt
          </Button>
        </Link>
      </div>

      {/* Supplier Selection */}
      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">Filter by Supplier</h2>
        <Input
          type="text"
          placeholder="Search supplier by account number or name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        {searchTerm && suppliers?.results && (
          <div className="mt-3 max-h-48 overflow-y-auto border rounded">
            {suppliers.results.map((supplier: CreditorAccount) => (
              <div
                key={supplier.id}
                className="p-2 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                onClick={() => {
                  setSelectedSupplier(supplier);
                  setSearchTerm('');
                }}
              >
                <p className="font-medium">{supplier.account_number} - {supplier.name}</p>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* GRN List */}
      <Card className="p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">GRN #</th>
                <th className="px-4 py-3 text-left font-semibold">Supplier</th>
                <th className="px-4 py-3 text-left font-semibold">Invoice</th>
                <th className="px-4 py-3 text-left font-semibold">Date</th>
                <th className="px-4 py-3 text-right font-semibold">Amount</th>
                <th className="px-4 py-3 text-left font-semibold">Status</th>
                <th className="px-4 py-3 text-center font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {grns?.results?.map((grn: any) => (
                <tr key={grn.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{grn.reference_number}</td>
                  <td className="px-4 py-3">{grn.supplier_name}</td>
                  <td className="px-4 py-3 text-gray-600">{grn.invoice_number}</td>
                  <td className="px-4 py-3 text-sm">
                    {new Date(grn.transaction_date).toLocaleDateString('en-ZA')}
                  </td>
                  <td className="px-4 py-3 text-right font-bold">
                    R {grn.total_amount?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded font-medium">
                      {grn.status || 'Posted'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <Link href={`/dashboard/admin/creditors/transactions/stock-receipts/${grn.id}`}>
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
            Showing {grns?.results?.length || 0} of {grns?.count || 0} receipts
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={!grns?.previous}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={!grns?.next}
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
