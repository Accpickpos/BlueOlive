'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { 
  Loader, Search, ArrowLeft, Download, AlertTriangle, 
  Package, ArrowRight
} from 'lucide-react';
import Link from 'next/link';
import { Pagination } from '@/components/ui/pagination';

export default function ReorderReportPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    search: '',
    level: 'all',
  });

  // Filtered + server-side-paginated list for the table. search/level are
  // now real backend params (StockItemViewSet.low_stock) instead of being
  // fetched in full and refiltered client-side on every keystroke.
  const { data: lowStockItems, isLoading } = useQuery({
    queryKey: ['low-stock-items', filters, page],
    queryFn: () => stockControlApi.stockItems.getLowStock({
      search: filters.search || undefined,
      level: filters.level === 'all' ? undefined : (filters.level as 'critical' | 'low'),
      page,
      page_size: 25,
    }),
    staleTime: 30 * 1000,
  });

  // Unfiltered list for the summary cards, which reflect the whole
  // reorder list regardless of the search/level filters above.
  const { data: allLowStock } = useQuery({
    queryKey: ['low-stock-items-all'],
    queryFn: () => stockControlApi.stockItems.getLowStock({ page_size: 1000 }),
    staleTime: 30 * 1000,
  });

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(1);
  };

  const exportToCSV = () => {
    if (!allLowStock?.results) return;

    const headers = ['Stock Code', 'Description', 'QOH', 'Reorder Qty', 'Shortage', 'Cost Price', 'Reorder Value', 'Status'];
    const rows = allLowStock.results.map((item: any) => [
      item.stock_code,
      item.description || '',
      item.quantity_on_hand,
      item.reorder_quantity,
      Math.max(0, item.reorder_quantity - item.quantity_on_hand),
      item.cost_price,
      Math.max(0, item.reorder_quantity - item.quantity_on_hand) * item.cost_price,
      item.quantity_on_hand <= 0 ? 'OUT OF STOCK' : 'LOW STOCK'
    ]);

    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `reorder-report-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  // Calculate summary stats
  const allItems = allLowStock?.results || [];
  const outOfStock = allItems.filter((item: any) => item.quantity_on_hand <= 0);
  const lowStock = allItems.filter((item: any) => item.quantity_on_hand > 0 && item.quantity_on_hand <= item.reorder_quantity);
  const totalReorderValue = allItems.reduce((sum: number, item: any) => {
    const shortage = Math.max(0, item.reorder_quantity - item.quantity_on_hand);
    return sum + (shortage * (item.cost_price || 0));
  }, 0);

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
          <h1 className="text-3xl font-bold">Re-Order Report</h1>
          <p className="text-gray-600 mt-1">Items at or below reorder level</p>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-6 border-l-4 border-l-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Out of Stock</p>
              <p className="text-2xl font-bold text-red-600 mt-1">{outOfStock.length}</p>
            </div>
            <Package className="w-8 h-8 text-red-200" />
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Low Stock</p>
              <p className="text-2xl font-bold text-amber-600 mt-1">{lowStock.length}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-amber-200" />
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-l-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Items</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">{allItems.length}</p>
            </div>
            <Package className="w-8 h-8 text-blue-200" />
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-l-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Reorder Value</p>
              <p className="text-2xl font-bold text-purple-600 mt-1">
                R {totalReorderValue.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <Download className="w-8 h-8 text-purple-200" />
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Search className="w-5 h-5 text-gray-600" />
          <h2 className="text-lg font-semibold">Filters</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Search</label>
            <Input
              placeholder="Search by code or description..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Stock Level</label>
            <Select 
              value={filters.level} 
              onValueChange={(value) => handleFilterChange('level', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Items</SelectItem>
                <SelectItem value="critical">Out of Stock Only</SelectItem>
                <SelectItem value="low">Low Stock Only</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-end">
            <Button onClick={exportToCSV} variant="outline" className="w-full">
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
          </div>
        </div>
      </Card>

      {/* Data Table */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Items Requiring Reorder</h3>
        
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : lowStockItems?.results && lowStockItems.results.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-left py-3 px-3 font-medium text-gray-600">Stock Code</th>
                    <th className="text-left py-3 px-3 font-medium text-gray-600">Description</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">QOH</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Reorder Qty</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Shortage</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Cost</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Reorder Value</th>
                    <th className="text-center py-3 px-3 font-medium text-gray-600">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {lowStockItems.results.map((item: any) => {
                    const shortage = Math.max(0, item.reorder_quantity - item.quantity_on_hand);
                    const reorderValue = shortage * (item.cost_price || 0);
                    
                    return (
                      <tr key={item.stock_code} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-3 font-mono">{item.stock_code}</td>
                        <td className="py-3 px-3 max-w-xs truncate">{item.description}</td>
                        <td className={`py-3 px-3 text-right font-medium ${
                          item.quantity_on_hand <= 0 ? 'text-red-600' : 'text-amber-600'
                        }`}>
                          {item.quantity_on_hand?.toFixed(2)}
                        </td>
                        <td className="py-3 px-3 text-right">{item.reorder_quantity?.toFixed(2)}</td>
                        <td className="py-3 px-3 text-right font-medium text-red-600">
                          {shortage.toFixed(2)}
                        </td>
                        <td className="py-3 px-3 text-right">
                          R {item.cost_price?.toFixed(2)}
                        </td>
                        <td className="py-3 px-3 text-right font-medium">
                          R {reorderValue.toFixed(2)}
                        </td>
                        <td className="py-3 px-3 text-center">
                          {item.quantity_on_hand <= 0 ? (
                            <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-red-100 text-red-800">
                              OUT OF STOCK
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-amber-100 text-amber-800">
                              LOW STOCK
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {lowStockItems.count > 25 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <p className="text-sm text-gray-600">
                  Showing {((page - 1) * 25) + 1} to {Math.min(page * 25, lowStockItems.count)} of {lowStockItems.count} items
                </p>
                <Pagination
                  currentPage={page}
                  totalPages={Math.ceil(lowStockItems.count / 25)}
                  onPageChange={setPage}
                />
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 text-lg">No items requiring reorder</p>
          </div>
        )}
      </Card>

      {/* Quick Actions */}
      <Card className="p-6 bg-blue-50">
        <h3 className="font-semibold mb-3">Quick Actions</h3>
        <div className="flex gap-4">
          <Link href="/dashboard/admin/stock-control/maintenance/items">
            <Button variant="outline">
              Create Purchase Order
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
