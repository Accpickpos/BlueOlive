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

interface MonthlyData {
  category: {
    id: number;
    name: string;
  };
  year: number;
  monthly_data: Array<{
    month: string;
    month_number: number;
    exclusive: number;
    percentage: number;
  }>;
  year_total: number;
}

export default function MonthlyExpenseDetails({ onBack }: { onBack: () => void }) {
  const [categories, setCategories] = useState<ExpenseCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [monthlyData, setMonthlyData] = useState<MonthlyData | null>(null);
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
          if ((data.results || data).length > 0) {
            setSelectedCategory((data.results || data)[0].id.toString());
          }
        }
      } catch (err) {
        console.error('Error fetching categories:', err);
      }
    };

    fetchCategories();
  }, []);

  const handleSearch = async () => {
    if (!selectedCategory) {
      alert('Please select an expense category');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/creditors/enquiries/monthly_expense_details/?category_id=${selectedCategory}`,
        {
          credentials: 'include',
        }
      );

      if (response.ok) {
        const data = await response.json();
        setMonthlyData(data);
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

  // Simple bar chart visualization
  const maxValue = monthlyData?.year_total || 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Monthly Expense Details</h1>
          <p className="text-gray-600">Monthly expense analysis by category</p>
        </div>
      </div>

      {/* Category Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Expense Category</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
            <div className="flex flex-col justify-end">
              <Button onClick={handleSearch} disabled={loading}>
                {loading ? 'Loading...' : 'Analyze'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {monthlyData && (
        <>
          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle>{monthlyData.category.name} - Year {monthlyData.year}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-gray-600">Year Total</p>
                  <p className="text-2xl font-bold text-blue-700">
                    {formatCurrency(monthlyData.year_total)}
                  </p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="text-sm text-gray-600">Monthly Average</p>
                  <p className="text-2xl font-bold text-green-700">
                    {formatCurrency(monthlyData.year_total / 12)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Graphical Representation */}
          <Card>
            <CardHeader>
              <CardTitle>Monthly Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {monthlyData.monthly_data.map((month, idx) => (
                  <div key={idx}>
                    <div className="flex justify-between mb-1">
                      <p className="text-sm font-medium">{month.month}</p>
                      <div className="flex gap-4">
                        <p className="text-sm font-bold">{formatCurrency(month.exclusive)}</p>
                        <p className="text-sm text-gray-600">{month.percentage.toFixed(1)}%</p>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-6 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-blue-600 h-full flex items-center justify-end pr-2 text-white text-xs font-semibold"
                        style={{
                          width: maxValue > 0 ? `${(month.exclusive / maxValue) * 100}%` : '0%',
                        }}
                      >
                        {month.percentage > 10 && `${month.percentage.toFixed(0)}%`}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Detailed Table */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <CardTitle>Monthly Breakdown</CardTitle>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50">
                      <th className="text-left py-3 px-4 font-semibold">Month</th>
                      <th className="text-right py-3 px-4 font-semibold">Amount</th>
                      <th className="text-right py-3 px-4 font-semibold">% of Total</th>
                      <th className="text-right py-3 px-4 font-semibold">vs Average</th>
                    </tr>
                  </thead>
                  <tbody>
                    {monthlyData.monthly_data.map((month, idx) => {
                      const average = monthlyData.year_total / 12;
                      const variance = month.exclusive - average;
                      const variancePercent = (variance / average) * 100;

                      return (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                          <td className="py-2 px-4 font-medium">{month.month}</td>
                          <td className="text-right py-2 px-4">
                            {formatCurrency(month.exclusive)}
                          </td>
                          <td className="text-right py-2 px-4">
                            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-semibold">
                              {month.percentage.toFixed(1)}%
                            </span>
                          </td>
                          <td
                            className={`text-right py-2 px-4 font-semibold ${
                              variance > 0 ? 'text-red-600' : 'text-green-600'
                            }`}
                          >
                            {variance > 0 ? '+' : ''}{variancePercent.toFixed(0)}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                  <tfoot>
                    <tr className="border-t-2 bg-gray-100 font-bold">
                      <td className="py-3 px-4">TOTAL</td>
                      <td className="text-right py-3 px-4">
                        {formatCurrency(monthlyData.year_total)}
                      </td>
                      <td className="text-right py-3 px-4">100%</td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
