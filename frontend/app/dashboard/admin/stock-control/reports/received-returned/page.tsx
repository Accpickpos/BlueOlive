'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader, ArrowLeft, ArrowDown, ArrowUp } from 'lucide-react';
import Link from 'next/link';
import { Pagination } from '@/components/ui/pagination';

export default function ReceivedReturnedReportPage() {
  const [page, setPage] = useState(1);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [stockItem, setStockItem] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['received-returned-report', dateFrom, dateTo, stockItem, page],
    queryFn: () => stockControlApi.enquiries.receivedReturnedReport({
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
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
          <h1 className="text-3xl font-bold">Stock Received / Returned Report</h1>
          <p className="text-gray-600 mt-1">Incoming stock and supplier returns together</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Stock Code</label>
            <input
              type="text"
              value={stockItem}
              onChange={(e) => { setStockItem(e.target.value); setPage(1); }}
              placeholder="Filter by stock code..."
              className="px-3 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">From</label>
            <input type="date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(1); }} className="px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">To</label>
            <input type="date" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(1); }} className="px-3 py-2 border rounded-lg" />
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Movements</h2>
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : !data?.results || data.results.length === 0 ? (
          <p className="text-gray-500 text-center py-12">No received or returned stock found</p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Date</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Type</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Stock Code</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Description</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Quantity</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Unit Cost</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Comments</th>
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((tx: any) => {
                    const isReceived = tx.transaction_type === 'INCOMING';
                    return (
                      <tr key={tx.id} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4">
                          {tx.transaction_date ? new Date(tx.transaction_date).toLocaleDateString('en-ZA') : '-'}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                            isReceived ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'
                          }`}>
                            {isReceived ? <ArrowDown className="w-3 h-3" /> : <ArrowUp className="w-3 h-3" />}
                            {isReceived ? 'Received' : 'Returned'}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono">{tx.stock_item}</td>
                        <td className="py-3 px-4">{tx.stock_item_detail?.description}</td>
                        <td className={`py-3 px-4 text-right font-medium ${isReceived ? 'text-green-600' : 'text-amber-600'}`}>
                          {isReceived ? '+' : '-'}{Number(isReceived ? tx.quantity_in : tx.quantity_out).toFixed(2)}
                        </td>
                        <td className="py-3 px-4 text-right">R {Number(tx.unit_cost || 0).toFixed(2)}</td>
                        <td className="py-3 px-4 text-gray-600">{tx.comments || '-'}</td>
                      </tr>
                    );
                  })}
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
