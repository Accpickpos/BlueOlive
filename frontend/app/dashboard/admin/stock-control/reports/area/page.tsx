'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { 
  Loader, ArrowLeft, Users, Download, Search,
  TrendingUp, DollarSign, Percent
} from 'lucide-react';
import Link from 'next/link';

export default function AreaSalesmanReportPage() {
  const [year, setYear] = useState(new Date().getFullYear());
  const [selectedArea, setSelectedArea] = useState('');

  const years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i);

  // Placeholder data - in a real implementation this would connect to sales/debtors API
  // that tracks salesman and area performance
  const placeholderData = [
    { id: 1, area: 'North', salesman: 'John Smith', sales: 125000, transactions: 450, margin: 28.5 },
    { id: 2, area: 'North', salesman: 'Jane Doe', sales: 98000, transactions: 380, margin: 26.2 },
    { id: 3, area: 'South', salesman: 'Bob Wilson', sales: 87000, transactions: 320, margin: 24.8 },
    { id: 4, area: 'South', salesman: 'Alice Brown', sales: 76000, transactions: 290, margin: 25.1 },
    { id: 5, area: 'East', salesman: 'Charlie Davis', sales: 112000, transactions: 410, margin: 27.9 },
    { id: 6, area: 'West', salesman: 'Eva Martinez', sales: 94000, transactions: 350, margin: 26.5 },
    { id: 7, area: 'West', salesman: 'Frank Miller', sales: 68000, transactions: 250, margin: 23.2 },
  ];

  const filteredData = selectedArea 
    ? placeholderData.filter(d => d.area === selectedArea)
    : placeholderData;

  const areas = [...new Set(placeholderData.map(d => d.area))];

  const totals = filteredData.reduce((acc, d) => ({
    sales: acc.sales + d.sales,
    transactions: acc.transactions + d.transactions,
  }), { sales: 0, transactions: 0 });

  const avgMargin = filteredData.reduce((acc, d) => acc + d.margin, 0) / filteredData.length;

  const areaSummary = areas.map(area => {
    const areaData = placeholderData.filter(d => d.area === area);
    return {
      area,
      sales: areaData.reduce((sum, d) => sum + d.sales, 0),
      salesmen: areaData.length,
    };
  }).sort((a, b) => b.sales - a.sales);

  const exportToCSV = () => {
    const headers = ['Area', 'Salesman', 'Sales', 'Transactions', 'Margin %'];
    const rows = filteredData.map(d => [d.area, d.salesman, d.sales, d.transactions, d.margin.toFixed(2)]);

    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `salesman-analysis-${year}.csv`;
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
          <h1 className="text-3xl font-bold">Area / Salesman Report</h1>
          <p className="text-gray-600 mt-1">Sales analysis by area and salesman</p>
        </div>
      </div>

      {/* Info Banner */}
      <Card className="p-4 bg-blue-50 border-blue-200">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> This report uses placeholder data. In production, it would connect to the Debtors/Sales API 
          to track actual salesman and area performance from invoice data.
        </p>
      </Card>

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

          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Area</label>
            <Select value={selectedArea} onValueChange={setSelectedArea}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All Areas" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Areas</SelectItem>
                {areas.map(area => (
                  <SelectItem key={area} value={area}>{area}</SelectItem>
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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-xs text-gray-600 uppercase">Total Sales</p>
          <p className="text-xl font-bold">R {totals.sales.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-gray-600 uppercase">Transactions</p>
          <p className="text-xl font-bold">{totals.transactions.toLocaleString()}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-gray-600 uppercase">Salesmen</p>
          <p className="text-xl font-bold">{filteredData.length}</p>
        </Card>
        <Card className="p-4 border-l-4 border-l-blue-500">
          <div className="flex items-center gap-2">
            <Percent className="w-5 h-5 text-blue-600" />
            <div>
              <p className="text-xs text-gray-600 uppercase">Avg Margin</p>
              <p className="text-xl font-bold text-blue-600">{avgMargin.toFixed(1)}%</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Area Summary */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Sales by Area</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {areaSummary.map(area => (
            <div key={area.area} className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-5 h-5 text-gray-500" />
                <h4 className="font-medium">{area.area}</h4>
              </div>
              <p className="text-2xl font-bold">R {area.sales.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</p>
              <p className="text-sm text-gray-500">{area.salesmen} salesman{area.salesmen > 1 ? 'men' : ''}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Salesman Table */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Salesman Performance</h3>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="text-left py-3 px-3 font-medium text-gray-600">Area</th>
                <th className="text-left py-3 px-3 font-medium text-gray-600">Salesman</th>
                <th className="text-right py-3 px-3 font-medium text-gray-600">Sales</th>
                <th className="text-right py-3 px-3 font-medium text-gray-600">Transactions</th>
                <th className="text-right py-3 px-3 font-medium text-gray-600">Avg/Transaction</th>
                <th className="text-right py-3 px-3 font-medium text-gray-600">Margin</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.sort((a, b) => b.sales - a.sales).map((person) => (
                <tr key={person.id} className="border-b hover:bg-gray-50">
                  <td className="py-3 px-3">
                    <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-800">
                      {person.area}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-medium">{person.salesman}</td>
                  <td className="py-3 px-3 text-right font-medium">
                    R {person.sales.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
                  </td>
                  <td className="py-3 px-3 text-right">{person.transactions}</td>
                  <td className="py-3 px-3 text-right">
                    R {Math.round(person.sales / person.transactions).toLocaleString('en-ZA')}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      person.margin >= 28 ? 'bg-green-100 text-green-800' :
                      person.margin >= 25 ? 'bg-blue-100 text-blue-800' :
                      'bg-amber-100 text-amber-800'
                    }`}>
                      {person.margin.toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="font-bold bg-gray-50">
                <td className="py-3 px-3" colSpan={2}>TOTAL</td>
                <td className="py-3 px-3 text-right">R {totals.sales.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                <td className="py-3 px-3 text-right">{totals.transactions}</td>
                <td className="py-3 px-3 text-right">R {Math.round(totals.sales / totals.transactions).toLocaleString('en-ZA')}</td>
                <td className="py-3 px-3 text-right">{avgMargin.toFixed(1)}%</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </Card>
    </div>
  );
}
