'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import {
  Loader, ArrowLeft, Layers, Download,
  TrendingUp, Percent
} from 'lucide-react';
import Link from 'next/link';
import { Pagination } from '@/components/ui/pagination';

export default function DepartmentAnalysisPage() {
  const [page, setPage] = useState(1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [selectedDepartment, setSelectedDepartment] = useState('');

  const years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i);

  // Backend-aggregated sales/cost/profit by department — was previously
  // computed client-side by joining monthlyStats against a full 1000-item
  // stock-items fetch, reading total_sales/total_cost/gross_profit fields
  // that don't exist on StockMonthlyStatisticSerializer (real fields:
  // value_sold/profit_value; cost is derived as value_sold - profit_value),
  // so every number in this report rendered as R0 regardless of real data.
  const { data: rows, isLoading: statsLoading } = useQuery({
    queryKey: ['stats-by-department', year],
    queryFn: () => stockControlApi.enquiries.statsByDepartment({ year }),
    staleTime: 30 * 1000,
  });

  const departments = (rows || []).map((r) => ({ id: r.department_id, name: r.department_name }));

  const byDepartment = (rows || [])
    .filter((r) => !selectedDepartment || r.department_name === selectedDepartment)
    .map((r) => ({
      name: r.department_name,
      totalSales: Number(r.total_sales || 0),
      totalCost: Number(r.total_cost || 0),
      totalProfit: Number(r.total_profit || 0),
      quantitySold: Number(r.total_quantity || 0),
      margin: r.margin_pct,
      itemCount: r.item_count,
    }));

  const totals = byDepartment.length
    ? byDepartment.reduce(
        (acc, d) => ({
          sales: acc.sales + d.totalSales,
          cost: acc.cost + d.totalCost,
          profit: acc.profit + d.totalProfit,
          quantity: acc.quantity + d.quantitySold,
          departmentCount: acc.departmentCount + 1,
          margin: 0,
        }),
        { sales: 0, cost: 0, profit: 0, quantity: 0, departmentCount: 0, margin: 0 }
      )
    : null;
  if (totals) totals.margin = totals.sales > 0 ? (totals.profit / totals.sales) * 100 : 0;

  const paginatedDepts = byDepartment.slice((page - 1) * 10, page * 10);

  const exportToCSV = () => {
    const headers = ['Department', 'Item Count', 'Qty Sold', 'Total Sales', 'Total Cost', 'Gross Profit', 'Margin %'];
    const rows = byDepartment.map((dept: any) => [
      dept.name,
      dept.itemCount,
      dept.quantitySold,
      dept.totalSales.toFixed(2),
      dept.totalCost.toFixed(2),
      dept.totalProfit.toFixed(2),
      dept.margin.toFixed(2)
    ]);

    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `department-analysis-${year}.csv`;
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
          <h1 className="text-3xl font-bold">Department Analysis</h1>
          <p className="text-gray-600 mt-1">Sales analysis by department</p>
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
            <label className="text-sm font-medium text-gray-700 mb-1 block">Department</label>
            <Select value={selectedDepartment} onValueChange={(v) => { setSelectedDepartment(v); setPage(1); }}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="All Departments" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Departments</SelectItem>
                {departments.map((dept: any) => (
                  <SelectItem key={dept.id} value={dept.name}>{dept.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

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
            <p className="text-xs text-gray-600 uppercase">Departments</p>
            <p className="text-xl font-bold">{totals.departmentCount}</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-gray-600 uppercase">Total Sales</p>
            <p className="text-xl font-bold">R {totals.sales.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-gray-600 uppercase">Total Cost</p>
            <p className="text-xl font-bold text-red-600">R {totals.cost.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</p>
          </Card>
          <Card className="p-4 border-l-4 border-l-green-500">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-xs text-gray-600 uppercase">Gross Profit</p>
                <p className="text-xl font-bold text-green-600">R {totals.profit.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4 border-l-4 border-l-blue-500">
            <div className="flex items-center gap-2">
              <Percent className="w-5 h-5 text-blue-600" />
              <div>
                <p className="text-xs text-gray-600 uppercase">Avg Margin</p>
                <p className="text-xl font-bold text-blue-600">{totals.margin.toFixed(1)}%</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Department Table */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Sales by Department</h3>
        
        {statsLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : paginatedDepts.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-left py-3 px-3 font-medium text-gray-600">Department</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Items</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Qty Sold</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Total Sales</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Total Cost</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Gross Profit</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">% of Total</th>
                    <th className="text-right py-3 px-3 font-medium text-gray-600">Margin</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedDepts.map((dept: any) => {
                    const pctOfTotal = totals ? (dept.totalSales / totals.sales) * 100 : 0;
                    return (
                      <tr key={dept.name} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-3 font-medium">
                          <div className="flex items-center gap-2">
                            <Layers className="w-4 h-4 text-gray-400" />
                            {dept.name}
                          </div>
                        </td>
                        <td className="py-3 px-3 text-right">{dept.itemCount}</td>
                        <td className="py-3 px-3 text-right">{dept.quantitySold.toLocaleString('en-ZA')}</td>
                        <td className="py-3 px-3 text-right">R {dept.totalSales.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                        <td className="py-3 px-3 text-right text-red-600">R {dept.totalCost.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                        <td className="py-3 px-3 text-right font-medium text-green-600">
                          R {dept.totalProfit.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
                        </td>
                        <td className="py-3 px-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div className="h-full bg-blue-600" style={{ width: `${pctOfTotal}%` }} />
                            </div>
                            <span className="text-sm">{pctOfTotal.toFixed(1)}%</span>
                          </div>
                        </td>
                        <td className="py-3 px-3 text-right">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            dept.margin >= 30 ? 'bg-green-100 text-green-800' :
                            dept.margin >= 20 ? 'bg-amber-100 text-amber-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {dept.margin.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {byDepartment.length > 10 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <p className="text-sm text-gray-600">
                  Showing {((page - 1) * 10) + 1} to {Math.min(page * 10, byDepartment.length)} of {byDepartment.length} departments
                </p>
                <Pagination
                  currentPage={page}
                  totalPages={Math.ceil(byDepartment.length / 10)}
                  onPageChange={setPage}
                />
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <Layers className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 text-lg">No department data available for {year}</p>
          </div>
        )}
      </Card>
    </div>
  );
}
