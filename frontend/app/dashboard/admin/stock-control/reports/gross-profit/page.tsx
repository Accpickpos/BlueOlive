'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import {
  Loader, ArrowLeft, TrendingUp, Download, Search,
  DollarSign, Percent
} from 'lucide-react';
import Link from 'next/link';
import { Pagination } from '@/components/ui/pagination';

export default function GrossProfitReportPage() {
  const [page, setPage] = useState(1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStockCode, setSelectedStockCode] = useState('');

  const years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i);

  // Backend-aggregated sales/cost/profit by item (+ monthly trend when a
  // specific item is selected) — was previously computed client-side from
  // monthlyStats rows reading total_sales/total_cost/gross_profit and
  // stock_item_detail?.description, none of which exist on
  // StockMonthlyStatisticSerializer, so every number here rendered R0 and
  // Description was always blank. selectedStockCode also had no UI path
  // to ever become non-empty — the search box only filtered a list that
  // was already empty of real data — so item-scoped trend was dead too;
  // clicking a row below now sets it for real.
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats-by-item', year, selectedStockCode],
    queryFn: () => stockControlApi.enquiries.statsByItem({
      year,
      stock_item: selectedStockCode || undefined,
    }),
    staleTime: 30 * 1000,
  });

  const byItem = (stats?.by_item || []).map((r) => ({
    stock_code: r.stock_item_id,
    description: r.description || '',
    totalSales: Number(r.total_sales || 0),
    totalCost: Number(r.total_cost || 0),
    totalProfit: Number(r.total_profit || 0),
    quantitySold: Number(r.total_quantity || 0),
    margin: r.margin_pct,
  }));

  const totals = byItem.length
    ? byItem.reduce(
        (acc, item) => ({
          totalSales: acc.totalSales + item.totalSales,
          totalCost: acc.totalCost + item.totalCost,
          totalProfit: acc.totalProfit + item.totalProfit,
          quantitySold: acc.quantitySold + item.quantitySold,
          margin: 0,
        }),
        { totalSales: 0, totalCost: 0, totalProfit: 0, quantitySold: 0, margin: 0 }
      )
    : null;
  if (totals) totals.margin = totals.totalSales > 0 ? (totals.totalProfit / totals.totalSales) * 100 : 0;

  const byMonth = (stats?.by_month || []).map((m) => ({
    month: m.month,
    totalSales: Number(m.total_sales || 0),
    totalCost: Number(m.total_cost || 0),
    totalProfit: Number(m.total_profit || 0),
    quantitySold: Number(m.total_quantity || 0),
  }));

  // Filter by search term
  const filteredItems = searchTerm
    ? byItem.filter((item) =>
        item.stock_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.description?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : byItem;

  const paginatedItems = filteredItems.slice((page - 1) * 25, page * 25);

  const exportToCSV = () => {
    const headers = ['Stock Code', 'Description', 'Qty Sold', 'Total Sales', 'Total Cost', 'Gross Profit', 'Margin %'];
    const rows = filteredItems.map((item: any) => [
      item.stock_code,
      item.description || '',
      item.quantitySold,
      item.totalSales.toFixed(2),
      item.totalCost.toFixed(2),
      item.totalProfit.toFixed(2),
      item.margin.toFixed(2)
    ]);

    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gross-profit-report-${year}.csv`;
    a.click();
  };

  const handleStockSelect = (code: string) => {
    setSelectedStockCode(code);
    setSearchTerm('');
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
          <h1 className="text-3xl font-bold">Gross Profit Report</h1>
          <p className="text-gray-600 mt-1">Profitability analysis by item</p>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Year</label>
            <Select value={year.toString()} onValueChange={(v) => setYear(parseInt(v))}>
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

          <div className="flex-1 min-w-64">
            <label className="text-sm font-medium text-gray-700 mb-1 block">Stock Item (Optional)</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search for specific item..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  if (e.target.value) setSelectedStockCode('');
                }}
                className="pl-10"
              />
            </div>
          </div>

          {selectedStockCode && (
            <Button variant="ghost" onClick={() => setSelectedStockCode('')} className="text-red-600">
              Clear Filter
            </Button>
          )}

          <Button onClick={exportToCSV} variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </Card>

      {/* Summary Stats */}
      {totals && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card className="p-4">
            <p className="text-xs text-gray-600 uppercase">Total Sales</p>
            <p className="text-xl font-bold">R {totals.totalSales.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-gray-600 uppercase">Total Cost</p>
            <p className="text-xl font-bold text-red-600">R {totals.totalCost.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</p>
          </Card>
          <Card className="p-4 border-l-4 border-l-green-500">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-xs text-gray-600 uppercase">Gross Profit</p>
                <p className="text-xl font-bold text-green-600">R {totals.totalProfit.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4 border-l-4 border-l-blue-500">
            <div className="flex items-center gap-2">
              <Percent className="w-5 h-5 text-blue-600" />
              <div>
                <p className="text-xs text-gray-600 uppercase">Avg Margin</p>
                <p className="text-xl font-bold text-blue-600">{totals.margin?.toFixed(1)}%</p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-gray-600 uppercase">Items Sold</p>
            <p className="text-xl font-bold">{totals.quantitySold.toLocaleString('en-ZA')}</p>
          </Card>
        </div>
      )}

      {/* Monthly Trend */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">
          Monthly Trend {selectedStockCode && `— ${selectedStockCode}`}
        </h3>
        {!selectedStockCode ? (
          <p className="text-gray-500 text-center py-8">Click an item below to see its monthly trend</p>
        ) : statsLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : byMonth.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left py-3 px-3 font-medium text-gray-600">Month</th>
                  <th className="text-right py-3 px-3 font-medium text-gray-600">Qty Sold</th>
                  <th className="text-right py-3 px-3 font-medium text-gray-600">Sales</th>
                  <th className="text-right py-3 px-3 font-medium text-gray-600">Cost</th>
                  <th className="text-right py-3 px-3 font-medium text-gray-600">Profit</th>
                  <th className="text-right py-3 px-3 font-medium text-gray-600">Margin</th>
                </tr>
              </thead>
              <tbody>
                {byMonth.map((month: any) => {
                  const margin = month.totalSales > 0 ? (month.totalProfit / month.totalSales) * 100 : 0;
                  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                  return (
                    <tr key={month.month} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-3 font-medium">{monthNames[month.month - 1]}</td>
                      <td className="py-3 px-3 text-right">{month.quantitySold.toLocaleString('en-ZA')}</td>
                      <td className="py-3 px-3 text-right">R {month.totalSales.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                      <td className="py-3 px-3 text-right text-red-600">R {month.totalCost.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                      <td className="py-3 px-3 text-right font-medium text-green-600">R {month.totalProfit.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                      <td className="py-3 px-3 text-right">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          margin >= 30 ? 'bg-green-100 text-green-800' :
                          margin >= 20 ? 'bg-amber-100 text-amber-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {margin.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No data available for {year}</p>
        )}
      </Card>

      {/* By Item Table */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Profitability by Item</h3>
        
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
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Qty Sold</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Sales</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Cost</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Profit</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Margin</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedItems.map((item: any) => (
                    <tr
                      key={item.stock_code}
                      onClick={() => handleStockSelect(item.stock_code)}
                      className={`border-b hover:bg-gray-50 cursor-pointer ${selectedStockCode === item.stock_code ? 'bg-blue-50' : ''}`}
                      title="Click to view this item's monthly trend"
                    >
                      <td className="py-3 px-3 font-mono">{item.stock_code}</td>
                      <td className="py-3 px-3 max-w-xs truncate">{item.description}</td>
                      <td className="py-3 px-3 text-right">{item.quantitySold.toLocaleString('en-ZA')}</td>
                      <td className="py-3 px-3 text-right">R {item.totalSales.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                      <td className="py-3 px-3 text-right text-red-600">R {item.totalCost.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                      <td className="py-3 px-3 text-right font-medium text-green-600">
                        R {item.totalProfit.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
                      </td>
                      <td className="py-3 px-3 text-right">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          item.margin >= 30 ? 'bg-green-100 text-green-800' :
                          item.margin >= 20 ? 'bg-amber-100 text-amber-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {item.margin.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {filteredItems.length > 25 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <p className="text-sm text-gray-600">
                  Showing {((page - 1) * 25) + 1} to {Math.min(page * 25, filteredItems.length)} of {filteredItems.length} items
                </p>
                <Pagination
                  currentPage={page}
                  totalPages={Math.ceil(filteredItems.length / 25)}
                  onPageChange={setPage}
                />
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <DollarSign className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 text-lg">No profit data available for {year}</p>
          </div>
        )}
      </Card>
    </div>
  );
}
