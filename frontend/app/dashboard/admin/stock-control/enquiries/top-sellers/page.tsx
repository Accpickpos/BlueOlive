'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader, ArrowLeft, Trophy } from 'lucide-react';
import Link from 'next/link';

export default function TopSellersPage() {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [limit, setLimit] = useState(20);

  const { data: rows, isLoading } = useQuery({
    queryKey: ['top-sellers', dateFrom, dateTo, limit],
    queryFn: () =>
      stockControlApi.enquiries.topSellers({
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        limit,
      }),
    staleTime: 30 * 1000,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/stock-control/enquiries">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Top Sellers</h1>
          <p className="text-gray-600 mt-1">Best-selling items by quantity</p>
        </div>
      </div>

      <Card className="p-4">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">From</label>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">To</label>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Show Top</label>
            <select value={limit} onChange={(e) => setLimit(Number(e.target.value))} className="px-3 py-2 border rounded-lg">
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Trophy className="w-5 h-5 mr-2 text-amber-600" />
          Best Sellers
        </h2>
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : !rows || rows.length === 0 ? (
          <p className="text-gray-500 text-center py-12">No sales in this period</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Rank</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Stock Code</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Description</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Qty Sold</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Value</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, idx) => (
                  <tr key={row.stock_item_id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 text-gray-500">#{idx + 1}</td>
                    <td className="py-3 px-4 font-mono">{row.stock_item_id}</td>
                    <td className="py-3 px-4">{row.stock_item__description}</td>
                    <td className="py-3 px-4 text-right font-medium">{Number(row.total_quantity || 0).toFixed(2)}</td>
                    <td className="py-3 px-4 text-right">R {Number(row.total_value || 0).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
