'use client';

import React, { useState } from 'react';
import { Download, BarChart3, TrendingUp, PieChart, CalendarDays, FileText } from 'lucide-react';

export default function CashBookReportsPage() {
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [loading, setLoading] = useState(false);

  const reports = [
    {
      id: 'transaction-summary',
      title: 'Transaction Summary',
      description: 'Summary of all cash transactions for the period',
      icon: <FileText className="w-8 h-8" />,
      color: 'blue',
    },
    {
      id: 'income-analysis',
      title: 'Income Analysis',
      description: 'Detailed analysis of income by category',
      icon: <TrendingUp className="w-8 h-8" />,
      color: 'green',
    },
    {
      id: 'expense-analysis',
      title: 'Expense Analysis',
      description: 'Detailed analysis of expenses by category',
      icon: <BarChart3 className="w-8 h-8" />,
      color: 'red',
    },
    {
      id: 'bank-reconciliation',
      title: 'Bank Reconciliation',
      description: 'Bank account reconciliation report',
      icon: <CalendarDays className="w-8 h-8" />,
      color: 'purple',
    },
    {
      id: 'cash-flow',
      title: 'Cash Flow Analysis',
      description: 'Cash flow trends and projections',
      icon: <PieChart className="w-8 h-8" />,
      color: 'orange',
    },
  ];

  const handleGenerateReport = async () => {
    if (!selectedReport) {
      alert('Please select a report type');
      return;
    }
    if (!dateFrom || !dateTo) {
      alert('Please select date range');
      return;
    }

    setLoading(true);
    // Simulate report generation
    setTimeout(() => {
      setLoading(false);
      alert(`Generated ${selectedReport} report from ${dateFrom} to ${dateTo}`);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-gray-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Cash Book Reports</h1>
            <p className="text-sm text-gray-500">Generate and download reports</p>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="max-w-5xl">
          {/* Date Range Selection */}
          <div className="bg-white rounded-lg border shadow-sm p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Report Parameters</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">From Date</label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">To Date</label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleGenerateReport}
                  disabled={loading || !selectedReport}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Download className="w-4 h-4" />
                  {loading ? 'Generating...' : 'Generate Report'}
                </button>
              </div>
            </div>
          </div>

          {/* Report Selection Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {reports.map((report) => (
              <button
                key={report.id}
                onClick={() => setSelectedReport(report.id)}
                className={`p-6 rounded-lg border-2 text-left transition-all ${
                  selectedReport === report.id
                    ? `border-blue-600 bg-blue-50 shadow-md`
                    : `border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm`
                }`}
              >
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-3 ${
                  selectedReport === report.id
                    ? 'bg-blue-600 text-white'
                    : `bg-${report.color}-50 text-${report.color}-600`
                }`}>
                  {report.icon}
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">{report.title}</h3>
                <p className="text-sm text-gray-600">{report.description}</p>
                {selectedReport === report.id && (
                  <div className="mt-3 flex items-center text-blue-600 text-sm font-medium">
                    ✓ Selected
                  </div>
                )}
              </button>
            ))}
          </div>

          {/* Report Preview */}
          {selectedReport && (
            <div className="mt-6 bg-white rounded-lg border shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                {reports.find((r) => r.id === selectedReport)?.title} Preview
              </h3>
              <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
                <p className="text-gray-600 mb-2">Report preview will be displayed here</p>
                <p className="text-sm text-gray-500">Select date range and click "Generate Report" to download</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
