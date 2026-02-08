'use client';

import React, { useState } from 'react';
import {
  FileText,
  Download,
  Calendar,
  Filter,
  BarChart3,
  ArrowLeft,
} from 'lucide-react';
import Link from 'next/link';

type ReportType =
  | 'outstanding-delivery'
  | 'outstanding-stock'
  | 'outstanding-supplier'
  | 'back-orders'
  | 'pre-orders'
  | 'delivered';

const REPORT_DEFINITIONS = {
  'outstanding-delivery': {
    title: 'Outstanding Orders by Delivery Date',
    description:
      'Purchase orders not yet fully received, grouped by delivery date',
    icon: '📅',
  },
  'outstanding-stock': {
    title: 'Outstanding Stock Items',
    description: 'Outstanding stock items across all purchase orders',
    icon: '📦',
  },
  'outstanding-supplier': {
    title: 'Outstanding Orders by Supplier',
    description:
      'Outstanding purchase orders grouped by supplier with totals',
    icon: '🏢',
  },
  'back-orders': {
    title: 'Back Orders Report',
    description: 'Orders with back-ordered items and expected delivery dates',
    icon: '⏳',
  },
  'pre-orders': {
    title: 'Pre-Orders Report',
    description: 'Items not yet in stock that have been pre-ordered',
    icon: '🔄',
  },
  delivered: {
    title: 'Delivered Orders Report',
    description: 'Recently delivered orders and their receipt details',
    icon: '✓',
  },
};

export default function PurchaseOrdersReportsPage() {
  const [selectedReport, setSelectedReport] = useState<ReportType | null>(null);
  const [filters, setFilters] = useState({
    date_from: new Date().toISOString().split('T')[0],
    date_to: new Date().toISOString().split('T')[0],
    supplier: '',
  });
  const [loading, setLoading] = useState(false);
  const [generatedReport, setGeneratedReport] = useState<any>(null);

  const handleGenerateReport = async () => {
    if (!selectedReport) return;

    setLoading(true);
    // Simulated report generation - replace with actual API call
    setTimeout(() => {
      setGeneratedReport({
        type: selectedReport,
        generated_at: new Date().toISOString(),
        record_count: 12,
        total_value: 85500.5,
      });
      setLoading(false);
    }, 1000);
  };

  const handleExport = (format: 'pdf' | 'excel') => {
    if (!generatedReport) return;
    // Logic to export report
    console.log(`Exporting ${format}...`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4">
        <Link
          href="/dashboard/admin/purchase-orders"
          className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Purchase Orders
        </Link>
        <h1 className="text-xl font-bold text-gray-900">
          Purchase Orders Reports
        </h1>
        <p className="text-sm text-gray-500">
          Generate reports on purchase orders, deliveries, and stock status
        </p>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Report Selection */}
          <div className="lg:col-span-1">
            <h2 className="text-lg font-bold text-gray-900 mb-4">
              Available Reports
            </h2>
            <div className="space-y-3">
              {(
                Object.entries(REPORT_DEFINITIONS) as [
                  ReportType,
                  (typeof REPORT_DEFINITIONS)[ReportType],
                ][]
              ).map(([reportType, report]) => (
                <button
                  key={reportType}
                  onClick={() => setSelectedReport(reportType)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition ${
                    selectedReport === reportType
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xl">{report.icon}</span>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 text-sm">
                        {report.title}
                      </h3>
                      <p className="text-xs text-gray-500 mt-1">
                        {report.description}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Report Configuration & Results */}
          <div className="lg:col-span-2">
            {selectedReport ? (
              <>
                {/* Configuration */}
                <div className="bg-white rounded-lg border shadow-sm p-6 mb-6">
                  <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <Filter className="w-5 h-5" />
                    Report Filters
                  </h3>

                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          From Date
                        </label>
                        <input
                          type="date"
                          value={filters.date_from}
                          onChange={(e) =>
                            setFilters({ ...filters, date_from: e.target.value })
                          }
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          To Date
                        </label>
                        <input
                          type="date"
                          value={filters.date_to}
                          onChange={(e) =>
                            setFilters({ ...filters, date_to: e.target.value })
                          }
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>

                    {['outstanding-supplier', 'outstanding-delivery'].includes(
                      selectedReport
                    ) && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Supplier (Optional)
                        </label>
                        <input
                          type="text"
                          placeholder="Leave blank for all suppliers"
                          value={filters.supplier}
                          onChange={(e) =>
                            setFilters({ ...filters, supplier: e.target.value })
                          }
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    )}

                    <button
                      onClick={handleGenerateReport}
                      disabled={loading}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium"
                    >
                      {loading ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <BarChart3 className="w-4 h-4" />
                          Generate Report
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Report Results */}
                {generatedReport && (
                  <div className="bg-white rounded-lg border shadow-sm p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                        <FileText className="w-5 h-5" />
                        Report Results
                      </h3>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleExport('pdf')}
                          className="flex items-center gap-2 px-3 py-2 border border-red-300 text-red-600 hover:bg-red-50 rounded-lg text-sm font-medium"
                        >
                          <Download className="w-4 h-4" />
                          PDF
                        </button>
                        <button
                          onClick={() => handleExport('excel')}
                          className="flex items-center gap-2 px-3 py-2 border border-green-300 text-green-600 hover:bg-green-50 rounded-lg text-sm font-medium"
                        >
                          <Download className="w-4 h-4" />
                          Excel
                        </button>
                      </div>
                    </div>

                    <div className="space-y-3 border-t pt-4">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Records Included</span>
                        <span className="font-bold text-gray-900">
                          {generatedReport.record_count}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Total Value (excl VAT)</span>
                        <span className="font-bold text-gray-900">
                          R{' '}
                          {generatedReport.total_value.toLocaleString('en-ZA', {
                            minimumFractionDigits: 2,
                          })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Generated At</span>
                        <span className="font-bold text-gray-900">
                          {new Date(
                            generatedReport.generated_at
                          ).toLocaleString('en-ZA')}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-white rounded-lg border shadow-sm p-12 text-center">
                <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 font-medium">
                  Select a report to get started
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  Choose from the available reports on the left
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
