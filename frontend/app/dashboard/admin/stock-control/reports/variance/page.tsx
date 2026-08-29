'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { 
  Loader, ArrowLeft, Activity, Download, 
  CheckCircle, XCircle, ArrowRight
} from 'lucide-react';
import Link from 'next/link';

export default function VarianceReportPage() {
  const [selectedTakeId, setSelectedTakeId] = useState<string>('latest');

  // Fetch stock takes
  const { data: stockTakes, isLoading: takesLoading } = useQuery({
    queryKey: ['stock-takes-for-variance'],
    queryFn: () => stockControlApi.stockTakes.list({ page_size: 20 }),
    staleTime: 30 * 1000,
  });

  // Get completed takes
  const completedTakes = stockTakes?.results?.filter((t: any) => t.status === 'COMPLETED') || [];
  const latestCompleted = completedTakes[0];

  // Fetch variance report for selected stock take
  const { data: varianceItems, isLoading: varianceLoading } = useQuery({
    queryKey: ['variance-report', selectedTakeId, latestCompleted],
    queryFn: async () => {
      if (!completedTakes.length) return [];
      
      let takeId = selectedTakeId;
      if (selectedTakeId === 'latest') {
        if (!latestCompleted) return [];
        takeId = latestCompleted.id.toString();
      }
      
      if (takeId === 'all') {
        // Could aggregate from all, but for now return empty
        return [];
      }
      
      return stockControlApi.stockTakes.getVarianceReport(parseInt(takeId));
    },
    enabled: !!completedTakes.length,
    staleTime: 30 * 1000,
  });

  // Calculate summary from variance items
  const getSummary = () => {
    if (!varianceItems || !Array.isArray(varianceItems)) return null;
    
    const positive = varianceItems.filter((item: any) => item.variance_quantity > 0);
    const negative = varianceItems.filter((item: any) => item.variance_quantity < 0);
    const zero = varianceItems.filter((item: any) => item.variance_quantity === 0);
    
    const positiveValue = positive.reduce((sum: number, item: any) => sum + Number(item.variance_value || 0), 0);
    const negativeValue = Math.abs(negative.reduce((sum: number, item: any) => sum + Number(item.variance_value || 0), 0));
    
    return {
      total: varianceItems.length,
      positive: positive.length,
      negative: negative.length,
      zero: zero.length,
      positiveValue,
      negativeValue,
    };
  };

  const summary = getSummary();

  const exportToCSV = () => {
    if (!varianceItems || !Array.isArray(varianceItems)) return;
    
    const headers = ['Stock Code', 'Description', 'System Qty', 'Counted Qty', 'Variance', 'Unit Cost', 'Variance Value'];
    const rows = varianceItems.map((item: any) => [
      item.stock_item_detail?.stock_code,
      item.stock_item_detail?.description || item.description || '',
      item.quantity_on_hand,
      item.quantity_counted,
      item.variance_quantity,
      item.cost_price_at_count,
      item.variance_value
    ]);

    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `variance-report-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/stock-control/reports">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Stock Variance Report</h1>
          <p className="text-gray-600 mt-1">Stock take count discrepancies</p>
        </div>
      </div>

      {/* Stock Take Selection */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">Select Stock Take</h2>
        
        {takesLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : completedTakes.length > 0 ? (
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="text-sm font-medium text-gray-700 mb-1 block">Stock Take</label>
              <Select 
                value={selectedTakeId} 
                onValueChange={setSelectedTakeId}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a stock take" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="latest">
                    Latest ({latestCompleted ? new Date(latestCompleted.stock_take_date).toLocaleDateString('en-ZA') : 'N/A'})
                  </SelectItem>
                  {completedTakes.map((take: any) => (
                    <SelectItem key={take.id} value={take.id.toString()}>
                      #{take.id} - {take.stock_take_date ? new Date(take.stock_take_date).toLocaleDateString('en-ZA') : 'N/A'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={exportToCSV} variant="outline" disabled={!varianceItems?.length}>
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
          </div>
        ) : (
          <div className="text-center py-8">
            <Activity className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600">No completed stock takes found</p>
            <Link href="/dashboard/admin/stock-control/transactions/stocktake">
              <Button variant="outline" className="mt-4">
                Go to Stock Take
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        )}
      </Card>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card className="p-4">
            <p className="text-xs text-gray-600 uppercase">Total Items</p>
            <p className="text-xl font-bold">{summary.total}</p>
          </Card>
          <Card className="p-4 border-l-4 border-l-green-500">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-xs text-gray-600 uppercase">Positive (Found)</p>
                <p className="text-xl font-bold text-green-600">{summary.positive}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4 border-l-4 border-l-red-500">
            <div className="flex items-center gap-2">
              <XCircle className="w-5 h-5 text-red-600" />
              <div>
                <p className="text-xs text-gray-600 uppercase">Negative (Missing)</p>
                <p className="text-xl font-bold text-red-600">{summary.negative}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4 border-l-4 border-l-blue-500">
            <p className="text-xs text-gray-600 uppercase">Surplus Value</p>
            <p className="text-xl font-bold text-green-600">R {summary.positiveValue.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</p>
          </Card>
          <Card className="p-4 border-l-4 border-l-amber-500">
            <p className="text-xs text-gray-600 uppercase">Shortage Value</p>
            <p className="text-xl font-bold text-red-600">R {summary.negativeValue.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</p>
          </Card>
        </div>
      )}

      {/* Variance Table */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Variance Details</h3>
        
        {varianceLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : varianceItems && varianceItems.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left py-3 px-3 font-medium text-gray-600">Stock Code</th>
                  <th className="text-left py-3 px-3 font-medium text-gray-600">Description</th>
                  <th className="text-right py-3 px-3 font-medium text-gray-600">System Qty</th>
                  <th className="text-right py-3 px-3 font-medium text-gray-600">Counted Qty</th>
                  <th className="text-right py-3 px-3 font-medium text-gray-600">Variance</th>
                  <th className="text-right py-3 px-3 font-medium text-gray-600">Unit Cost</th>
                  <th className="text-right py-3 px-3 font-medium text-gray-600">Value Impact</th>
                  <th className="text-center py-3 px-3 font-medium text-gray-600">Status</th>
                </tr>
              </thead>
              <tbody>
                {varianceItems.map((item: any, idx: number) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-3 font-mono">{item.stock_item_detail?.stock_code}</td>
                    <td className="py-3 px-3 max-w-xs truncate">
                      {item.stock_item_detail?.description || item.description || '-'}
                    </td>
                    <td className="py-3 px-3 text-right">{item.quantity_on_hand?.toFixed(2)}</td>
                    <td className="py-3 px-3 text-right">{item.quantity_counted?.toFixed(2)}</td>
                    <td className={`py-3 px-3 text-right font-medium ${
                      item.variance_quantity > 0 ? 'text-green-600' : item.variance_quantity < 0 ? 'text-red-600' : 'text-gray-600'
                    }`}>
                      {item.variance_quantity > 0 ? '+' : ''}{item.variance_quantity?.toFixed(2)}
                    </td>
                    <td className="py-3 px-3 text-right">R {item.cost_price_at_count?.toFixed(2)}</td>
                    <td className={`py-3 px-3 text-right font-medium ${
                      Number(item.variance_value) > 0 ? 'text-green-600' : Number(item.variance_value) < 0 ? 'text-red-600' : 'text-gray-600'
                    }`}>
                      R {Number(item.variance_value || 0).toFixed(2)}
                    </td>
                    <td className="py-3 px-3 text-center">
                      {item.variance_quantity > 0 ? (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-green-100 text-green-800">
                          Surplus
                        </span>
                      ) : item.variance_quantity < 0 ? (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-red-100 text-red-800">
                          Shortage
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-800">
                          Exact
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <Activity className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 text-lg">Select a stock take to view variance</p>
          </div>
        )}
      </Card>
    </div>
  );
}
