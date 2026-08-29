'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader, ArrowLeft, DollarSign } from 'lucide-react';
import Link from 'next/link';

export default function StockValuationReportPage() {
  const [codeFrom, setCodeFrom] = useState('');
  const [codeTo, setCodeTo] = useState('');
  const [costBasis, setCostBasis] = useState<'last' | 'average'>('last');

  const { data, isLoading } = useQuery({
    queryKey: ['valuation-report', codeFrom, codeTo, costBasis],
    queryFn: () => stockControlApi.stockItems.getValuationReport({
      code_from: codeFrom || undefined,
      code_to: codeTo || undefined,
      cost_basis: costBasis,
    }),
    staleTime: 30 * 1000,
  });

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
          <h1 className="text-3xl font-bold">Stock Valuation Report</h1>
          <p className="text-gray-600 mt-1">Parameterized valuation by code range and cost basis</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Code From</label>
            <input type="text" value={codeFrom} onChange={(e) => setCodeFrom(e.target.value)} placeholder="e.g. 1000" className="px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Code To</label>
            <input type="text" value={codeTo} onChange={(e) => setCodeTo(e.target.value)} placeholder="e.g. 9999" className="px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Cost Basis</label>
            <div className="flex rounded-lg border overflow-hidden">
              <button
                onClick={() => setCostBasis('last')}
                className={`px-3 py-2 text-sm ${costBasis === 'last' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
              >
                Last Cost
              </button>
              <button
                onClick={() => setCostBasis('average')}
                className={`px-3 py-2 text-sm border-l ${costBasis === 'average' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
              >
                Average Cost
              </button>
            </div>
          </div>
        </div>
      </Card>

      {data && (
        <Card className="p-4 border-l-4 border-l-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Stock Value ({costBasis === 'last' ? 'Last Cost' : 'Average Cost'})</p>
              <p className="text-2xl font-bold text-green-600 mt-1">
                R {Number(data.total_value).toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-green-200" />
          </div>
        </Card>
      )}

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Item Valuation</h2>
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : !data?.items || data.items.length === 0 ? (
          <p className="text-gray-500 text-center py-12">No items found in this range</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Stock Code</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Description</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Department</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Qty on Hand</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Unit Cost</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Value</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.stock_code} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 font-mono">{item.stock_code}</td>
                    <td className="py-3 px-4">{item.description}</td>
                    <td className="py-3 px-4">{item.department_name || '-'}</td>
                    <td className={`py-3 px-4 text-right ${Number(item.quantity_on_hand) < 0 ? 'text-red-600 font-semibold' : ''}`}>
                      {Number(item.quantity_on_hand).toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-right">R {Number(item.unit_cost).toFixed(2)}</td>
                    <td className="py-3 px-4 text-right font-medium">R {Number(item.value).toFixed(2)}</td>
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
