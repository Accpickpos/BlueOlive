'use client';

import React, { useEffect, useState } from 'react';
import { Search, Printer, Package } from 'lucide-react';
import purchaseOrdersApi from '@/lib/purchaseOrdersApi';
import { getApiErrorMessage } from '@/lib/api';
import type { OutstandingByStockFilter, StockOnOrderItem } from '@/lib/types/purchaseOrders';

interface OutstandingByStockProps {
  onFilter?: (filters: OutstandingByStockFilter) => void;
}

/**
 * Stock items currently on order — calls the real
 * PurchaseOrderReportViewSet.stock_on_order report, grouped by stock item
 * with the outstanding orders nested underneath each one.
 */
export function OutstandingByStock({ onFilter }: OutstandingByStockProps) {
  const [stockCode, setStockCode] = useState('');
  const [items, setItems] = useState<StockOnOrderItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await purchaseOrdersApi.reports.stockOnOrder();
      setItems(data);
      setSearched(true);
      onFilter?.({ stock_code: stockCode });
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load stock on order'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filtered = stockCode
    ? items.filter((i) => i.stock_code.toLowerCase().includes(stockCode.toLowerCase()))
    : items;

  const totalOnOrder = filtered.reduce((sum, item) => sum + Number(item.quantity_on_order || 0), 0);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex flex-col md:flex-row gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Stock Code</label>
            <input
              type="text"
              placeholder="Filter by stock code..."
              value={stockCode}
              onChange={(e) => setStockCode(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
          >
            <Search className="w-4 h-4" />
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded text-sm text-red-600">{error}</div>
      )}

      {/* Results */}
      {filtered.length > 0 && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <p className="text-sm text-gray-500">Stock Items on Order</p>
              <p className="text-2xl font-bold text-gray-900">{filtered.length}</p>
            </div>
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <p className="text-sm text-gray-500">Total Quantity on Order</p>
              <p className="text-2xl font-bold text-gray-900">{totalOnOrder}</p>
            </div>
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium">
                <Printer className="w-4 h-4" />
                Print
              </button>
            </div>
          </div>

          {/* Table */}
          <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Stock Code</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">On Hand</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">On Order</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">Reorder Level</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Orders</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filtered.map((item) => (
                  <tr key={item.stock_code} className="hover:bg-gray-50 align-top">
                    <td className="px-4 py-3 text-sm font-medium text-blue-600">{item.stock_code}</td>
                    <td className="px-4 py-3 text-sm">{item.description}</td>
                    <td className="px-4 py-3 text-sm text-right">{item.quantity_on_hand}</td>
                    <td className="px-4 py-3 text-sm text-right text-orange-600 font-medium">
                      {item.quantity_on_order}
                    </td>
                    <td className="px-4 py-3 text-sm text-right">{item.reorder_quantity}</td>
                    <td className="px-4 py-3 text-xs text-gray-600">
                      {item.orders.map((o, i) => (
                        <div key={i}>
                          PO {o.order_number} · {o.supplier} · {o.quantity} due{' '}
                          {new Date(o.delivery_date).toLocaleDateString('en-ZA')}
                        </div>
                      ))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {!loading && searched && filtered.length === 0 && (
        <div className="bg-white rounded-lg border shadow-sm p-8 text-center">
          <Package className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No stock items currently on order</p>
        </div>
      )}
    </div>
  );
}
