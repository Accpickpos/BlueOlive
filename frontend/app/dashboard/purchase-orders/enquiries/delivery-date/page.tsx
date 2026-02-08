'use client';

import React, { useState } from 'react';
import { Search, Calendar, FileText, Printer, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { OrderStatusBadge } from '@/components/purchase-orders/common/OrderStatusBadge';

export default function OutstandingByDeliveryPage() {
  const [filters, setFilters] = useState({
    date_from: new Date().toISOString().split('T')[0],
    date_to: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split('T')[0],
  });
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = () => {
    setLoading(true);
    // Simulated search - replace with actual API call
    setTimeout(() => {
      setResults([
        {
          order_number: 'PO-001',
          order_date: '2024-01-15',
          supplier_name: 'ABC Supplies',
          delivery_date: '2024-02-01',
          exclusive_value_due: 15000.0,
          status: 'ISSUED',
        },
        {
          order_number: 'PO-002',
          order_date: '2024-01-18',
          supplier_name: 'XYZ Trading',
          delivery_date: '2024-02-05',
          exclusive_value_due: 8500.5,
          status: 'PARTIALLY_RECEIVED',
        },
      ]);
      setLoading(false);
    }, 500);
  };

  const totalValue = results.reduce(
    (sum, r) => sum + r.exclusive_value_due,
    0
  );

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
        <h1 className="text-xl font-bold text-gray-900">
          Outstanding Orders by Delivery Date
        </h1>
        <p className="text-sm text-gray-500">
          View all outstanding purchase orders within date range
        </p>
      </div>

      <div className="p-6">
        {/* Filters */}
        <div className="bg-white rounded-lg border shadow-sm p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4 items-end">
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
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
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
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={handleSearch}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium"
            >
              <Search className="w-4 h-4" />
              Search
            </button>
          </div>
        </div>

        {/* Results */}
        {results.length > 0 && (
          <>
            {/* Summary */}
            <div className="bg-white rounded-lg border shadow-sm p-4 mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">
                    Total Outstanding Value
                  </p>
                  <p className="text-2xl font-bold text-gray-900">
                    R{' '}
                    {totalValue.toLocaleString('en-ZA', {
                      minimumFractionDigits: 2,
                    })}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                    <Printer className="w-4 h-4" />
                    Print
                  </button>
                </div>
              </div>
            </div>

            {/* Table */}
            <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                      Order #
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                      Date Ordered
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                      Supplier
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                      Delivery Date
                    </th>
                    <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                      Value (excl VAT)
                    </th>
                    <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {results.map((order) => (
                    <tr key={order.order_number} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-blue-600">
                        {order.order_number}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {new Date(order.order_date).toLocaleDateString(
                          'en-ZA'
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm">{order.supplier_name}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {new Date(order.delivery_date).toLocaleDateString(
                          'en-ZA'
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-medium">
                        R{' '}
                        {order.exclusive_value_due.toLocaleString('en-ZA', {
                          minimumFractionDigits: 2,
                        })}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <OrderStatusBadge status={order.status} size="sm" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {!loading && results.length === 0 && (
          <div className="bg-white rounded-lg border shadow-sm p-8 text-center">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No orders found for the selected date range</p>
            <p className="text-sm text-gray-400 mt-1">
              Adjust your filters and try again
            </p>
          </div>
        )}

        {loading && (
          <div className="bg-white rounded-lg border shadow-sm p-8 text-center">
            <div className="inline-flex items-center gap-2 text-gray-500">
              <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin" />
              Loading results...
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
