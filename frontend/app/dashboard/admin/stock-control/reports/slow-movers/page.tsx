'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import {
  Loader, ArrowLeft, TrendingDown, Download,
  Package, AlertTriangle
} from 'lucide-react';
import Link from 'next/link';
import { Pagination } from '@/components/ui/pagination';

export default function SlowMoversReportPage() {
  const [page, setPage] = useState(1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [searchTerm, setSearchTerm] = useState('');
  const [threshold, setThreshold] = useState('10'); // items sold per month threshold

  const years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i);

  // Backend-computed slow movers — was previously computed client-side
  // from monthlyStats rows reading total_sales/stock_item_detail?.description
  // (neither exists on StockMonthlyStatisticSerializer, so Description and
  // Sales Value always rendered blank/R0), and averaged totalQuantitySold
  // by a hardcoded /12 regardless of how many months of the year had
  // actually elapsed — understating the average for a partial current
  // year. The backend divides by the number of months that actually have
  // data instead.
  const { data: rows, isLoading: statsLoading } = useQuery({
    queryKey: ['stats-slow-movers', year, threshold],
    queryFn: () => stockControlApi.enquiries.statsSlowMovers({ year, threshold: parseInt(threshold) }),
    staleTime: 30 * 1000,
  });

  const allSlowMovers = (rows || []).map((r) => ({
    stock_code: r.stock_item_id,
    description: r.description || '',
    totalQuantitySold: Number(r.total_quantity || 0),
    totalSales: Number(r.total_sales || 0),
    avgMonthlySales: r.avg_monthly_sales,
    monthsWithData: r.months_with_data,
  }));

  const slowMovers = searchTerm
    ? allSlowMovers.filter((item) =>
        item.stock_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.description?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : allSlowMovers;

  const totals = {
    count: slowMovers.length,
    totalValue: slowMovers.reduce((sum, item) => sum + item.totalSales, 0),
  };

  const paginatedItems = slowMovers.slice((page - 1) * 25, page * 25);

  const exportToCSV = () => {
    const headers = ['Stock Code', 'Description', 'Total Sold', 'Avg Monthly', 'Months w/ Data', 'Total Sales'];
    const rows = slowMovers.map((item) => [
      item.stock_code,
      item.description || '',
      item.totalQuantitySold,
      item.avgMonthlySales.toFixed(2),
      item.monthsWithData,
      item.totalSales.toFixed(2)
    ]);

    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `slow-movers-${year}.csv`;
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
          <h1 className="text-3xl font-bold">Slow Movers Report</h1>
          <p className="text-gray-600 mt-1">Items with low sales activity</p>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Year</label>
            <Select value={year.toString()} onValueChange={(v) => { setYear(parseInt(v)); setPage(1); }}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {years.map(y => (
                  <SelectItem key={y} value={y.toString()}>{y}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Max Avg Monthly Sales</label>
            <Select value={threshold} onValueChange={(v) => { setThreshold(v); setPage(1); }}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0">Zero sales</SelectItem>
                <SelectItem value="5">5 or less</SelectItem>
                <SelectItem value="10">10 or less</SelectItem>
                <SelectItem value="20">20 or less</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex-1">
            <label className="text-sm font-medium text-gray-700 mb-1 block">Search</label>
            <Input
              placeholder="Search by code or description..."
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
            />
          </div>

          <Button onClick={exportToCSV} variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </Card>

      {/* Summary Stats */}
      {totals && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-6 border-l-4 border-l-amber-500">
            <div className="flex items-center gap-3">
              <TrendingDown className="w-8 h-8 text-amber-500" />
              <div>
                <p className="text-xs text-gray-600 uppercase">Slow Movers Count</p>
                <p className="text-2xl font-bold text-amber-600">{totals.count}</p>
              </div>
            </div>
          </Card>
          <Card className="p-6 border-l-4 border-l-blue-500">
            <div className="flex items-center gap-3">
              <Package className="w-8 h-8 text-blue-500" />
              <div>
                <p className="text-xs text-gray-600 uppercase">Total Sales Value</p>
                <p className="text-2xl font-bold text-blue-600">R {totals.totalValue.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</p>
              </div>
            </div>
          </Card>
          <Card className="p-6 border-l-4 border-l-red-500">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-8 h-8 text-red-500" />
              <div>
                <p className="text-xs text-gray-600 uppercase">No Sales</p>
                <p className="text-2xl font-bold text-red-600">
                  {slowMovers.filter((i) => i.totalQuantitySold === 0).length}
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Data Table */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Slow Moving Items</h3>
        
        {statsLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : paginatedItems.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-left py-3 px-3 font-medium text-gray-600">Stock Code</th>
                    <th className="text-left py-3 px-3 font-medium text-gray-600">Description</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Total Sold</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Avg/Month</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Months w/ Data</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Sales Value</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedItems.map((item) => (
                    <tr key={item.stock_code} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-3 font-mono">{item.stock_code}</td>
                      <td className="py-3 px-3 max-w-xs truncate">{item.description}</td>
                      <td className="py-3 px-3 text-right">{item.totalQuantitySold.toLocaleString()}</td>
                      <td className="py-3 px-3 text-right">
                        <span className={`font-medium ${
                          item.avgMonthlySales === 0 ? 'text-red-600' : 'text-amber-600'
                        }`}>
                          {item.avgMonthlySales.toFixed(2)}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <span className={`px-2 py-1 rounded text-xs ${
                          item.totalQuantitySold === 0 ? 'bg-red-100 text-red-800' :
                          item.monthsWithData <= 3 ? 'bg-amber-100 text-amber-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {item.monthsWithData}/12
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right">R {item.totalSales.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {slowMovers.length > 25 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <p className="text-sm text-gray-600">
                  Showing {((page - 1) * 25) + 1} to {Math.min(page * 25, slowMovers.length)} of {slowMovers.length} items
                </p>
                <Pagination
                  currentPage={page}
                  totalPages={Math.ceil(slowMovers.length / 25)}
                  onPageChange={setPage}
                />
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <TrendingDown className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 text-lg">No slow movers found for {year}</p>
          </div>
        )}
      </Card>
    </div>
  );
}
