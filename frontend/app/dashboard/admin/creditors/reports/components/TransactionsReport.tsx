'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Printer } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api-config';

export default function TransactionsReport({ onBack }: { onBack: () => void }) {
  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [reportType, setReportType] = useState('detailed');

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('start_date', startDate);
      params.append('end_date', endDate);
      params.append('report_type', reportType);

      const response = await fetch(
        `${API_BASE_URL}/api/creditors/reports/transactions/?${params.toString()}`,
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
          <h1 className="text-3xl font-bold">Transactions Report</h1>
          <p className="text-gray-600">View transactions by date range</p>
        </div>
      </div>

      {!reportData ? (
        <Card>
          <CardHeader>
            <CardTitle>Report Criteria</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Start Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">End Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                />
              </div>
            </div>

            <div>
              <label className="text-sm font-medium">Report Type</label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
              >
                <option value="detailed">Detailed</option>
                <option value="totals_only">Totals Only</option>
              </select>
            </div>

            <Button onClick={handleGenerate} disabled={loading} className="bg-orange-600 hover:bg-orange-700">
              {loading ? 'Generating...' : 'Generate Report'}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold">{reportData.report_title}</h2>
              <p className="text-gray-600 text-sm">
                {reportData.period_from} to {reportData.period_to}
              </p>
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

          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Totals</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-gray-600">EXCLUSIVE VAT</p>
                  <p className="text-lg font-bold">{formatCurrency(reportData.totals.amount_vat_exclusive)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">VAT</p>
                  <p className="text-lg font-bold">{formatCurrency(reportData.totals.amount_vat)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">TOTAL</p>
                  <p className="text-lg font-bold">{formatCurrency(reportData.totals.amount_total)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">COUNT</p>
                  <p className="text-lg font-bold">{reportData.totals.transaction_count}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Transactions */}
          {reportData.transactions && reportData.transactions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Transaction Details</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-100 border-b">
                      <tr>
                        <th className="text-left p-2">Date</th>
                        <th className="text-left p-2">Supplier</th>
                        <th className="text-left p-2">Type</th>
                        <th className="text-right p-2">Amount</th>
                        <th className="text-right p-2">VAT</th>
                        <th className="text-right p-2">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reportData.transactions.map((txn: any, idx: number) => (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                          <td className="p-2">{txn.date}</td>
                          <td className="p-2">{txn.supplier}</td>
                          <td className="p-2">{txn.type}</td>
                          <td className="text-right p-2">{formatCurrency(txn.amount_vat_exclusive)}</td>
                          <td className="text-right p-2">{formatCurrency(txn.amount_vat)}</td>
                          <td className="text-right p-2 font-semibold">{formatCurrency(txn.amount_total)}</td>
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
