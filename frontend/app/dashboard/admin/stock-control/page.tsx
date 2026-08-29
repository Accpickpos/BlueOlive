'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getStockSummary, getTransactions } from '@/lib/stockApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Loader, Package, Tags, TrendingUp, History, 
  FileText, ArrowDown, ArrowUp, Box, 
  Settings, Activity, DollarSign, Layers, TrendingDown, Users
} from 'lucide-react';
import Link from 'next/link';

export default function StockControlOverviewPage() {
  const [activeTab, setActiveTab] = useState('maintenance');
  
  const { data: summary, isLoading } = useQuery({
    queryKey: ['stock-summary'],
    queryFn: () => getStockSummary(),
    staleTime: 5 * 60 * 1000,
  });

  const { data: recentTransactions } = useQuery({
    queryKey: ['stock-recent-transactions'],
    queryFn: () => getTransactions({ ordering: '-date', page_size: 5 }),
  });

  if (isLoading) {
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
        <h1 className="text-3xl font-bold">Stock Control Management</h1>
        <p className="text-gray-600 mt-1">
          Manage inventory, transactions, pricing, and stock analysis
        </p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600 uppercase">Total Items</p>
                <p className="text-3xl font-bold text-blue-600 mt-2">
                  {summary.total_items?.toLocaleString()}
                </p>
              </div>
              <Package className="w-10 h-10 text-blue-200" />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {summary.active_items} active, {summary.inactive_items} inactive
            </p>
          </Card>

          <Card className="p-6 border-l-4 border-l-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600 uppercase">Stock Value</p>
                <p className="text-3xl font-bold text-green-600 mt-2">
                  R {summary.total_value?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
                </p>
              </div>
              <DollarSign className="w-10 h-10 text-green-200" />
            </div>
          </Card>

          <Card className="p-6 border-l-4 border-l-amber-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600 uppercase">Low Stock Items</p>
                <p className="text-3xl font-bold text-amber-600 mt-2">
                  {summary.low_stock_count}
                </p>
              </div>
              <Activity className="w-10 h-10 text-amber-200" />
            </div>
          </Card>

          <Card className="p-6 border-l-4 border-l-red-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600 uppercase">Out of Stock</p>
                <p className="text-3xl font-bold text-red-600 mt-2">
                  {summary.out_of_stock_count}
                </p>
              </div>
              <Box className="w-10 h-10 text-red-200" />
            </div>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="maintenance">Maintenance</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="enquiries">Enquiries</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        <TabsContent value="maintenance" className="mt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { href: '/dashboard/admin/stock-control/maintenance/items', icon: Package, color: 'blue', title: 'Stock Items', desc: 'Create and maintain stock items' },
              { href: '/dashboard/admin/stock-control/maintenance', icon: Tags, color: 'purple', title: 'Special Deals', desc: 'Promotional pricing management' },
              { href: '/dashboard/admin/stock-control/maintenance/prices', icon: DollarSign, color: 'green', title: 'Prices', desc: 'Cost and selling price management' },
              { href: '/dashboard/admin/stock-control/maintenance/departments', icon: Layers, color: 'indigo', title: 'Sales Depts', desc: 'Sales department setup' },
              { href: '/dashboard/admin/stock-control/maintenance/areas', icon: TrendingUp, color: 'amber', title: 'Sales Areas', desc: 'Salesman and area management' },
              { href: '/dashboard/admin/stock-control/maintenance', icon: FileText, color: 'cyan', title: 'Contract Pricing', desc: 'Debtor-specific pricing' },
              { href: '/dashboard/admin/stock-control/maintenance/shrink-wraps', icon: Box, color: 'pink', title: 'Shrink Wraps', desc: 'Bulk to unit relationships' },
              { href: '/dashboard/admin/stock-control/maintenance', icon: Settings, color: 'gray', title: 'Packs/Bundles', desc: 'Finished goods and recipes' },
            ].map((item) => (
              <Link key={item.title} href={item.href}>
                <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
                  <item.icon className={`w-8 h-8 text-${item.color}-600 mb-3`} />
                  <h3 className="font-bold">{item.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{item.desc}</p>
                </Card>
              </Link>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="transactions" className="mt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { href: '/dashboard/admin/stock-control/transactions', icon: ArrowDown, color: 'green', title: 'Incoming Stock', desc: 'Goods received notes' },
              { href: '/dashboard/admin/stock-control/transactions', icon: ArrowUp, color: 'red', title: 'Stock Returns', desc: 'Returns to suppliers' },
              { href: '/dashboard/admin/stock-control/transactions/stocktake', icon: Activity, color: 'amber', title: 'Stock Take', desc: 'Physical inventory count' },
              { href: '/dashboard/admin/stock-control/transactions', icon: Settings, color: 'blue', title: 'Manufacture', desc: 'Pack/bundle manufacturing' },
            ].map((item) => (
              <Link key={item.title} href={item.href}>
                <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
                  <item.icon className={`w-8 h-8 text-${item.color}-600 mb-3`} />
                  <h3 className="font-bold">{item.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{item.desc}</p>
                </Card>
              </Link>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="enquiries" className="mt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { href: '/dashboard/admin/stock-control/enquiries/item', icon: Package, color: 'blue', title: 'Individual Item', desc: 'Stock item details' },
              { href: '/dashboard/admin/stock-control/enquiries/valuation', icon: DollarSign, color: 'green', title: 'Stock Valuation', desc: 'Current stock value' },
              { href: '/dashboard/admin/stock-control/enquiries/movements', icon: TrendingUp, color: 'purple', title: 'Stock Movements', desc: 'Transaction history' },
              { href: '/dashboard/admin/stock-control/enquiries/trends', icon: History, color: 'amber', title: 'Sales Trends', desc: 'Historical analysis' },
            ].map((item) => (
              <Link key={item.href} href={item.href}>
                <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
                  <item.icon className={`w-8 h-8 text-${item.color}-600 mb-3`} />
                  <h3 className="font-bold">{item.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{item.desc}</p>
                </Card>
              </Link>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="reports" className="mt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { href: '/dashboard/admin/stock-control/reports/details', icon: FileText, color: 'blue', title: 'Stock Details', desc: 'Full item listings' },
              { href: '/dashboard/admin/stock-control/reports/variance', icon: Activity, color: 'red', title: 'Stock Variance', desc: 'Count discrepancies' },
              { href: '/dashboard/admin/stock-control/reports/reorder', icon: Box, color: 'amber', title: 'Re-Order Report', desc: 'Low stock alerts' },
              { href: '/dashboard/admin/stock-control/reports/gross-profit', icon: DollarSign, color: 'green', title: 'Gross Profit', desc: 'Profitability analysis' },
              { href: '/dashboard/admin/stock-control/reports/slow-movers', icon: TrendingDown, color: 'purple', title: 'Slow Movers', desc: 'Low sales activity' },
              { href: '/dashboard/admin/stock-control/reports/department', icon: Layers, color: 'indigo', title: 'Department', desc: 'Sales by department' },
              { href: '/dashboard/admin/stock-control/reports/area', icon: Users, color: 'cyan', title: 'Area/Salesman', desc: 'Sales by area' },
            ].map((item) => (
              <Link key={item.href} href={item.href}>
                <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
                  <item.icon className={`w-8 h-8 text-${item.color}-600 mb-3`} />
                  <h3 className="font-bold">{item.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{item.desc}</p>
                </Card>
              </Link>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Recent Activity */}
      {recentTransactions?.results && recentTransactions.results.length > 0 && (
        <Card className="p-6">
          <h2 className="text-lg font-bold mb-4">Recent Stock Activity</h2>
          <div className="space-y-3">
            {recentTransactions.results.map((transaction: any) => (
              <div key={transaction.id} className="flex items-center justify-between py-2 border-b last:border-b-0">
                <div className="flex items-center gap-3">
                  {transaction.transaction_type === 'INCOMING' ? (
                    <ArrowDown className="w-4 h-4 text-green-600" />
                  ) : transaction.transaction_type === 'RETURN' ? (
                    <ArrowUp className="w-4 h-4 text-red-600" />
                  ) : (
                    <Package className="w-4 h-4 text-blue-600" />
                  )}
                  <div>
                    <p className="font-medium">{transaction.stock_code}</p>
                    <p className="text-xs text-gray-600">
                      {new Date(transaction.date).toLocaleDateString('en-ZA')}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold">
                    {transaction.quantity > 0 ? '+' : ''}{transaction.quantity}
                  </p>
                  <p className="text-xs text-gray-500">
                    {transaction.transaction_type}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
