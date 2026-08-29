'use client';

import { useQuery } from '@tanstack/react-query';
import { getStockSummary, getStockItems } from '@/lib/stockApi';
import { stockControlApi } from '@/lib/stockControlApi';
import { Card } from '@/components/ui/card';
import { 
  Loader, FileText, Activity, Box, DollarSign, 
  ArrowRight, AlertTriangle, TrendingUp
} from 'lucide-react';
import Link from 'next/link';

export default function StockControlReportsPage() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['stock-summary'],
    queryFn: getStockSummary,
    staleTime: 5 * 60 * 1000,
  });

  const { data: lowStockItems } = useQuery({
    queryKey: ['low-stock-items'],
    queryFn: () => stockControlApi.stockItems.getLowStock(),
    staleTime: 30 * 1000,
  });

  const { data: recentStockTakes } = useQuery({
    queryKey: ['recent-stock-takes'],
    queryFn: () => stockControlApi.stockTakes.list({ page_size: 5 }),
    staleTime: 30 * 1000,
  });

  const { data: monthlyStats } = useQuery({
    queryKey: ['monthly-stats-summary'],
    queryFn: () => stockControlApi.monthlyStats.list({ year: new Date().getFullYear() }),
    staleTime: 30 * 1000,
  });

  if (summaryLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Stock Control - Reports</h1>
        <p className="text-gray-600 mt-1">Generate and view stock reports</p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-6 border-l-4 border-l-blue-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600 uppercase">Total Items</p>
                <p className="text-2xl font-bold text-blue-600 mt-1">
                  {summary.total_items?.toLocaleString() || 0}
                </p>
              </div>
              <Box className="w-8 h-8 text-blue-200" />
            </div>
          </Card>

          <Card className="p-6 border-l-4 border-l-amber-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600 uppercase">Low Stock</p>
                <p className="text-2xl font-bold text-amber-600 mt-1">
                  {summary.low_stock_count || 0}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-amber-200" />
            </div>
          </Card>

          <Card className="p-6 border-l-4 border-l-red-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600 uppercase">Out of Stock</p>
                <p className="text-2xl font-bold text-red-600 mt-1">
                  {summary.out_of_stock_count || 0}
                </p>
              </div>
              <Activity className="w-8 h-8 text-red-200" />
            </div>
          </Card>

          <Card className="p-6 border-l-4 border-l-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600 uppercase">Stock Value</p>
                <p className="text-2xl font-bold text-green-600 mt-1">
                  R {(summary.total_value || 0).toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-green-200" />
            </div>
          </Card>
        </div>
      )}

      {/* Report Types */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Available Reports</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link href="/dashboard/admin/stock-control/reports/details">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <FileText className="w-10 h-10 text-blue-600 mb-3" />
              <h3 className="font-bold text-lg">Stock Details</h3>
              <p className="text-sm text-gray-600 mt-1">Full item listings with all details</p>
              <div className="mt-4 flex items-center text-blue-600 text-sm font-medium">
                View Report <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/admin/stock-control/reports/reorder">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <AlertTriangle className="w-10 h-10 text-amber-600 mb-3" />
              <h3 className="font-bold text-lg">Re-Order Report</h3>
              <p className="text-sm text-gray-600 mt-1">Items at or below reorder level</p>
              <div className="mt-4 flex items-center text-amber-600 text-sm font-medium">
                View Report <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/admin/stock-control/reports/variance">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <Activity className="w-10 h-10 text-red-600 mb-3" />
              <h3 className="font-bold text-lg">Variance Report</h3>
              <p className="text-sm text-gray-600 mt-1">Stock take count discrepancies</p>
              <div className="mt-4 flex items-center text-red-600 text-sm font-medium">
                View Report <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/admin/stock-control/reports/gross-profit">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <TrendingUp className="w-10 h-10 text-green-600 mb-3" />
              <h3 className="font-bold text-lg">Gross Profit</h3>
              <p className="text-sm text-gray-600 mt-1">Profitability analysis by item</p>
              <div className="mt-4 flex items-center text-green-600 text-sm font-medium">
                View Report <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/admin/stock-control/reports/department">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <FileText className="w-10 h-10 text-indigo-600 mb-3" />
              <h3 className="font-bold text-lg">Department</h3>
              <p className="text-sm text-gray-600 mt-1">Sales analysis by department</p>
              <div className="mt-4 flex items-center text-indigo-600 text-sm font-medium">
                View Report <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/admin/stock-control/reports/slow-movers">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <TrendingUp className="w-10 h-10 text-purple-600 mb-3 rotate-180" />
              <h3 className="font-bold text-lg">Slow Movers</h3>
              <p className="text-sm text-gray-600 mt-1">Items with low sales activity</p>
              <div className="mt-4 flex items-center text-purple-600 text-sm font-medium">
                View Report <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/admin/stock-control/reports/area">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <FileText className="w-10 h-10 text-cyan-600 mb-3" />
              <h3 className="font-bold text-lg">Area / Salesman</h3>
              <p className="text-sm text-gray-600 mt-1">Sales analysis by area and salesman</p>
              <div className="mt-4 flex items-center text-cyan-600 text-sm font-medium">
                View Report <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/admin/stock-control/reports/transactions">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <Activity className="w-10 h-10 text-teal-600 mb-3" />
              <h3 className="font-bold text-lg">Stock Transactions</h3>
              <p className="text-sm text-gray-600 mt-1">All stock movements, filterable by type/item/date</p>
              <div className="mt-4 flex items-center text-teal-600 text-sm font-medium">
                View Report <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/admin/stock-control/reports/valuation">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <DollarSign className="w-10 h-10 text-emerald-600 mb-3" />
              <h3 className="font-bold text-lg">Stock Valuation</h3>
              <p className="text-sm text-gray-600 mt-1">Parameterized valuation by code range and cost basis</p>
              <div className="mt-4 flex items-center text-emerald-600 text-sm font-medium">
                View Report <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/admin/stock-control/reports/received-returned">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <FileText className="w-10 h-10 text-rose-600 mb-3" />
              <h3 className="font-bold text-lg">Received / Returned</h3>
              <p className="text-sm text-gray-600 mt-1">Incoming stock and supplier returns together</p>
              <div className="mt-4 flex items-center text-rose-600 text-sm font-medium">
                View Report <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/admin/stock-control/transactions">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <FileText className="w-10 h-10 text-gray-600 mb-3" />
              <h3 className="font-bold text-lg">Stock Take Forms</h3>
              <p className="text-sm text-gray-600 mt-1">Print blank forms for physical counting (Transactions &gt; Stock Take)</p>
              <div className="mt-4 flex items-center text-gray-600 text-sm font-medium">
                Go to Stock Take <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Low Stock Preview */}
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Low Stock Items</h3>
          {lowStockItems && lowStockItems.results.length > 0 ? (
            <div className="space-y-3">
              {lowStockItems.results.slice(0, 5).map((item: any) => (
                <div key={item.stock_code} className="flex items-center justify-between py-2 border-b last:border-b-0">
                  <div>
                    <p className="font-mono font-medium">{item.stock_code}</p>
                    <p className="text-sm text-gray-500 truncate max-w-[200px]">{item.description}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-amber-600">{item.quantity_on_hand?.toFixed(0)}</p>
                    <p className="text-xs text-gray-500">of {item.reorder_quantity?.toFixed(0)}</p>
                  </div>
                </div>
              ))}
              <Link href="/dashboard/admin/stock-control/reports/reorder" className="block text-center text-blue-600 text-sm font-medium mt-2">
                View Full Report →
              </Link>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">No low stock items</p>
          )}
        </Card>

        {/* Recent Stock Takes */}
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Recent Stock Takes</h3>
          {recentStockTakes?.results && recentStockTakes.results.length > 0 ? (
            <div className="space-y-3">
              {recentStockTakes.results.map((take: any) => (
                <div key={take.id} className="flex items-center justify-between py-2 border-b last:border-b-0">
                  <div>
                    <p className="font-medium">Stock Take #{take.id}</p>
                    <p className="text-sm text-gray-500">
                      {take.stock_take_date ? new Date(take.stock_take_date).toLocaleDateString('en-ZA') : 'N/A'}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    take.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                    take.status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {take.status}
                  </span>
                </div>
              ))}
              <Link href="/dashboard/admin/stock-control/transactions/stocktake" className="block text-center text-blue-600 text-sm font-medium mt-2">
                View All Stock Takes →
              </Link>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">No recent stock takes</p>
          )}
        </Card>
      </div>
    </div>
  );
}
