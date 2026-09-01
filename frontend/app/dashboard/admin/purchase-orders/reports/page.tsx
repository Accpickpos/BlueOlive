'use client';

import React, { useState } from 'react';
import {
  FileText,
  Download,
  ArrowLeft,
  BarChart3,
  Package,
  TrendingUp,
  Calendar,
  Truck,
} from 'lucide-react';
import Link from 'next/link';
import purchaseOrdersApi from '@/lib/purchaseOrdersApi';
import { getApiErrorMessage } from '@/lib/api';
import { OrderStatusBadge } from '@/components/purchase-orders/common/OrderStatusBadge';

interface ReportTemplate {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
}

const REPORTS: ReportTemplate[] = [
  {
    id: 'outstanding-delivery',
    title: 'Outstanding by Delivery Date',
    description: 'All outstanding orders within the selected date range',
    icon: <Calendar className="w-6 h-6" />,
  },
  {
    id: 'outstanding-stock',
    title: 'Stock on Order',
    description: 'Outstanding inventory organized by stock item',
    icon: <Package className="w-6 h-6" />,
  },
  {
    id: 'pre-orders',
    title: 'Pre-Order Planning',
    description: 'Items below reorder level with suggested order quantities',
    icon: <TrendingUp className="w-6 h-6" />,
  },
  {
    id: 'delivered',
    title: 'Fully Received Orders',
    description: 'All orders that have been fully received',
    icon: <BarChart3 className="w-6 h-6" />,
  },
  {
    id: 'back-orders',
    title: 'Back Orders',
    description: 'Back orders created from short deliveries',
    icon: <Truck className="w-6 h-6" />,
  },
  {
    id: 'delivery-variance',
    title: 'Delivery Variance',
    description: 'Cost and quantity variances found when receiving stock',
    icon: <FileText className="w-6 h-6" />,
  },
];

export default function ReportsPage() {
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [dateTo, setDateTo] = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [rows, setRows] = useState<any[]>([]);
  const [columns, setColumns] = useState<{ key: string; label: string; align?: 'right' }[]>([]);

  const handleGenerateReport = async () => {
    if (!selectedReport) return;
    setLoading(true);
    setError('');
    setRows([]);
    try {
      switch (selectedReport) {
        case 'outstanding-delivery': {
          const data = await purchaseOrdersApi.orders.outstanding({
            delivery_date_from: dateFrom,
            delivery_date_to: dateTo,
          });
          setColumns([
            { key: 'order_number', label: 'Order #' },
            { key: 'supplier_name', label: 'Supplier' },
            { key: 'delivery_date', label: 'Delivery Date' },
            { key: 'status_display', label: 'Status' },
            { key: 'outstanding_value_inclusive', label: 'Outstanding Value', align: 'right' },
          ]);
          setRows(data);
          break;
        }
        case 'outstanding-stock': {
          const data = await purchaseOrdersApi.reports.stockOnOrder();
          setColumns([
            { key: 'stock_code', label: 'Stock Code' },
            { key: 'description', label: 'Description' },
            { key: 'quantity_on_hand', label: 'On Hand', align: 'right' },
            { key: 'quantity_on_order', label: 'On Order', align: 'right' },
            { key: 'reorder_quantity', label: 'Reorder Level', align: 'right' },
          ]);
          setRows(data);
          break;
        }
        case 'pre-orders': {
          const data = await purchaseOrdersApi.reports.preOrderReport();
          setColumns([
            { key: 'stock_code', label: 'Stock Code' },
            { key: 'description', label: 'Description' },
            { key: 'supplier_name', label: 'Supplier' },
            { key: 'suggested_order_qty', label: 'Suggested Qty', align: 'right' },
            { key: 'estimated_value', label: 'Estimated Value', align: 'right' },
          ]);
          setRows(data);
          break;
        }
        case 'delivered': {
          const data = await purchaseOrdersApi.orders.list({ status: 'F', page_size: 100 });
          setColumns([
            { key: 'order_number', label: 'Order #' },
            { key: 'supplier_name', label: 'Supplier' },
            { key: 'order_date', label: 'Order Date' },
            { key: 'total_value_inclusive', label: 'Total Value', align: 'right' },
          ]);
          setRows(data.results || (data as any));
          break;
        }
        case 'back-orders': {
          const data = await purchaseOrdersApi.backOrders.list();
          setColumns([
            { key: 'back_order_number', label: 'Back Order #' },
            { key: 'original_order_number', label: 'Original Order #' },
            { key: 'supplier_name', label: 'Supplier' },
            { key: 'reason', label: 'Reason' },
          ]);
          setRows((data as any).results || data);
          break;
        }
        case 'delivery-variance': {
          const data = await purchaseOrdersApi.orders.deliveryVarianceReport({
            start_date: dateFrom,
            end_date: dateTo,
          });
          setColumns([
            { key: 'order_number', label: 'Order #' },
            { key: 'supplier_name', label: 'Supplier' },
            { key: 'stock_code', label: 'Stock Code' },
            { key: 'quantity_short', label: 'Qty Short', align: 'right' },
            { key: 'value_variance', label: 'Value Variance', align: 'right' },
          ]);
          setRows(data);
          break;
        }
      }
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to generate report'));
    } finally {
      setLoading(false);
    }
  };

  const formatCell = (key: string, value: any) => {
    if (value === null || value === undefined) return '';
    if (key === 'status_display' && rows.length) {
      return value;
    }
    if (typeof value === 'number' && key.match(/value|price|cost/i)) {
      return `R ${value.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}`;
    }
    return String(value);
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
        <h1 className="text-2xl font-bold text-gray-900">Purchase Orders Reports</h1>
        <p className="text-sm text-gray-500">
          Generate and view purchase order reports
        </p>
      </div>

      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          {/* Date Range */}
          <div className="bg-white rounded-lg border shadow-sm p-4 mb-6">
            <h3 className="font-semibold text-gray-900 mb-4">Report Period</h3>
            <p className="text-xs text-gray-500 mb-3">Used by Outstanding by Delivery Date and Delivery Variance</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">From Date</label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">To Date</label>
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
            {REPORTS.map((report) => (
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
                    <h4 className="font-semibold text-gray-900">{report.title}</h4>
                    <p className="text-xs text-gray-500 mt-1">{report.description}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* Action */}
          <div className="bg-white rounded-lg border shadow-sm p-4">
            <div className="flex flex-col md:flex-row gap-4 items-end justify-between">
              <div className="text-sm text-gray-600">
                {selectedReport ? (
                  <p>
                    Selected: <strong>{REPORTS.find((r) => r.id === selectedReport)?.title}</strong>
                  </p>
                ) : (
                  <p className="text-gray-400">Select a report to continue</p>
                )}
              </div>
              <button
                onClick={handleGenerateReport}
                disabled={!selectedReport || loading}
                className="flex items-center justify-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
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

          {error && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded text-sm text-red-600">{error}</div>
          )}

          {/* Results */}
          {rows.length > 0 && (
            <div className="mt-6 bg-white rounded-lg border shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      {columns.map((col) => (
                        <th
                          key={col.key}
                          className={`px-4 py-3 text-xs font-medium text-gray-500 uppercase ${
                            col.align === 'right' ? 'text-right' : 'text-left'
                          }`}
                        >
                          {col.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {rows.map((row, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        {columns.map((col) => (
                          <td
                            key={col.key}
                            className={`px-4 py-3 text-sm ${col.align === 'right' ? 'text-right font-medium' : ''}`}
                          >
                            {col.key === 'status_display' ? (
                              <OrderStatusBadge status={row.status} size="sm" />
                            ) : (
                              formatCell(col.key, row[col.key])
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {!loading && selectedReport && rows.length === 0 && (
            <div className="mt-6 bg-white rounded-lg border shadow-sm p-8 text-center text-gray-500">
              Click Generate Report to view results
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
