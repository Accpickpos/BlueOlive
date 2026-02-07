'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Printer } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api-config';

export default function ExpenseTaxReport({ onBack }: { onBack: () => void }) {
  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [reportType, setReportType] = useState('monthly_tax');
  const [sequence, setSequence] = useState('A');
  const [reportZero, setReportZero] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('report_type', reportType);
      params.append('sequence', sequence);
      params.append('report_zero', reportZero.toString());
      params.append('report_date', new Date().toISOString().split('T')[0]);

      const response = await fetch(
        `${API_BASE_URL}/api/creditors/reports/expense_tax/?${params.toString()}`,
        {
          credentials: 'include',
        }
      );

      if (response.ok) {
        const data = await response.json();
        setReportData(data);
      }
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' }).format(value);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Expense & Tax Report</h1>
          <p className="text-gray-600">Expense analysis and tax details</p>
        </div>
      </div>

      {!reportData ? (
        <Card>
          <CardHeader>
            <CardTitle>Report Options</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Report Type</label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                >
                  <option value="monthly_tax">Monthly & Tax Analysis</option>
                  <option value="ytd">Year to Date</option>
                  <option value="detailed">Detailed Transactions</option>
                  <option value="by_range">Categories by Range</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium">Sequence</label>
                <select
                  value={sequence}
                  onChange={(e) => setSequence(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                >
                  <option value="A">Alphabetical</option>
                  <option value="N">Numerical</option>
                </select>
              </div>
            </div>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={reportZero}
                onChange={(e) => setReportZero(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-sm">Report on Zero Expenses</span>
            </label>

            <Button onClick={handleGenerate} disabled={loading} className="bg-pink-600 hover:bg-pink-700">
              {loading ? 'Generating...' : 'Generate Report'}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold">{reportData.report_title}</h2>
              <p className="text-gray-600 text-sm">Type: {reportData.report_type}</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => window.print()}>
                <Printer className="w-4 h-4 mr-2" /> Print
              </Button>
              <Button variant="outline" onClick={() => setReportData(null)}>
                Generate New Report
              </Button>
            </div>
          </div>

          {/* Categories */}
          {reportData.categories && reportData.categories.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Expense Categories</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-100 border-b">
                      <tr>
                        <th className="text-left p-2">Category</th>
                        <th className="text-right p-2">Exclusive VAT</th>
                        <th className="text-right p-2">VAT</th>
                        <th className="text-right p-2">Total</th>
                        <th className="text-right p-2">Count</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reportData.categories.map((cat: any, idx: number) => (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                          <td className="p-2 font-medium">{cat.category_name}</td>
                          <td className="text-right p-2">{formatCurrency(cat.amount_vat_exclusive)}</td>
                          <td className="text-right p-2">{formatCurrency(cat.amount_vat)}</td>
                          <td className="text-right p-2 font-semibold">{formatCurrency(cat.amount_vat_inclusive)}</td>
                          <td className="text-right p-2">{cat.transaction_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
