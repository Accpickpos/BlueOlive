'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader, Search } from 'lucide-react';

export default function TransactionScrollPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    transaction_type: '',
    date_from: '',
    date_to: new Date().toISOString().split('T')[0],
  });
  const [page, setPage] = useState(1);

  const { data: transactions, isLoading } = useQuery({
    queryKey: ['creditors-transaction-scroll', searchTerm, filters, page],
    queryFn: () =>
      creditorsApi.transactions.list({
        search: searchTerm || undefined,
        transaction_type: filters.transaction_type || undefined,
        start_date: filters.date_from || undefined,
        end_date: filters.date_to || undefined,
        page,
        page_size: 50,
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

  const totalAmount = transactions?.results?.reduce((sum: number, txn: any) => sum + (txn.amount || 0), 0) || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Transaction Scroll</h1>
        <p className="text-gray-600 mt-1">View all creditor transactions in chronological order</p>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <h2 className="font-bold mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Account, reference..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setPage(1);
                }}
                className="pl-10"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Transaction Type</label>
            <select
              value={filters.transaction_type}
              onChange={(e) => {
                setFilters({ ...filters, transaction_type: e.target.value });
                setPage(1);
              }}
              className="w-full border border-gray-300 rounded px-3 py-2"
            >
              <option value="">All Types</option>
              <option value="GRN">Stock Receipt</option>
              <option value="INVOICE_EXPENSE">Invoice</option>
              <option value="PAYMENT">Payment</option>
              <option value="RETURN_STOCK">Stock Return</option>
              <option value="RETURN_EXPENSE">Credit Note</option>
              <option value="JOURNAL">Journal</option>
              <option value="RFC">RFC</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">From Date</label>
            <Input
              type="date"
              value={filters.date_from}
              onChange={(e) => {
                setFilters({ ...filters, date_from: e.target.value });
                setPage(1);
              }}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">To Date</label>
            <Input
              type="date"
              value={filters.date_to}
              onChange={(e) => {
                setFilters({ ...filters, date_to: e.target.value });
                setPage(1);
              }}
            />
          </div>
        </div>
      </Card>

      {/* Totals Summary */}
      <Card className="p-6 bg-blue-50">
        <p className="text-sm text-gray-600 mb-1">Total Amount ({transactions?.results?.length || 0} transactions)</p>
        <p className="text-3xl font-bold text-blue-700">
          R {totalAmount.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
        </p>
      </Card>

      {/* Transactions Table */}
      <Card className="p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Date</th>
                <th className="px-4 py-3 text-left font-semibold">Reference</th>
                <th className="px-4 py-3 text-left font-semibold">Supplier</th>
                <th className="px-4 py-3 text-left font-semibold">Type</th>
                <th className="px-4 py-3 text-left font-semibold">Description</th>
                <th className="px-4 py-3 text-right font-semibold">Amount</th>
              </tr>
            </thead>
            <tbody>
              {transactions?.results?.map((txn: any) => (
                <tr key={txn.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">
                    {new Date(txn.transaction_date).toLocaleDateString('en-ZA')}
                  </td>
                  <td className="px-4 py-3">{txn.reference_number}</td>
                  <td className="px-4 py-3 text-sm">{txn.supplier_name}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded font-medium">
                      {txn.transaction_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-600">{txn.description}</td>
                  <td className="px-4 py-3 text-right font-bold">
                    R {txn.amount?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {(!transactions?.results || transactions.results.length === 0) && (
          <div className="text-center py-8 text-gray-500">No transactions found.</div>
        )}

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t">
          <p className="text-sm text-gray-600">
            Showing {transactions?.results?.length || 0} of {transactions?.count || 0} transactions
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={!transactions?.previous}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={!transactions?.next}
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
