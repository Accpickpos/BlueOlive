'use client';

import React, { useState } from 'react';
import axios from 'axios';
import { Download, Filter, RotateCcw } from 'lucide-react';

interface ReportFilters {
  reportType: string;
  startDate?: string;
  endDate?: string;
  areaCode?: string;
  departmentNumber?: string;
  accountNumber?: string;
  shortName?: string;
  includeZeroBalance?: boolean;
  includeBlocked?: boolean;
  sortBy?: string;
  sequenceType?: 'alphabetical' | 'numerical';
  [key: string]: any;
}

const REPORT_TYPES = [
  {
    id: 'account_details',
    name: 'Account Details',
    description: 'List all debtors with account numbers, names, addresses, telephone, area, VAT and credit limits',
  },
  {
    id: 'age_analysis',
    name: 'Age Analysis',
    description: 'Outstanding balances by period (weekly/monthly) with payment info',
  },
  {
    id: 'statement',
    name: 'Statement Print',
    description: 'Current and historical statements with opening/closing balances',
  },
  {
    id: 'department_analysis',
    name: 'Department Analysis',
    description: 'Sales figures for departments (current, YTD, detailed, cash/account split)',
  },
  {
    id: 'transactions',
    name: 'Transactions',
    description: 'All account transactions (invoices, notes, receipts, interest, journals)',
  },
  {
    id: 'area_user',
    name: 'Area/User Report',
    description: 'Sales transactions and totals per area/salesman (YTD, detailed, masterfile)',
  },
  {
    id: 'address_labels',
    name: 'Address Labels',
    description: 'Address labels for statement envelopes (alphabetical/numeric order)',
  },
  {
    id: 'credit_limit_warning',
    name: 'Credit Limit Warning',
    description: 'Accounts exceeding credit limits or payment terms',
  },
  {
    id: 'account_performance',
    name: 'Account Performance',
    description: 'Sales and profit (MTD/YTD) by account with 12-month history',
  },
  {
    id: 'reprint_transaction',
    name: 'Reprint Transaction',
    description: 'Reprint invoices, credit notes and cash documents from current or archive',
  },
  {
    id: 'items_sold',
    name: 'Items Sold',
    description: 'Stock items sold to debtors (MTD, historical, average, by department/supplier)',
  },
];

export default function DebtorsReportsPage() {
  const [selectedReport, setSelectedReport] = useState<string>('account_details');
  const [filters, setFilters] = useState<ReportFilters>({
    reportType: 'account_details',
    includeZeroBalance: false,
    includeBlocked: false,
    sequenceType: 'alphabetical',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportData, setReportData] = useState<any>(null);

  const handleFilterChange = (key: string, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const generateReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        '/api/debtors/reports/generate/',
        { ...filters, reportType: selectedReport },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      setReportData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = async (format: 'pdf' | 'csv') => {
    try {
      const response = await axios.post(
        `/api/debtors/reports/generate/`,
        { ...filters, reportType: selectedReport, format },
        {
          responseType: 'blob',
        }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute(
        'download',
        `debtor_report_${selectedReport}_${new Date().toISOString().split('T')[0]}.${format}`
      );
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err: any) {
      setError('Failed to download report');
    }
  };

  const resetFilters = () => {
    setFilters({
      reportType: selectedReport,
      includeZeroBalance: false,
      includeBlocked: false,
      sequenceType: 'alphabetical',
    });
    setReportData(null);
  };

  const currentReport = REPORT_TYPES.find((r) => r.id === selectedReport);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Debtors - Reports</h1>
        <p className="text-gray-600">Generate comprehensive debtor reports with customizable filters</p>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Report Types Sidebar */}
        <div className="col-span-3">
          <div className="bg-white rounded-lg shadow p-4">
            <h2 className="text-lg font-semibold mb-4">Report Types</h2>
            <div className="space-y-2">
              {REPORT_TYPES.map((report) => (
                <button
                  key={report.id}
                  onClick={() => {
                    setSelectedReport(report.id);
                    resetFilters();
                  }}
                  className={`w-full text-left px-4 py-2 rounded transition ${
                    selectedReport === report.id
                      ? 'bg-blue-500 text-white'
                      : 'hover:bg-gray-100'
                  }`}
                  title={report.description}
                >
                  <div className="text-sm font-medium">{report.name}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="col-span-9 space-y-6">
          {/* Report Description */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900">{currentReport?.name}</h3>
            <p className="text-sm text-blue-800 mt-1">{currentReport?.description}</p>
          </div>

          {/* Filters Section */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Filter size={20} />
                Report Filters & Options
              </h3>
              <button
                onClick={resetFilters}
                className="text-gray-600 hover:text-gray-800 flex items-center gap-1"
              >
                <RotateCcw size={16} />
                Reset
              </button>
            </div>

            <div className="space-y-4">
              {/* Common Filters */}
              <div className="grid grid-cols-2 gap-4">
                {/* Sequence Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Sequence Type
                  </label>
                  <select
                    value={filters.sequenceType}
                    onChange={(e) =>
                      handleFilterChange('sequenceType', e.target.value)
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="alphabetical">Alphabetical</option>
                    <option value="numerical">Numerical</option>
                  </select>
                </div>

                {/* Area Code */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Area Code (Optional)
                  </label>
                  <input
                    type="text"
                    value={filters.areaCode || ''}
                    onChange={(e) =>
                      handleFilterChange('areaCode', e.target.value)
                    }
                    placeholder="Enter area code"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>

              {/* Report-Specific Filters */}
              {['age_analysis', 'statement', 'department_analysis', 'transactions', 'account_performance'].includes(selectedReport) && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={filters.startDate || ''}
                      onChange={(e) =>
                        handleFilterChange('startDate', e.target.value)
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={filters.endDate || ''}
                      onChange={(e) =>
                        handleFilterChange('endDate', e.target.value)
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
              )}

              {/* Account Number Range */}
              {['account_details', 'account_performance'].includes(selectedReport) && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Account Number
                    </label>
                    <input
                      type="text"
                      value={filters.accountNumber || ''}
                      onChange={(e) =>
                        handleFilterChange('accountNumber', e.target.value)
                      }
                      placeholder="Enter start account"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      End Account Number
                    </label>
                    <input
                      type="text"
                      value={filters.endAccountNumber || ''}
                      onChange={(e) =>
                        handleFilterChange('endAccountNumber', e.target.value)
                      }
                      placeholder="Enter end account"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
              )}

              {/* Department Number */}
              {['department_analysis', 'items_sold'].includes(selectedReport) && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Department Number (Optional)
                  </label>
                  <input
                    type="text"
                    value={filters.departmentNumber || ''}
                    onChange={(e) =>
                      handleFilterChange('departmentNumber', e.target.value)
                    }
                    placeholder="Enter department number"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              )}

              {/* Checkboxes */}
              <div className="space-y-3 border-t pt-4">
                {['age_analysis', 'account_details'].includes(selectedReport) && (
                  <>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={filters.includeZeroBalance}
                        onChange={(e) =>
                          handleFilterChange('includeZeroBalance', e.target.checked)
                        }
                        className="rounded"
                      />
                      <span className="text-sm">Include Zero Balance Accounts</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={filters.includeBlocked}
                        onChange={(e) =>
                          handleFilterChange('includeBlocked', e.target.checked)
                        }
                        className="rounded"
                      />
                      <span className="text-sm">Include Blocked Accounts</span>
                    </label>
                  </>
                )}

                {selectedReport === 'address_labels' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Number of Copies
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={filters.numberOfCopies || 1}
                      onChange={(e) =>
                        handleFilterChange('numberOfCopies', parseInt(e.target.value))
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                )}

                {selectedReport === 'statement' && (
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={filters.includeCodAccounts}
                      onChange={(e) =>
                        handleFilterChange('includeCodAccounts', e.target.checked)
                      }
                      className="rounded"
                    />
                    <span className="text-sm">Include COD Accounts with Zero Balance</span>
                  </label>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 mt-6 pt-4 border-t">
              <button
                onClick={generateReport}
                disabled={loading}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded font-medium transition"
              >
                {loading ? 'Generating...' : 'Generate Report'}
              </button>
              <button
                onClick={() => downloadReport('pdf')}
                disabled={!reportData || loading}
                className="flex items-center gap-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white px-4 py-2 rounded font-medium transition"
              >
                <Download size={18} />
                PDF
              </button>
              <button
                onClick={() => downloadReport('csv')}
                disabled={!reportData || loading}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded font-medium transition"
              >
                <Download size={18} />
                CSV
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
              <p className="font-semibold">Error</p>
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Report Preview */}
          {reportData && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Report Preview</h3>
              <div className="overflow-x-auto max-h-96 overflow-y-auto border rounded">
                <table className="w-full text-sm">
                  <thead className="bg-gray-100 sticky top-0">
                    <tr>
                      {reportData.columns?.map((col: string) => (
                        <th
                          key={col}
                          className="px-4 py-2 text-left font-semibold border-b"
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.rows?.map((row: any[], idx: number) => (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        {row.map((cell: any, cidx: number) => (
                          <td
                            key={cidx}
                            className="px-4 py-2"
                          >
                            {typeof cell === 'number'
                              ? cell.toLocaleString('en-US', {
                                  minimumFractionDigits: 2,
                                  maximumFractionDigits: 2,
                                })
                              : cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {reportData.summary && (
                <div className="mt-4 p-4 bg-gray-50 rounded border">
                  <h4 className="font-semibold mb-2">Summary</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {Object.entries(reportData.summary).map(([key, value]) => (
                      <div key={key}>
                        <span className="text-gray-600">{key}:</span>{' '}
                        <span className="font-semibold">
                          {typeof value === 'number'
                            ? (value as number).toLocaleString('en-US', {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                              })
                            : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
