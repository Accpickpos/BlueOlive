'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Download, Printer } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api-config';

interface Creditor {
  account_number: number;
  name: string;
  balances: Record<string, number>;
}

interface ReportData {
  report_title: string;
  report_date: string;
  report_type: string;
  sequence: string;
  include_zero_balances: boolean;
  summary_totals: Record<string, number>;
  creditor_count: number;
  creditors: Creditor[];
}

export default function AgeAnalysisReport({ onBack }: { onBack: () => void }) {
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [reportType, setReportType] = useState('summary');
  const [sequence, setSequence] = useState('A');
  const [includeZero, setIncludeZero] = useState(true);
  const [printLastPaid, setPrintLastPaid] = useState(false);
  const [printBanking, setPrintBanking] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('report_type', reportType);
      params.append('sequence', sequence);
      params.append('include_zero', includeZero.toString());
      params.append('print_last_paid', printLastPaid.toString());
      params.append('print_banking', printBanking.toString());
      params.append('report_date', new Date().toISOString().split('T')[0]);

      const response = await fetch(
        `${API_BASE_URL}/api/creditors/reports/age_analysis/?${params.toString()}`,
        {
          credentials: 'include',
        }
      );

      if (response.ok) {
        const data = await response.json();
        setReportData(data);
      }
    } catch (err) {
      console.error('Error generating report:', err);
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

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Age Analysis Report</h1>
          <p className="text-gray-600">Outstanding balances by age period</p>
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
                  <option value="summary">Summary Only</option>
                  <option value="detailed">Detailed</option>
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

            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={includeZero}
                  onChange={(e) => setIncludeZero(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Include Zero Balances</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={printLastPaid}
                  onChange={(e) => setPrintLastPaid(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Print Last Paid & Terms Details</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={printBanking}
                  onChange={(e) => setPrintBanking(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Print Banking Details</span>
              </label>
            </div>

            <Button onClick={handleGenerate} disabled={loading} className="bg-purple-600 hover:bg-purple-700">
              {loading ? 'Generating...' : 'Generate Report'}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Report Header */}
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold">{reportData.report_title}</h2>
              <p className="text-gray-600 text-sm mt-1">
                Date: {reportData.report_date} | Type: {reportData.report_type} | Total Creditors: {reportData.creditor_count}
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => window.print()}>
                <Printer className="w-4 h-4 mr-2" />
                Print
              </Button>
              <Button variant="outline" onClick={() => setReportData(null)}>
                Generate New Report
              </Button>
            </div>
          </div>

          {/* Summary Totals */}
          <Card>
            <CardHeader>
              <CardTitle>Summary Totals</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(reportData.summary_totals).map(([period, value]) => (
                  <div key={period} className="text-center">
                    <p className="text-xs text-gray-600 uppercase">{period.replace('_', ' ')}</p>
                    <p className="text-lg font-bold">{formatCurrency(value)}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Detailed Creditors */}
          {reportData.creditors.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Creditor Details</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-100 border-b">
                      <tr>
                        <th className="text-left p-2">Account #</th>
                        <th className="text-left p-2">Name</th>
                        <th className="text-right p-2">Current</th>
                        <th className="text-right p-2">30 Days</th>
                        <th className="text-right p-2">60 Days</th>
                        <th className="text-right p-2">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reportData.creditors.map((creditor) => (
                        <tr key={creditor.account_number} className="border-b hover:bg-gray-50">
                          <td className="p-2">{creditor.account_number}</td>
                          <td className="p-2 font-medium">{creditor.name}</td>
                          <td className="text-right p-2">{formatCurrency(creditor.balances.current)}</td>
                          <td className="text-right p-2">{formatCurrency(creditor.balances['30_days'])}</td>
                          <td className="text-right p-2">{formatCurrency(creditor.balances['60_days'])}</td>
                          <td className="text-right p-2 font-semibold">{formatCurrency(creditor.balances.total)}</td>
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
