'use client';

import React, { useEffect, useState } from 'react';
import { Printer, TrendingDown } from 'lucide-react';
import { OrderStatusBadge } from '../common/OrderStatusBadge';
import purchaseOrdersApi from '@/lib/purchaseOrdersApi';
import { getApiErrorMessage } from '@/lib/api';
import type { OutstandingByDeliveryFilter, PurchaseOrder } from '@/lib/types/purchaseOrders';

interface OutstandingByDeliveryProps {
  onFilter?: (filters: OutstandingByDeliveryFilter) => void;
}

/**
 * Outstanding purchase orders by delivery date — calls the real
 * PurchaseOrderViewSet.outstanding action (delivery_date_from/to range).
 */
export function OutstandingByDelivery({ onFilter }: OutstandingByDeliveryProps) {
  const [filters, setFilters] = useState<OutstandingByDeliveryFilter>({
    date_from: new Date().toISOString().split('T')[0],
    date_to: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  });
  const [results, setResults] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await purchaseOrdersApi.orders.outstanding({
        delivery_date_from: filters.date_from,
        delivery_date_to: filters.date_to,
      });
      setResults(data);
      setSearched(true);
      onFilter?.(filters);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load outstanding orders'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totalValue = results.reduce((sum, r) => sum + (Number(r.outstanding_value_exclusive) || 0), 0);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex flex-col md:flex-row gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">From Date</label>
            <input
              type="date"
              value={filters.date_from}
              onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">To Date</label>
            <input
              type="date"
              value={filters.date_to}
              onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded text-sm text-red-600">{error}</div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <>
          {/* Summary */}
          <div className="bg-white rounded-lg border shadow-sm p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Outstanding Value (excl VAT)</p>
                <p className="text-2xl font-bold text-gray-900">
                  R {totalValue.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => window.print()}
                  className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
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
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Order #</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Date Ordered</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Supplier</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Delivery Date</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">Value (excl VAT)</th>
                  <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {results.map((order) => (
                  <tr key={order.order_number} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-blue-600">{order.order_number}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {new Date(order.order_date).toLocaleDateString('en-ZA')}
                    </td>
                    <td className="px-4 py-3 text-sm">{order.supplier_name}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {new Date(order.delivery_date).toLocaleDateString('en-ZA')}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-medium">
                      R {(Number(order.outstanding_value_exclusive) || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2 })}
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

      {!loading && searched && results.length === 0 && (
        <div className="bg-white rounded-lg border shadow-sm p-8 text-center">
          <TrendingDown className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No outstanding orders found for this delivery date range</p>
        </div>
      )}
    </div>
  );
}
