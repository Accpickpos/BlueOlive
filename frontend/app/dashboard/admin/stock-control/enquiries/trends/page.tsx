'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { getStockItems } from '@/lib/stockApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { 
  Loader, ArrowLeft, TrendingUp, TrendingDown, 
  Calendar, Package, BarChart3, Search
} from 'lucide-react';
import Link from 'next/link';

export default function TrendsPage() {
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedStockCode, setSelectedStockCode] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  // Fetch stock items for selection
  const { data: stockItems } = useQuery({
    queryKey: ['stock-items-trends'],
    queryFn: () => getStockItems({ page_size: 100 }),
    staleTime: 5 * 60 * 1000,
  });

  // Fetch monthly statistics
  const { data: monthlyStats, isLoading: statsLoading } = useQuery({
    queryKey: ['monthly-stats', selectedYear, selectedStockCode],
    queryFn: () => stockControlApi.monthlyStats.list({
      year: selectedYear,
      stock_item: selectedStockCode || undefined,
    }),
    staleTime: 30 * 1000,
  });

  // Handle search
  const handleSearch = async (value: string) => {
    setSearchTerm(value);
    if (value.length >= 2 && stockItems) {
      const filtered = stockItems.results.filter((item: any) =>
        item.stock_code.toLowerCase().includes(value.toLowerCase()) ||
        item.description.toLowerCase().includes(value.toLowerCase())
      );
      setSearchResults(filtered.slice(0, 10));
    } else {
      setSearchResults([]);
    }
  };

  const handleStockSelect = (code: string) => {
    setSelectedStockCode(code);
    setSearchTerm('');
    setSearchResults([]);
  };

  const clearStockFilter = () => {
    setSelectedStockCode('');
    setSearchTerm('');
    setSearchResults([]);
  };

  // Process monthly data for chart
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  
  const processMonthlyData = () => {
    if (!monthlyStats?.results) return [];
    
    return months.map((month, idx) => {
      const stat = monthlyStats.results.find((s: any) => s.month === idx + 1);
      return {
        month,
        quantitySold: stat?.quantity_sold || 0,
        totalRevenue: stat?.total_sales || 0,
        totalCost: stat?.total_cost || 0,
        profit: stat?.gross_profit || 0,
      };
    });
  };

  const monthlyData = processMonthlyData();
  
  const totalQuantity = monthlyData.reduce((sum, m) => sum + m.quantitySold, 0);
  const totalRevenue = monthlyData.reduce((sum, m) => sum + m.totalRevenue, 0);
  const totalCost = monthlyData.reduce((sum, m) => sum + m.totalCost, 0);
  const totalProfit = totalRevenue - totalCost;
  
  const avgMonthlySales = totalQuantity / 12;
  const avgMonthlyRevenue = totalRevenue / 12;

  const bestMonth = monthlyData.length > 0 ? monthlyData.reduce((best, current) => 
    current.quantitySold > best.quantitySold ? current : best
  , monthlyData[0]) : { month: 'N/A', quantitySold: 0 };

  // Find month with highest profit
  const bestProfitMonth = monthlyData.length > 0 ? monthlyData.reduce((best, current) => 
    current.profit > best.profit ? current : best
  , monthlyData[0]) : { month: 'N/A', profit: 0 };

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
          <h1 className="text-3xl font-bold">Sales Trends</h1>
          <p className="text-gray-600 mt-1">Analyze historical sales data and patterns</p>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Year</label>
            <Select value={selectedYear.toString()} onValueChange={(v) => setSelectedYear(parseInt(v))}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {years.map(year => (
                  <SelectItem key={year} value={year.toString()}>{year}</SelectItem>
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
                onChange={(e) => handleSearch(e.target.value)}
                className="pl-10"
              />
              {searchResults.length > 0 && (
                <div className="absolute z-10 w-full mt-1 border rounded-lg divide-y bg-white shadow-lg max-h-48 overflow-y-auto">
                  {searchResults.map((item: any) => (
                    <button
                      key={item.stock_code}
                      onClick={() => handleStockSelect(item.stock_code)}
                      className="w-full px-4 py-2 text-left hover:bg-gray-50"
                    >
                      <span className="font-mono">{item.stock_code}</span>
                      <span className="text-gray-500 ml-2">{item.description}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {selectedStockCode && (
            <Button variant="ghost" onClick={clearStockFilter} className="text-red-600">
              Clear Item Filter
            </Button>
          )}
        </div>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-6 border-l-4 border-l-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Quantity Sold</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">
                {totalQuantity.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <Package className="w-8 h-8 text-blue-200" />
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-l-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Revenue</p>
              <p className="text-2xl font-bold text-green-600 mt-1">
                R {totalRevenue.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-200" />
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-l-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Profit</p>
              <p className="text-2xl font-bold text-purple-600 mt-1">
                R {totalProfit.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <BarChart3 className="w-8 h-8 text-purple-200" />
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Avg Monthly Sales</p>
              <p className="text-2xl font-bold text-amber-600 mt-1">
                {avgMonthlySales.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <Calendar className="w-8 h-8 text-amber-200" />
          </div>
        </Card>
      </div>

      {/* Monthly Breakdown */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Monthly Breakdown</h2>
        
        {statsLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Month</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Quantity Sold</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Revenue</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Cost</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Profit</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Margin</th>
                  </tr>
                </thead>
                <tbody>
                  {monthlyData.map((data, idx) => {
                    const margin = data.totalRevenue > 0 ? (data.profit / data.totalRevenue) * 100 : 0;
                    const isBestMonth = data.month === bestMonth.month;
                    const isBestProfit = data.month === bestProfitMonth.month;
                    
                    return (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4 font-medium">
                          {data.month}
                          {isBestMonth && (
                            <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded">
                              Top Sales
                            </span>
                          )}
                          {isBestProfit && (
                            <span className="ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded">
                              Top Profit
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right">{data.quantitySold.toLocaleString('en-ZA')}</td>
                        <td className="py-3 px-4 text-right">R {data.totalRevenue.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                        <td className="py-3 px-4 text-right">R {data.totalCost.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                        <td className={`py-3 px-4 text-right font-medium ${data.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          R {data.profit.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div 
                                className={`h-full ${margin >= 30 ? 'bg-green-500' : margin >= 20 ? 'bg-amber-500' : 'bg-red-500'}`}
                                style={{ width: `${Math.min(margin, 100)}%` }}
                              />
                            </div>
                            <span className="text-sm w-12 text-right">{Number(margin).toFixed(1)}%</span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot>
                  <tr className="bg-gray-100 font-bold">
                    <td className="py-3 px-4">TOTAL</td>
                    <td className="py-3 px-4 text-right">{totalQuantity.toLocaleString('en-ZA')}</td>
                    <td className="py-3 px-4 text-right">R {totalRevenue.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                    <td className="py-3 px-4 text-right">R {totalCost.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                    <td className="py-3 px-4 text-right">R {totalProfit.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                    <td className="py-3 px-4 text-right">
                      {totalRevenue > 0 ? (Number(totalProfit) / Number(totalRevenue) * 100).toFixed(1) : 0}%
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            {/* Simple bar visualization */}
            <div className="mt-8">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Sales Volume by Month</h3>
              <div className="flex items-end gap-1 h-40">
                {monthlyData.map((data, idx) => {
                  const height = totalQuantity > 0 ? (data.quantitySold / totalQuantity) * 100 : 0;
                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center">
                      <div 
                        className="w-full bg-blue-500 hover:bg-blue-600 rounded-t transition-colors"
                        style={{ height: `${Math.max(height, 2)}%` }}
                        title={`${data.month}: ${data.quantitySold.toLocaleString()} units`}
                      />
                      <span className="text-xs text-gray-500 mt-1">{data.month}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </Card>

      {/* Insights */}
      <Card className="p-6 bg-blue-50">
        <h3 className="font-semibold mb-4">Key Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-start gap-3">
            <TrendingUp className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <p className="font-medium">Best Selling Month</p>
              <p className="text-sm text-gray-600">
                {bestMonth.month} with {bestMonth.quantitySold.toLocaleString()} units sold
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <BarChart3 className="w-5 h-5 text-green-600 mt-0.5" />
            <div>
              <p className="font-medium">Highest Profit Month</p>
              <p className="text-sm text-gray-600">
                {bestProfitMonth.month} with R {bestProfitMonth.profit.toLocaleString()} profit
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Package className="w-5 h-5 text-purple-600 mt-0.5" />
            <div>
              <p className="font-medium">Average Monthly Sales</p>
              <p className="text-sm text-gray-600">
                {avgMonthlySales.toLocaleString('en-ZA', { maximumFractionDigits: 0 })} units per month
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <TrendingDown className="w-5 h-5 text-amber-600 mt-0.5" />
            <div>
              <p className="font-medium">Average Monthly Revenue</p>
              <p className="text-sm text-gray-600">
                R {avgMonthlyRevenue.toLocaleString('en-ZA', { maximumFractionDigits: 0 })} per month
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
