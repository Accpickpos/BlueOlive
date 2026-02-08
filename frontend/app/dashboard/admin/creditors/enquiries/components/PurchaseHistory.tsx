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
import { ArrowLeft, Download, ArrowUpDown } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api-config';

interface PurchaseData {
  year: number;
  sorted_by: string;
  purchases: Array<{
    supplier_number: number;
    supplier_name: string;
    net_purchases: number;
    vat: number;
    total_purchases: number;
  }>;
  summary: {
    net_purchases: number;
    vat: number;
    total_purchases: number;
  };
  supplier_count: number;
}

export default function PurchaseHistory({ onBack }: { onBack: () => void }) {
  const [year, setYear] = useState(new Date().getFullYear());
  const [sortBy, setSortBy] = useState('supplier_number');
  const [purchaseData, setPurchaseData] = useState<PurchaseData | null>(null);
  const [loading, setLoading] = useState(false);

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - 2 + i);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/creditors/enquiries/purchase_history/?year=${year}&sort_by=${sortBy}`,
        {
          credentials: 'include',
        }
      );

      if (response.ok) {
        const data = await response.json();
        setPurchaseData(data);
      }
    } catch (err) {
      console.error('Error fetching purchase history:', err);
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

  const toggleSort = () => {
    const newSort = sortBy === 'supplier_number' ? 'total_purchases' : 'supplier_number';
    setSortBy(newSort);
  };

  useEffect(() => {
    // Auto-fetch when year or sort changes
    if (purchaseData) {
      handleSearch();
    }
  }, [year, sortBy]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Purchase History</h1>
          <p className="text-gray-600">Net stock purchases analysis by supplier</p>
        </div>
      </div>

      {/* Search Criteria */}
      <Card>
        <CardHeader>
          <CardTitle>Purchase History Criteria</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
              <label className="text-sm font-medium block mb-2">Sort By</label>
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="supplier_number">Supplier Number</SelectItem>
                  <SelectItem value="total_purchases">Total Purchases</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col justify-end gap-2">
              <Button onClick={handleSearch} disabled={loading}>
                {loading ? 'Loading...' : 'Search'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {purchaseData && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-gray-600">Total Suppliers</p>
                <p className="text-3xl font-bold text-blue-700">{purchaseData.supplier_count}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-gray-600">Net Purchases</p>
                <p className="text-2xl font-bold text-green-700">
                  {formatCurrency(purchaseData.summary.net_purchases)}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-gray-600">Total VAT</p>
                <p className="text-2xl font-bold text-orange-700">
                  {formatCurrency(purchaseData.summary.vat)}
                </p>
              </CardContent>
            </Card>
            <Card className="border-2 border-purple-300 bg-purple-50">
              <CardContent className="pt-6">
                <p className="text-sm text-gray-600">Total Purchases</p>
                <p className="text-2xl font-bold text-purple-700">
                  {formatCurrency(purchaseData.summary.total_purchases)}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Purchase Listing */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Purchase History - {purchaseData.year}</CardTitle>
                <p className="text-sm text-gray-600 mt-1">
                  Sorted by:{' '}
                  {sortBy === 'supplier_number'
                    ? 'Supplier Number (A-Z)'
                    : 'Total Purchases (High to Low)'}
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={toggleSort}
                  title="Toggle sort order"
                >
                  <ArrowUpDown className="w-4 h-4 mr-2" />
                  Toggle Sort
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Print
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {purchaseData.purchases.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left py-3 px-4 font-semibold">Supplier #</th>
                        <th className="text-left py-3 px-4 font-semibold">Supplier Name</th>
                        <th className="text-right py-3 px-4 font-semibold">Net Purchases</th>
                        <th className="text-right py-3 px-4 font-semibold">VAT</th>
                        <th className="text-right py-3 px-4 font-semibold">Total Purchases</th>
                        <th className="text-right py-3 px-4 font-semibold">% of Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {purchaseData.purchases.map((purchase, idx) => {
                        const percentage =
                          purchaseData.summary.total_purchases > 0
                            ? (
                                (purchase.total_purchases /
                                  purchaseData.summary.total_purchases) *
                                100
                              ).toFixed(2)
                            : '0.00';

                        return (
                          <tr key={idx} className="border-b hover:bg-gray-50">
                            <td className="py-2 px-4 font-medium">{purchase.supplier_number}</td>
                            <td className="py-2 px-4">{purchase.supplier_name}</td>
                            <td className="text-right py-2 px-4">
                              {formatCurrency(purchase.net_purchases)}
                            </td>
                            <td className="text-right py-2 px-4">
                              {formatCurrency(purchase.vat)}
                            </td>
                            <td className="text-right py-2 px-4 font-bold">
                              {formatCurrency(purchase.total_purchases)}
                            </td>
                            <td className="text-right py-2 px-4">
                              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-semibold">
                                {percentage}%
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                    <tfoot>
                      <tr className="border-t-2 bg-gray-100 font-bold">
                        <td colSpan={2} className="py-3 px-4">
                          TOTALS
                        </td>
                        <td className="text-right py-3 px-4">
                          {formatCurrency(purchaseData.summary.net_purchases)}
                        </td>
                        <td className="text-right py-3 px-4">
                          {formatCurrency(purchaseData.summary.vat)}
                        </td>
                        <td className="text-right py-3 px-4">
                          {formatCurrency(purchaseData.summary.total_purchases)}
                        </td>
                        <td className="text-right py-3 px-4">100%</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No purchase history found</p>
              )}
            </CardContent>
          </Card>

          {/* Top Suppliers */}
          {purchaseData.purchases.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Top 10 Suppliers by Purchase Amount</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {purchaseData.purchases.slice(0, 10).map((purchase, idx) => {
                    const percentage =
                      purchaseData.summary.total_purchases > 0
                        ? (
                            (purchase.total_purchases /
                              purchaseData.summary.total_purchases) *
                            100
                          ).toFixed(1)
                        : '0.0';

                    return (
                      <div key={idx}>
                        <div className="flex justify-between mb-1">
                          <p className="text-sm font-medium">
                            {idx + 1}. {purchase.supplier_name}
                          </p>
                          <div className="flex gap-4">
                            <p className="text-sm font-bold">
                              {formatCurrency(purchase.total_purchases)}
                            </p>
                            <p className="text-sm text-gray-600">{percentage}%</p>
                          </div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-6 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-green-500 to-green-600 h-full flex items-center justify-end pr-2 text-white text-xs font-semibold"
                            style={{
                              width: `${Math.max(
                                (purchase.total_purchases /
                                  purchaseData.purchases[0].total_purchases) *
                                  100,
                                5
                              )}%`,
                            }}
                          >
                            {parseFloat(percentage) > 5 && `${percentage}%`}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
