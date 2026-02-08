'use client';

import React, { useState } from 'react';
import { Search, Download, Printer, Package } from 'lucide-react';
import { OrderStatusBadge } from '../common/OrderStatusBadge';
import { OutstandingByStockFilter } from '@/lib/types/purchaseOrders';

interface OutstandingByStockProps {
  onFilter?: (filters: OutstandingByStockFilter) => void;
}

export function OutstandingByStock({ onFilter }: OutstandingByStockProps) {
  const [filters, setFilters] = useState<OutstandingByStockFilter>({
    stock_code: '',
    include_received: false,
  });
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = () => {
    // Simulate API call
    setLoading(true);
    setTimeout(() => {
      // Mock data
      setResults([
        {
          stock_code: 'ITEM-001',
          stock_description: 'Widget A',
          order_number: 'PO-001',
          supplier_name: 'ABC Supplies',
          quantity_ordered: 100,
          quantity_received: 60,
          quantity_outstanding: 40,
          unit_cost: 50.00,
          total_cost: 2000.00,
          status: 'PARTIALLY_RECEIVED',
        },
        {
          stock_code: 'ITEM-002',
          stock_description: 'Widget B',
          order_number: 'PO-002',
          supplier_name: 'XYZ Trading',
          quantity_ordered: 50,
          quantity_received: 0,
          quantity_outstanding: 50,
          unit_cost: 75.00,
          total_cost: 3750.00,
          status: 'ISSUED',
        },
      ]);
      setLoading(false);
    }, 500);
    
    onFilter?.(filters);
  };

  const totalValue = results.reduce((sum, r) => sum + r.total_cost, 0);
  const totalOutstanding = results.reduce((sum, r) => sum + r.quantity_outstanding, 0);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex flex-col md:flex-row gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Stock Code</label>
            <input
              type="text"
              placeholder="Enter stock code or search..."
              value={filters.stock_code || ''}
              onChange={(e) => setFilters({ ...filters, stock_code: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.include_received}
              onChange={(e) => setFilters({ ...filters, include_received: e.target.checked })}
              className="w-4 h-4 rounded border-gray-300 text-blue-600"
            />
            <span className="text-sm font-medium text-gray-700">Include Received</span>
          </label>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <p className="text-sm text-gray-500">Total Outstanding Items</p>
              <p className="text-2xl font-bold text-gray-900">{totalOutstanding}</p>
            </div>
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <p className="text-sm text-gray-500">Total Outstanding Value</p>
              <p className="text-2xl font-bold text-gray-900">
                R {totalValue.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <p className="text-sm text-gray-500">Records Found</p>
              <p className="text-2xl font-bold text-gray-900">{results.length}</p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium">
              <Printer className="w-4 h-4" />
              Print
            </button>
            <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium">
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>

          {/* Table */}
          <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Stock Code</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Order #</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">Ordered</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">Received</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">Outstanding</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">Value</th>
                  <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {results.map((item, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-blue-600">{item.stock_code}</td>
                    <td className="px-4 py-3 text-sm">{item.stock_description}</td>
                    <td className="px-4 py-3 text-sm font-medium">{item.order_number}</td>
                    <td className="px-4 py-3 text-sm text-right">{item.quantity_ordered}</td>
                    <td className="px-4 py-3 text-sm text-right">{item.quantity_received}</td>
                    <td className="px-4 py-3 text-sm text-right text-orange-600 font-medium">
                      {item.quantity_outstanding}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-medium">
                      R {item.total_cost.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <OrderStatusBadge status={item.status} size="sm" />
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
          <Package className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Click search to view outstanding stock items</p>
        </div>
      )}
    </div>
  );
}
