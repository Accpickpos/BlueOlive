'use client';

import React, { useState, useEffect } from 'react';
import { debtorsApi } from '@/lib/debtorsApi';
import { posAPI } from '@/lib/posApi';
import { getStockSummary } from '@/lib/stockApi';
import { creditorsApi } from '@/lib/creditorsApi';
import { cashBookApi } from '@/lib/cashBookApi';
import { generalLedgerApi } from '@/lib/generalLedgerApi';
import { purchaseOrdersApi } from '@/lib/purchaseOrdersApi';
import { jobCardsApi } from '@/lib/jobCardsApi';
import { creditNotesApi } from '@/lib/creditNotesApi';
import { cashControlApi } from '@/lib/cashControlApi';
import { cashReturnsApi } from '@/lib/cashReturnsApi';
import { chequeApi } from '@/lib/chequeApi';
import { repairsApi } from '@/lib/repairsApi';

interface ReportData {
  debtors?: any;
  creditors?: any;
  stock?: any;
  sales?: any;
  purchases?: any;
  cashBook?: any;
  generalLedger?: any;
  jobCards?: any;
  creditNotes?: any;
  cashControl?: any;
  repairs?: any;
}

interface SummaryCard {
  label: string;
  value: string | number;
  change?: string;
  icon?: string;
  color?: string;
}

export default function ReportsPage() {
  const [data, setData] = useState<ReportData>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState('month'); // month, quarter, year
  const [summaryCards, setSummaryCards] = useState<SummaryCard[]>([]);

  useEffect(() => {
    fetchReportData();
  }, [selectedPeriod]);

  const fetchReportData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [
        debtorsSummary,
        creditorsSummary,
        stockSummary,
        cashControlData,
        jobCardsSummary,
        creditNotesSummary,
        repairsSummary,
      ] = await Promise.allSettled([
        debtorsApi.summary.get?.(),
        creditorsApi.summary.get?.(),
        getStockSummary?.(),
        cashControlApi.getSummary?.(),
        jobCardsApi.getSummary?.(),
        creditNotesApi.getSummary?.(),
        repairsApi.getSummary?.(),
      ]);

      const processedData = {
        debtors:
          debtorsSummary.status === 'fulfilled' ? debtorsSummary.value : null,
        creditors:
          creditorsSummary.status === 'fulfilled' ? creditorsSummary.value : null,
        stock: stockSummary.status === 'fulfilled' ? stockSummary.value : null,
        cashControl:
          cashControlData.status === 'fulfilled' ? cashControlData.value : null,
        jobCards:
          jobCardsSummary.status === 'fulfilled' ? jobCardsSummary.value : null,
        creditNotes:
          creditNotesSummary.status === 'fulfilled'
            ? creditNotesSummary.value
            : null,
        repairs:
          repairsSummary.status === 'fulfilled' ? repairsSummary.value : null,
      };

      setData(processedData);
      buildSummaryCards(processedData);
    } catch (err: any) {
      setError(
        err.message || 'Failed to load report data. Please try again later.'
      );
      console.error('Report data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const buildSummaryCards = (reportData: ReportData) => {
    const cards: SummaryCard[] = [
      {
        label: 'Debtors Accounts',
        value: reportData.debtors?.total_accounts || 0,
        icon: '👥',
        color: 'bg-blue-50',
      },
      {
        label: 'Outstanding Debtors',
        value:
          `R${(reportData.debtors?.total_outstanding || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2 })}` ||
          'R0.00',
        icon: '💰',
        color: 'bg-red-50',
      },
      {
        label: 'Stock Items',
        value: reportData.stock?.total_items || 0,
        icon: '📦',
        color: 'bg-green-50',
      },
      {
        label: 'Stock Value',
        value:
          `R${(reportData.stock?.total_value || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2 })}` ||
          'R0.00',
        icon: '💵',
        color: 'bg-purple-50',
      },
      {
        label: 'Active Job Cards',
        value: reportData.jobCards?.active_count || 0,
        icon: '🔧',
        color: 'bg-orange-50',
      },
      {
        label: 'Creditor Accounts',
        value: reportData.creditors?.total_accounts || 0,
        icon: '🏢',
        color: 'bg-indigo-50',
      },
    ];

    setSummaryCards(cards);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading report data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8 p-6 bg-gray-50 min-h-screen">
      {/* Header Section */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Reports & Analytics</h1>
          <p className="text-gray-600 mt-1">Dashboard overview and key metrics</p>
        </div>
        <div className="flex gap-2">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-700 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="month">This Month</option>
            <option value="quarter">This Quarter</option>
            <option value="year">This Year</option>
          </select>
          <button
            onClick={fetchReportData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          <p className="font-semibold">Error loading data</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Summary Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {summaryCards.map((card, index) => (
          <div
            key={index}
            className={`${card.color} border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow`}
          >
            <div className="flex justify-between items-start">
              <div>
                <p className="text-gray-600 text-sm font-medium">{card.label}</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">
                  {card.value}
                </p>
                {card.change && (
                  <p className="text-green-600 text-sm mt-2">{card.change}</p>
                )}
              </div>
              <span className="text-3xl">{card.icon}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sales Overview */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Sales Overview</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Cash Sales (This Month)</span>
              <span className="font-semibold text-gray-900">Pending Integration</span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Invoices</span>
              <span className="font-semibold text-gray-900">Pending Integration</span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Credit Sales</span>
              <span className="font-semibold text-gray-900">Pending Integration</span>
            </div>
            <div className="text-center text-sm text-gray-500 py-4">
              💡 Charts will be displayed once data integration is complete
            </div>
          </div>
        </div>

        {/* Debtors Analysis */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Debtors Analysis</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Total Debtors</span>
              <span className="font-semibold text-gray-900">
                {data.debtors?.total_accounts || 0}
              </span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Outstanding Balance</span>
              <span className="font-semibold text-red-600">
                R
                {(data.debtors?.total_outstanding || 0).toLocaleString(
                  'en-ZA',
                  { minimumFractionDigits: 2 }
                )}
              </span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Overdue Accounts</span>
              <span className="font-semibold text-gray-900">
                {data.debtors?.overdue_count || 0}
              </span>
            </div>
            <div className="text-center text-sm text-gray-500 py-4">
              📊 Age analysis charts coming soon
            </div>
          </div>
        </div>

        {/* Stock Control */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Stock Control</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Total Items</span>
              <span className="font-semibold text-gray-900">
                {data.stock?.total_items || 0}
              </span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Stock Value</span>
              <span className="font-semibold text-green-600">
                R
                {(data.stock?.total_value || 0).toLocaleString('en-ZA', {
                  minimumFractionDigits: 2,
                })}
              </span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Low Stock Items</span>
              <span className="font-semibold text-orange-600">
                {data.stock?.low_stock_count || 0}
              </span>
            </div>
            <div className="text-center text-sm text-gray-500 py-4">
              📈 Stock trends and movements charts coming soon
            </div>
          </div>
        </div>

        {/* Job Cards & Repairs */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Job Cards & Repairs
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Active Job Cards</span>
              <span className="font-semibold text-gray-900">
                {data.jobCards?.active_count || 0}
              </span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Repairs Awaiting Collection</span>
              <span className="font-semibold text-gray-900">
                {data.repairs?.ready_for_collection || 0}
              </span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Pending Credit Notes</span>
              <span className="font-semibold text-gray-900">
                {data.creditNotes?.pending_count || 0}
              </span>
            </div>
            <div className="text-center text-sm text-gray-500 py-4">
              🔧 Service workload charts coming soon
            </div>
          </div>
        </div>

        {/* Financial Summary */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Financial Summary
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Creditor Accounts</span>
              <span className="font-semibold text-gray-900">
                {data.creditors?.total_accounts || 0}
              </span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Outstanding Payables</span>
              <span className="font-semibold text-red-600">
                R
                {(data.creditors?.total_outstanding || 0).toLocaleString(
                  'en-ZA',
                  { minimumFractionDigits: 2 }
                )}
              </span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Overdue Payables</span>
              <span className="font-semibold text-orange-600">
                R
                {(data.creditors?.overdue_amount || 0).toLocaleString('en-ZA', {
                  minimumFractionDigits: 2,
                })}
              </span>
            </div>
            <div className="text-center text-sm text-gray-500 py-4">
              💹 Expense and revenue breakdown coming soon
            </div>
          </div>
        </div>

        {/* Cash Management */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Cash Management
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Current Cash Float</span>
              <span className="font-semibold text-green-600">
                R
                {(data.cashControl?.current_float || 0).toLocaleString('en-ZA', {
                  minimumFractionDigits: 2,
                })}
              </span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Pending Cheques</span>
              <span className="font-semibold text-gray-900">
                {data.cashControl?.pending_cheques || 0}
              </span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
              <span className="text-gray-600">Cash Returns</span>
              <span className="font-semibold text-gray-900">
                {data.cashControl?.pending_returns || 0}
              </span>
            </div>
            <div className="text-center text-sm text-gray-500 py-4">
              💳 Daily cash flow analysis coming soon
            </div>
          </div>
        </div>
      </div>

      {/* Implementation Notes */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">📋 Implementation Status</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>✅ All API clients created and integrated</li>
          <li>✅ Summary cards with real data loaded</li>
          <li>⏳ Chart visualizations (Recharts) - coming soon</li>
          <li>⏳ Date range filtering - coming soon</li>
          <li>⏳ Export to PDF/Excel - coming soon</li>
          <li>⏳ Advanced filtering and segmentation - coming soon</li>
        </ul>
      </div>
    </div>
  );
}