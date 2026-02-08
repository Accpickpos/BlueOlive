'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ArrowLeft, Download } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api-config';

interface ExpenseCategory {
  id: number;
  category_name: string;
}

export default function ExpenseTaxAnalysis({ onBack }: { onBack: () => void }) {
  const [analysisType, setAnalysisType] = useState<'expenditure' | 'categories' | 'details'>(
    'expenditure'
  );
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [categories, setCategories] = useState<ExpenseCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [expenditureData, setExpenditureData] = useState<any>(null);
  const [categoriesData, setCategoriesData] = useState<any>(null);
  const [detailsData, setDetailsData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Fetch categories
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/creditors/expense-categories/`,
          {
            credentials: 'include',
          }
        );
        if (response.ok) {
          const data = await response.json();
          setCategories(data.results || data);
        }
      } catch (err) {
        console.error('Error fetching categories:', err);
      }
    };

    fetchCategories();
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('year', year.toString());
      params.append('month', month.toString());

      let url = '';
      if (analysisType === 'expenditure') {
        url = `${API_BASE_URL}/api/creditors/enquiries/expenditure_totals/?${params.toString()}`;
      } else if (analysisType === 'categories') {
        url = `${API_BASE_URL}/api/creditors/enquiries/expense_category_totals/?${params.toString()}`;
      } else if (analysisType === 'details') {
        if (!selectedCategory) {
          alert('Please select an expense category');
          setLoading(false);
          return;
        }
        url = `${API_BASE_URL}/api/creditors/enquiries/expense_category_details/?category_id=${selectedCategory}&${params.toString()}`;
      }

      const response = await fetch(url, {
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        if (analysisType === 'expenditure') {
          setExpenditureData(data);
          setCategoriesData(null);
          setDetailsData(null);
        } else if (analysisType === 'categories') {
          setCategoriesData(data);
          setExpenditureData(null);
          setDetailsData(null);
        } else {
          setDetailsData(data);
          setExpenditureData(null);
          setCategoriesData(null);
        }
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR',
    }).format(value);
  };

  const monthNames = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
  ];

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - 2 + i);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Expense & Tax Analysis</h1>
          <p className="text-gray-600">Expenditure and tax analysis by category</p>
        </div>
      </div>

      {/* Search Criteria */}
      <Card>
        <CardHeader>
          <CardTitle>Analysis Criteria</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Analysis Type */}
          <div>
            <label className="text-sm font-medium block mb-2">Analysis Type</label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <label className="flex items-center gap-2 p-3 border rounded hover:bg-gray-50 cursor-pointer">
                <input
                  type="radio"
                  value="expenditure"
                  checked={analysisType === 'expenditure'}
                  onChange={(e) => setAnalysisType(e.target.value as any)}
                  className="w-4 h-4"
                />
                <div>
                  <p className="font-medium text-sm">Expenditure Totals</p>
                  <p className="text-xs text-gray-600">Monthly expense and tax totals</p>
                </div>
              </label>
              <label className="flex items-center gap-2 p-3 border rounded hover:bg-gray-50 cursor-pointer">
                <input
                  type="radio"
                  value="categories"
                  checked={analysisType === 'categories'}
                  onChange={(e) => setAnalysisType(e.target.value as any)}
                  className="w-4 h-4"
                />
                <div>
                  <p className="font-medium text-sm">Category Totals</p>
                  <p className="text-xs text-gray-600">Totals by expense category</p>
                </div>
              </label>
              <label className="flex items-center gap-2 p-3 border rounded hover:bg-gray-50 cursor-pointer">
                <input
                  type="radio"
                  value="details"
                  checked={analysisType === 'details'}
                  onChange={(e) => setAnalysisType(e.target.value as any)}
                  className="w-4 h-4"
                />
                <div>
                  <p className="font-medium text-sm">Category Details</p>
                  <p className="text-xs text-gray-600">Detailed transactions by category</p>
                </div>
              </label>
            </div>
          </div>

          {/* Date Selection */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium block mb-2">Year</label>
              <Select value={year.toString()} onValueChange={(val: string) => setYear(parseInt(val))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {years.map((y) => (
                    <SelectItem key={y} value={y.toString()}>
                      {y}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium block mb-2">Month</label>
              <Select value={month.toString()} onValueChange={(val: string) => setMonth(parseInt(val))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {monthNames.map((m, idx) => (
                    <SelectItem key={idx + 1} value={(idx + 1).toString()}>
                      {m}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {analysisType === 'details' && (
              <div>
                <label className="text-sm font-medium block mb-2">Category</label>
                <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select category..." />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((cat) => (
                      <SelectItem key={cat.id} value={cat.id.toString()}>
                        {cat.category_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="flex flex-col justify-end">
              <Button onClick={handleSearch} disabled={loading}>
                {loading ? 'Loading...' : 'Search'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Expenditure Totals */}
      {analysisType === 'expenditure' && expenditureData && (
        <Card>
          <CardHeader>
            <CardTitle>Expenditure Totals - {monthNames[month - 1]} {year}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-600">Net Expenditure</p>
                <p className="text-2xl font-bold text-blue-700">
                  {formatCurrency(expenditureData.expenditure.total_exclusive)}
                </p>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg">
                <p className="text-sm text-gray-600">VAT Amount</p>
                <p className="text-2xl font-bold text-orange-700">
                  {formatCurrency(expenditureData.expenditure.total_vat)}
                </p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg border-2 border-green-300">
                <p className="text-sm text-gray-600">Total Expenditure</p>
                <p className="text-2xl font-bold text-green-700">
                  {formatCurrency(expenditureData.expenditure.total_inclusive)}
                </p>
              </div>
            </div>
            <div className="mt-4 p-4 bg-gray-50 rounded">
              <p className="text-sm text-gray-600">Transaction Count</p>
              <p className="text-xl font-bold">{expenditureData.transaction_count}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Category Totals */}
      {analysisType === 'categories' && categoriesData && (
        <>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <CardTitle>Expense Category Totals - {monthNames[month - 1]} {year}</CardTitle>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </CardHeader>
            <CardContent>
              {categoriesData.categories.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left py-3 px-4 font-semibold">Category</th>
                        <th className="text-right py-3 px-4 font-semibold">Net Amount</th>
                        <th className="text-right py-3 px-4 font-semibold">VAT</th>
                        <th className="text-right py-3 px-4 font-semibold">Total MTD</th>
                      </tr>
                    </thead>
                    <tbody>
                      {categoriesData.categories.map((cat: any, idx: number) => (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                          <td className="py-2 px-4">{cat.category_name}</td>
                          <td className="text-right py-2 px-4">
                            {formatCurrency(cat.mtd_exclusive)}
                          </td>
                          <td className="text-right py-2 px-4">
                            {formatCurrency(cat.mtd_vat)}
                          </td>
                          <td className="text-right py-2 px-4 font-semibold">
                            {formatCurrency(cat.mtd_inclusive)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="border-t-2 bg-gray-100 font-bold">
                        <td className="py-3 px-4">TOTALS</td>
                        <td className="text-right py-3 px-4">
                          {formatCurrency(categoriesData.grand_total.exclusive)}
                        </td>
                        <td className="text-right py-3 px-4">
                          {formatCurrency(categoriesData.grand_total.vat)}
                        </td>
                        <td className="text-right py-3 px-4">
                          {formatCurrency(categoriesData.grand_total.inclusive)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No category data found</p>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Category Details */}
      {analysisType === 'details' && detailsData && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>
                {detailsData.category.name} - {monthNames[month - 1]} {year}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-gray-600">Net Amount</p>
                  <p className="text-2xl font-bold text-blue-700">
                    {formatCurrency(detailsData.totals.exclusive)}
                  </p>
                </div>
                <div className="p-4 bg-orange-50 rounded-lg">
                  <p className="text-sm text-gray-600">VAT Amount</p>
                  <p className="text-2xl font-bold text-orange-700">
                    {formatCurrency(detailsData.totals.vat)}
                  </p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg border-2 border-green-300">
                  <p className="text-sm text-gray-600">Total Amount</p>
                  <p className="text-2xl font-bold text-green-700">
                    {formatCurrency(detailsData.totals.inclusive)}
                  </p>
                </div>
              </div>

              {detailsData.details.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left py-3 px-4 font-semibold">Date</th>
                        <th className="text-left py-3 px-4 font-semibold">Ref #</th>
                        <th className="text-left py-3 px-4 font-semibold">Supplier</th>
                        <th className="text-left py-3 px-4 font-semibold">Description</th>
                        <th className="text-right py-3 px-4 font-semibold">Net</th>
                        <th className="text-right py-3 px-4 font-semibold">VAT</th>
                        <th className="text-right py-3 px-4 font-semibold">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detailsData.details.map((detail: any, idx: number) => (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                          <td className="py-2 px-4">
                            {new Date(detail.date).toLocaleDateString()}
                          </td>
                          <td className="py-2 px-4 font-mono text-xs">
                            {detail.transaction_number}
                          </td>
                          <td className="py-2 px-4">{detail.supplier_name}</td>
                          <td className="py-2 px-4 text-xs">{detail.description}</td>
                          <td className="text-right py-2 px-4">
                            {formatCurrency(detail.amount_exclusive)}
                          </td>
                          <td className="text-right py-2 px-4">
                            {formatCurrency(detail.tax_amount)}
                          </td>
                          <td className="text-right py-2 px-4 font-semibold">
                            {formatCurrency(detail.amount_inclusive)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No transactions for this category</p>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
