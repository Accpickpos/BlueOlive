'use client';

import React, { useState } from 'react';
import {
  FileText,
  Download,
  Printer,
  ArrowLeft,
  BarChart3,
  Package,
  TrendingUp,
  Calendar,
} from 'lucide-react';
import Link from 'next/link';

interface ReportTemplate {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
}

export default function ReportsPage() {
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split('T')[0]
  );
  const [dateTo, setDateTo] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [loading, setLoading] = useState(false);

  const reports: ReportTemplate[] = [
    {
      id: 'outstanding-delivery',
      title: 'Outstanding by Delivery Date',
      description: 'View all outstanding orders organized by delivery date',
      icon: <Calendar className="w-6 h-6" />,
    },
    {
      id: 'outstanding-stock',
      title: 'Outstanding by Stock Items',
      description: 'View outstanding inventory organized by stock items',
      icon: <Package className="w-6 h-6" />,
    },
    {
      id: 'outstanding-supplier',
      title: 'Outstanding by Supplier',
      description: 'View outstanding orders organized by supplier',
      icon: <FileText className="w-6 h-6" />,
    },
    {
      id: 'back-orders',
      title: 'Back Orders',
      description: 'View all pending back orders and shortfalls',
      icon: <TrendingUp className="w-6 h-6" />,
    },
    {
      id: 'pre-orders',
      title: 'Pre-Orders',
      description: 'View all pre-orders and estimated delivery dates',
      icon: <FileText className="w-6 h-6" />,
    },
    {
      id: 'delivered',
      title: 'Delivered Orders',
      description: 'View all delivered and closed orders',
      icon: <BarChart3 className="w-6 h-6" />,
    },
  ];

  const handleGenerateReport = async () => {
    if (!selectedReport) return;

    setLoading(true);
    try {
      // Simulate report generation
      await new Promise((resolve) => setTimeout(resolve, 1000));
      // In a real application, this would call the API and download the report
      alert(`Report "${selectedReport}" would be generated from ${dateFrom} to ${dateTo}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4">
        <Link
          href="/dashboard/purchase-orders"
          className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Purchase Orders
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Purchase Orders Reports</h1>
        <p className="text-sm text-gray-500">
          Generate and view comprehensive purchase order reports
        </p>
      </div>

      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          {/* Date Range */}
          <div className="bg-white rounded-lg border shadow-sm p-4 mb-6">
            <h3 className="font-semibold text-gray-900 mb-4">Report Period</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  From Date
                </label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  To Date
                </label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Report Templates */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {reports.map((report) => (
              <button
                key={report.id}
                onClick={() => setSelectedReport(report.id)}
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  selectedReport === report.id
                    ? 'border-blue-500 bg-blue-50 shadow-md'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`p-2 rounded-lg ${
                      selectedReport === report.id
                        ? 'bg-blue-100 text-blue-600'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {report.icon}
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">
                      {report.title}
                    </h4>
                    <p className="text-xs text-gray-500 mt-1">
                      {report.description}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="bg-white rounded-lg border shadow-sm p-4">
            <div className="flex flex-col md:flex-row gap-4 items-end justify-between">
              <div className="text-sm text-gray-600">
                {selectedReport ? (
                  <p>
                    Selected:{' '}
                    <strong>
                      {reports.find((r) => r.id === selectedReport)?.title}
                    </strong>
                  </p>
                ) : (
                  <p className="text-gray-400">Select a report to continue</p>
                )}
              </div>
              <div className="flex gap-3 w-full md:w-auto">
                <Link
                  href="/dashboard/purchase-orders"
                  className="flex-1 md:flex-initial px-4 py-2 text-center border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-600 font-medium"
                >
                  Cancel
                </Link>
                <button
                  onClick={handleGenerateReport}
                  disabled={!selectedReport || loading}
                  className="flex-1 md:flex-initial flex items-center justify-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4" />
                      Generate Report
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Report Options */}
          {selectedReport && (
            <div className="mt-6 bg-white rounded-lg border shadow-sm p-4">
              <h3 className="font-semibold text-gray-900 mb-4">
                Report Options
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Include costs
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Export to PDF
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Export to Excel
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Print directly
                  </span>
                </label>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
