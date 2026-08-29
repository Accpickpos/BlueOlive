'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Loader, ArrowLeft, Activity } from 'lucide-react';
import Link from 'next/link';
import { Pagination } from '@/components/ui/pagination';

const TRANSACTION_TYPES = [
  'INCOMING', 'RETURN', 'SALE', 'SALE_RETURN', 'ADJUSTMENT', 'STOCK_TAKE',
  'MANUFACTURE', 'BUNDLE_USE', 'BULK_ISSUE', 'LAYBYE_IN', 'LAYBYE_OUT',
  'JOB_IN', 'JOB_OUT', 'RFC_IN', 'RFC_OUT',
];

export default function StockTransactionsReportPage() {
  const [page, setPage] = useState(1);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [transactionType, setTransactionType] = useState('all');
  const [stockItem, setStockItem] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['transactions-report', dateFrom, dateTo, transactionType, stockItem, page],
    queryFn: () => stockControlApi.transactions.list({
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      transaction_type: transactionType === 'all' ? undefined : transactionType,
      stock_item: stockItem || undefined,
      page,
      page_size: 25,
    }),
    staleTime: 30 * 1000,
  });

  const totalPages = data ? Math.ceil(data.count / 25) : 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/stock-control/reports">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Stock Transactions Report</h1>
          <p className="text-gray-600 mt-1">All stock movements, filterable by type/item/date</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Stock Code</label>
            <input
              type="text"
              value={stockItem}
              onChange={(e) => { setStockItem(e.target.value); setPage(1); }}
              placeholder="Filter by stock code..."
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Type</label>
            <Select value={transactionType} onValueChange={(v) => { setTransactionType(v); setPage(1); }}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {TRANSACTION_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>{t}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">From</label>
            <input type="date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(1); }} className="w-full px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">To</label>
            <input type="date" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(1); }} className="w-full px-3 py-2 border rounded-lg" />
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Activity className="w-5 h-5 mr-2" />
          Transactions
        </h2>
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : !data?.results || data.results.length === 0 ? (
          <p className="text-gray-500 text-center py-12">No transactions found</p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Date</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Type</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Stock Code</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Qty In</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Qty Out</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Value</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Comments</th>
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((tx: any) => (
                    <tr key={tx.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4">
                        {tx.transaction_date ? new Date(tx.transaction_date).toLocaleDateString('en-ZA') : '-'}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-800">{tx.transaction_type}</span>
                      </td>
                      <td className="py-3 px-4 font-mono">{tx.stock_item}</td>
                      <td className="py-3 px-4 text-right text-green-600">
                        {Number(tx.quantity_in) > 0 ? `+${Number(tx.quantity_in).toFixed(2)}` : ''}
                      </td>
                      <td className="py-3 px-4 text-right text-red-600">
                        {Number(tx.quantity_out) > 0 ? `-${Number(tx.quantity_out).toFixed(2)}` : ''}
                      </td>
                      <td className="py-3 px-4 text-right">R {Number(tx.value || 0).toFixed(2)}</td>
                      <td className="py-3 px-4 text-gray-600">{tx.comments || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {totalPages > 1 && (
              <div className="mt-4 flex justify-center">
                <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
}
