'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader, ArrowLeft, Layers } from 'lucide-react';
import Link from 'next/link';

export default function SalesByDepartmentPage() {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const { data: rows, isLoading } = useQuery({
    queryKey: ['sales-by-department', dateFrom, dateTo],
    queryFn: () =>
      stockControlApi.enquiries.salesByDepartment({
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      }),
    staleTime: 30 * 1000,
  });

  const totalValue = (rows || []).reduce((sum, r) => sum + Number(r.total_value || 0), 0);

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
          <h1 className="text-3xl font-bold">Sales by Department</h1>
          <p className="text-gray-600 mt-1">Sales value and quantity grouped by sales department</p>
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
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Layers className="w-5 h-5 mr-2" />
          By Department
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
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Department</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Qty Sold</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Value</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">% of Total</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.department_id ?? 'none'} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">{row.department__name || 'Unassigned'}</td>
                    <td className="py-3 px-4 text-right">{Number(row.total_quantity || 0).toFixed(2)}</td>
                    <td className="py-3 px-4 text-right font-medium">R {Number(row.total_value || 0).toFixed(2)}</td>
                    <td className="py-3 px-4 text-right">
                      {totalValue > 0 ? ((Number(row.total_value || 0) / totalValue) * 100).toFixed(1) : '0.0'}%
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-gray-100 font-bold">
                  <td className="py-3 px-4">TOTAL</td>
                  <td className="py-3 px-4 text-right">
                    {rows.reduce((sum, r) => sum + Number(r.total_quantity || 0), 0).toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-right">R {totalValue.toFixed(2)}</td>
                  <td className="py-3 px-4 text-right">100%</td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
