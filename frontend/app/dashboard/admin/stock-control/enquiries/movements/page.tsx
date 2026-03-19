'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getTransactions, getStockItems } from '@/lib/stockApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { 
  Loader, Search, ArrowLeft, ArrowDown, ArrowUp, 
  Package, Filter, Download, Calendar
} from 'lucide-react';
import Link from 'next/link';
import { Pagination } from '@/components/ui/pagination';

export default function MovementsPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    search: '',
    transaction_type: '',
    date_from: '',
    date_to: '',
  });

  const { data: stockItems } = useQuery({
    queryKey: ['stock-items-minimal'],
    queryFn: () => getStockItems({ page_size: 100 }),
    staleTime: 5 * 60 * 1000,
  });

  const { data: transactions, isLoading } = useQuery({
    queryKey: ['stock-transactions', filters, page],
    queryFn: () => getTransactions({
      search: filters.search || undefined,
      transaction_type: filters.transaction_type || undefined,
      date_from: filters.date_from || undefined,
      date_to: filters.date_to || undefined,
      page,
      page_size: 20,
    }),
    staleTime: 30 * 1000,
  });

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(1);
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      transaction_type: '',
      date_from: '',
      date_to: '',
    });
    setPage(1);
  };

  const hasActiveFilters = filters.search || filters.transaction_type || filters.date_from || filters.date_to;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/stock-control/enquiries">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Stock Movements</h1>
          <p className="text-gray-600 mt-1">View transaction history and movement patterns</p>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-600" />
          <h2 className="text-lg font-semibold">Filters</h2>
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters} className="ml-auto text-red-600">
              Clear Filters
            </Button>
          )}
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Stock Code</label>
            <Input
              placeholder="Search by code..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Transaction Type</label>
            <Select 
              value={filters.transaction_type || 'all'} 
              onValueChange={(value) => handleFilterChange('transaction_type', value === 'all' ? '' : value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="IN">Incoming</SelectItem>
                <SelectItem value="OUT">Outgoing</SelectItem>
                <SelectItem value="ADJ">Adjustment</SelectItem>
                <SelectItem value="SAL">Sales</SelectItem>
                <SelectItem value="RET">Return</SelectItem>
                <SelectItem value="GRN">Goods Received</SelectItem>
                <SelectItem value="TRF">Transfer</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Date From</label>
            <Input
              type="date"
              value={filters.date_from}
              onChange={(e) => handleFilterChange('date_from', e.target.value)}
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Date To</label>
            <Input
              type="date"
              value={filters.date_to}
              onChange={(e) => handleFilterChange('date_to', e.target.value)}
            />
          </div>

          <div className="flex items-end">
            <Button variant="outline" className="w-full">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 border-l-4 border-l-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Incoming</p>
              <p className="text-xl font-bold text-green-600">
                {Number(transactions?.results
                  ?.filter((t: any) => t.transaction_type === 'IN' || t.transaction_type === 'GRN')
                  ?.reduce((sum: number, t: any) => sum + (t.quantity > 0 ? t.quantity : 0), 0)
                  || 0).toFixed(0) || 0}
              </p>
            </div>
            <ArrowDown className="w-8 h-8 text-green-200" />
          </div>
        </Card>

        <Card className="p-4 border-l-4 border-l-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Outgoing</p>
              <p className="text-xl font-bold text-red-600">
                {Number(transactions?.results
                  ?.filter((t: any) => t.transaction_type === 'OUT' || t.transaction_type === 'SAL')
                  ?.reduce((sum: number, t: any) => sum + Math.abs(t.quantity < 0 ? t.quantity : 0), 0)
                  || 0).toFixed(0) || 0}
              </p>
            </div>
            <ArrowUp className="w-8 h-8 text-red-200" />
          </div>
        </Card>

        <Card className="p-4 border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Adjustments</p>
              <p className="text-xl font-bold text-amber-600">
                {transactions?.results
                  ?.filter((t: any) => t.transaction_type === 'ADJ')
                  ?.length || 0}
              </p>
            </div>
            <Package className="w-8 h-8 text-amber-200" />
          </div>
        </Card>

        <Card className="p-4 border-l-4 border-l-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Transactions</p>
              <p className="text-xl font-bold text-blue-600">
                {transactions?.count || 0}
              </p>
            </div>
            <Calendar className="w-8 h-8 text-blue-200" />
          </div>
        </Card>
      </div>

      {/* Transactions Table */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Transaction History</h3>
        
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : transactions?.results && transactions.results.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Date</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Stock Code</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Description</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Type</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Quantity</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Unit Cost</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Total</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Reference</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Department</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.results.map((tx: any) => (
                    <tr key={tx.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4">
                        {tx.transaction_date ? new Date(tx.transaction_date).toLocaleDateString('en-ZA') : '-'}
                      </td>
                      <td className="py-3 px-4 font-mono">{tx.stock_code}</td>
                      <td className="py-3 px-4 max-w-xs truncate">
                        {tx.stock_item_detail?.description || tx.description || '-'}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          tx.transaction_type === 'IN' || tx.transaction_type === 'GRN'
                            ? 'bg-green-100 text-green-800' 
                            : tx.transaction_type === 'OUT' || tx.transaction_type === 'SAL'
                            ? 'bg-red-100 text-red-800'
                            : tx.transaction_type === 'ADJ'
                            ? 'bg-amber-100 text-amber-800'
                            : tx.transaction_type === 'RET'
                            ? 'bg-purple-100 text-purple-800'
                            : tx.transaction_type === 'TRF'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {tx.transaction_type}
                        </span>
                      </td>
                      <td className={`py-3 px-4 text-right font-medium ${
                        tx.quantity > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {tx.quantity > 0 ? '+' : ''}{Number(tx.quantity || 0).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        R {Number(tx.unit_cost || 0).toFixed(2) || '0.00'}
                      </td>
                      <td className="py-3 px-4 text-right font-medium">
                        R {(Number(tx.quantity || 0) * Number(tx.unit_cost || 0)).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-gray-600">
                        {tx.reference || '-'}
                      </td>
                      <td className="py-3 px-4 text-gray-600">
                        {tx.department_detail?.name || tx.department || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {transactions.count > 20 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <p className="text-sm text-gray-600">
                  Showing {((page - 1) * 20) + 1} to {Math.min(page * 20, transactions.count)} of {transactions.count} transactions
                </p>
                <Pagination
                  currentPage={page}
                  totalPages={Math.ceil(transactions.count / 20)}
                  onPageChange={setPage}
                />
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 text-lg">No transactions found</p>
            <p className="text-gray-500 text-sm mt-1">Try adjusting your filters</p>
          </div>
        )}
      </Card>
    </div>
  );
}
