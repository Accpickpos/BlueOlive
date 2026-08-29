'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getStockItems, getStockSummary } from '@/lib/stockApi';
import { api } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import {
  Loader, Search, ArrowLeft, Download, Package,
  Filter, AlertTriangle
} from 'lucide-react';
import Link from 'next/link';
import { Pagination } from '@/components/ui/pagination';

const ORDERING_OPTIONS = [
  { value: 'stock_code', label: 'Stock Code' },
  { value: 'description', label: 'Description' },
  { value: 'department', label: 'Department' },
  { value: 'quantity_on_hand', label: 'Quantity on Hand' },
  { value: 'cost_price', label: 'Cost Price' },
  { value: 'selling_price_1', label: 'Selling Price' },
];

export default function DetailsReportPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    search: '',
    is_active: 'all',
    department: 'all',
    code_from: '',
    code_to: '',
    ordering: 'stock_code',
  });

  const { data: summary } = useQuery({
    queryKey: ['stock-summary'],
    queryFn: getStockSummary,
    staleTime: 5 * 60 * 1000,
  });

  // Was previously declared in filter state but never had a UI control to
  // set it — always 'all' regardless of what the user picked, since there
  // was no picker at all.
  const { data: departments } = useQuery({
    queryKey: ['departments'],
    queryFn: async () => {
      const response = await api.get('/api/v1/settings/departments/');
      return response.data.results || response.data;
    },
    staleTime: 5 * 60 * 1000,
  });

  const { data: stockItems, isLoading } = useQuery({
    queryKey: ['stock-items-report', filters, page],
    queryFn: () => getStockItems({
      search: filters.search || undefined,
      is_active: filters.is_active === 'all' ? undefined : filters.is_active === 'true',
      department: filters.department === 'all' ? undefined : parseInt(filters.department),
      code_from: filters.code_from || undefined,
      code_to: filters.code_to || undefined,
      page,
      page_size: 25,
      ordering: filters.ordering,
    }),
    staleTime: 30 * 1000,
  });

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(1);
  };

  const exportToCSV = () => {
    if (!stockItems?.results) return;
    
    const headers = ['Stock Code', 'Description', 'Department', 'QOH', 'Reorder Qty', 'Cost Price', 'Selling Price 1', 'Active'];
    const rows = stockItems.results.map((item: any) => [
      item.stock_code,
      item.description,
      item.department_detail?.name || '',
      item.quantity_on_hand,
      item.reorder_quantity,
      item.cost_price,
      item.selling_price_1,
      item.is_active ? 'Yes' : 'No'
    ]);

    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `stock-details-${new Date().toISOString().split('T')[0]}.csv`;
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
          <h1 className="text-3xl font-bold">Stock Details Report</h1>
          <p className="text-gray-600 mt-1">Full item listings with all details</p>
        </div>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <p className="text-xs text-gray-600 uppercase">Total Items</p>
            <p className="text-xl font-bold">{summary.total_items?.toLocaleString() || 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-gray-600 uppercase">Active Items</p>
            <p className="text-xl font-bold text-green-600">{summary.active_items?.toLocaleString() || 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-gray-600 uppercase">Inactive Items</p>
            <p className="text-xl font-bold text-gray-600">{summary.inactive_items?.toLocaleString() || 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-gray-600 uppercase">Total Value</p>
            <p className="text-xl font-bold text-blue-600">R {(summary.total_value || 0).toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</p>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-600" />
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
            <label className="text-sm font-medium text-gray-700 mb-1 block">Status</label>
            <Select
              value={filters.is_active}
              onValueChange={(value) => handleFilterChange('is_active', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Items</SelectItem>
                <SelectItem value="true">Active Only</SelectItem>
                <SelectItem value="false">Inactive Only</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Department</label>
            <Select
              value={filters.department}
              onValueChange={(value) => handleFilterChange('department', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Departments</SelectItem>
                {departments?.map((dept: any) => (
                  <SelectItem key={dept.id} value={dept.id.toString()}>
                    {dept.department_name || dept.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Code From</label>
            <Input
              placeholder="e.g. 1000"
              value={filters.code_from}
              onChange={(e) => handleFilterChange('code_from', e.target.value)}
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Code To</label>
            <Input
              placeholder="e.g. 9999"
              value={filters.code_to}
              onChange={(e) => handleFilterChange('code_to', e.target.value)}
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Sort By</label>
            <Select
              value={filters.ordering}
              onValueChange={(value) => handleFilterChange('ordering', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ORDERING_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                ))}
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
        <h3 className="text-lg font-semibold mb-4">Stock Items</h3>
        
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : stockItems?.results && stockItems.results.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-left py-3 px-3 font-medium text-gray-600">Stock Code</th>
                    <th className="text-left py-3 px-3 font-medium text-gray-600">Description</th>
                    <th className="text-left py-3 px-3 font-medium text-gray-600">Department</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">QOH</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Reorder</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Cost</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Sell Price</th>
                    <th className="text-center py-3 px-3 font-medium text-gray-600">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {stockItems.results.map((item: any) => (
                    <tr key={item.stock_code} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-3 font-mono">{item.stock_code}</td>
                      <td className="py-3 px-3 max-w-xs truncate">{item.description}</td>
                      <td className="py-3 px-3">{item.department_detail?.name || '-'}</td>
                      <td className={`py-3 px-3 text-right font-medium ${
                        item.quantity_on_hand <= 0 ? 'text-red-600' :
                        item.quantity_on_hand <= item.reorder_quantity ? 'text-amber-600' : ''
                      }`}>
                        {item.quantity_on_hand?.toFixed(2)}
                      </td>
                      <td className="py-3 px-3 text-right text-gray-600">
                        {item.reorder_quantity?.toFixed(2)}
                      </td>
                      <td className="py-3 px-3 text-right">
                        R {item.cost_price?.toFixed(2)}
                      </td>
                      <td className="py-3 px-3 text-right">
                        R {item.selling_price_1?.toFixed(2)}
                      </td>
                      <td className="py-3 px-3 text-center">
                        {item.quantity_on_hand <= item.reorder_quantity && item.quantity_on_hand > 0 ? (
                          <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-amber-100 text-amber-800">
                            <AlertTriangle className="w-3 h-3 mr-1" /> Low
                          </span>
                        ) : item.quantity_on_hand <= 0 ? (
                          <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-red-100 text-red-800">
                            Out
                          </span>
                        ) : item.is_active ? (
                          <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-800">Active</span>
                        ) : (
                          <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-800">Inactive</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {stockItems.count > 25 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <p className="text-sm text-gray-600">
                  Showing {((page - 1) * 25) + 1} to {Math.min(page * 25, stockItems.count)} of {stockItems.count} items
                </p>
                <Pagination
                  currentPage={page}
                  totalPages={Math.ceil(stockItems.count / 25)}
                  onPageChange={setPage}
                />
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 text-lg">No stock items found</p>
          </div>
        )}
      </Card>
    </div>
  );
}
