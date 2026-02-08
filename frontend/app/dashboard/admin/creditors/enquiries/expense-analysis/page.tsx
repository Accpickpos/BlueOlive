'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader } from 'lucide-react';

export default function ExpenseAnalysisPage() {
  const [dateRange, setDateRange] = useState({
    from: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
    to: new Date().toISOString().split('T')[0],
  });
  const [page, setPage] = useState(1);

  const { data: expenseData, isLoading } = useQuery({
    queryKey: ['creditors-expense-analysis', dateRange, page],
    queryFn: () =>
      creditorsApi.transactions.list({
        transaction_type: 'INVOICE_EXPENSE',
        start_date: dateRange.from,
        end_date: dateRange.to,
        page,
        page_size: 50,
        ordering: '-transaction_date',
      }),
  });

  const { data: categoryBreakdown } = useQuery({
    queryKey: ['expense-category-breakdown', dateRange],
    queryFn: () =>
      creditorsApi.expenseCategories.list({
        start_date: dateRange.from,
        end_date: dateRange.to,
        page_size: 100,
      }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const totalExpenses = expenseData?.results?.reduce((sum: number, exp: any) => sum + (exp.amount || 0), 0) || 0;
  const totalTax = expenseData?.results?.reduce((sum: number, exp: any) => sum + (exp.tax_amount || 0), 0) || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Expense & Tax Analysis</h1>
        <p className="text-gray-600 mt-1">Analyze expenses and tax by category and supplier</p>
      </div>

      {/* Date Filter */}
      <Card className="p-4">
        <div className="flex gap-4 items-end">
          <div>
            <label className="block text-sm font-medium mb-1">From Date</label>
            <Input
              type="date"
              value={dateRange.from}
              onChange={(e) => setDateRange({ ...dateRange, from: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">To Date</label>
            <Input
              type="date"
              value={dateRange.to}
              onChange={(e) => setDateRange({ ...dateRange, to: e.target.value })}
            />
          </div>
          <Button className="bg-blue-600 hover:bg-blue-700">Generate Report</Button>
        </div>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6">
          <p className="text-xs text-gray-600 uppercase">Total Expenses</p>
          <p className="text-2xl font-bold text-blue-600 mt-2">
            R {totalExpenses.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
          </p>
          <p className="text-xs text-gray-600 mt-1">{expenseData?.results?.length || 0} invoices</p>
        </Card>

        <Card className="p-6">
          <p className="text-xs text-gray-600 uppercase">Total VAT</p>
          <p className="text-2xl font-bold text-amber-600 mt-2">
            R {totalTax.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
          </p>
          <p className="text-xs text-gray-600 mt-1">{((totalTax / totalExpenses) * 100).toFixed(1)}% of expenses</p>
        </Card>

        <Card className="p-6">
          <p className="text-xs text-gray-600 uppercase">Taxable Amount</p>
          <p className="text-2xl font-bold text-green-600 mt-2">
            R {(totalExpenses - totalTax).toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
          </p>
        </Card>
      </div>

      {/* Breakdown by Category */}
      {categoryBreakdown?.results && categoryBreakdown.results.length > 0 && (
        <Card className="p-6">
          <h2 className="text-lg font-bold mb-4">Expense by Category</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">Category</th>
                  <th className="px-4 py-3 text-right font-semibold">Count</th>
                  <th className="px-4 py-3 text-right font-semibold">Amount</th>
                  <th className="px-4 py-3 text-right font-semibold">VAT</th>
                  <th className="px-4 py-3 text-right font-semibold">% of Total</th>
                </tr>
              </thead>
              <tbody>
                {categoryBreakdown.results.map((cat: any) => (
                  <tr key={cat.id} className="border-b">
                    <td className="px-4 py-3 font-medium">{cat.name}</td>
                    <td className="px-4 py-3 text-right">{cat.transaction_count || 0}</td>
                    <td className="px-4 py-3 text-right font-bold">
                      R {cat.total_amount?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      R {cat.total_tax?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600">
                      {((cat.total_amount || 0) / totalExpenses * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Expenses Table */}
      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">Expense Invoices</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Invoice #</th>
                <th className="px-4 py-3 text-left font-semibold">Supplier</th>
                <th className="px-4 py-3 text-left font-semibold">Category</th>
                <th className="px-4 py-3 text-left font-semibold">Date</th>
                <th className="px-4 py-3 text-right font-semibold">Amount</th>
                <th className="px-4 py-3 text-right font-semibold">VAT</th>
              </tr>
            </thead>
            <tbody>
              {expenseData?.results?.map((exp: any) => (
                <tr key={exp.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{exp.invoice_number}</td>
                  <td className="px-4 py-3">{exp.supplier_name}</td>
                  <td className="px-4 py-3 text-xs text-gray-600">{exp.category_name}</td>
                  <td className="px-4 py-3 text-sm">
                    {new Date(exp.transaction_date).toLocaleDateString('en-ZA')}
                  </td>
                  <td className="px-4 py-3 text-right font-bold">
                    R {exp.amount?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3 text-right">
                    R {exp.tax_amount?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t">
          <p className="text-sm text-gray-600">
            Showing {expenseData?.results?.length || 0} of {expenseData?.count || 0} invoices
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={!expenseData?.previous}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={!expenseData?.next}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      </Card>

      {/* Export Options */}
      <div className="flex gap-2">
        <Button className="bg-blue-600 hover:bg-blue-700">Export to Excel</Button>
        <Button className="bg-green-600 hover:bg-green-700">Export to PDF</Button>
      </div>
    </div>
  );
}
