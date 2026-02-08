'use client';

import React, { useState } from 'react';
import { Search, FileText, Printer, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { OrderStatusBadge } from '@/components/purchase-orders/common/OrderStatusBadge';

export default function OutstandingByStockItemsPage() {
  const [filters, setFilters] = useState({
    stock_code: '',
    include_received: false,
  });
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = () => {
    setLoading(true);
    // Simulated search - replace with actual API call
    setTimeout(() => {
      setResults([
        {
          stock_code: 'SKU-001',
          description: 'Product 1',
          order_number: 'PO-001',
          supplier_name: 'ABC Supplies',
          quantity_ordered: 100,
          quantity_received: 60,
          quantity_outstanding: 40,
          unit_cost: 150.0,
          status: 'PARTIALLY_RECEIVED',
        },
        {
          stock_code: 'SKU-002',
          description: 'Product 2',
          order_number: 'PO-002',
          supplier_name: 'XYZ Trading',
          quantity_ordered: 50,
          quantity_received: 0,
          quantity_outstanding: 50,
          unit_cost: 275.5,
          status: 'ISSUED',
        },
      ]);
      setLoading(false);
    }, 500);
  };

  const totalValue = results.reduce(
    (sum, r) => sum + r.quantity_outstanding * r.unit_cost,
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
          Outstanding Orders by Stock Items
        </h1>
        <p className="text-sm text-gray-500">
          View outstanding inventory organized by stock items
        </p>
      </div>

      <div className="p-6">
        {/* Filters */}
        <div className="bg-white rounded-lg border shadow-sm p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Stock Code
              </label>
              <input
                type="text"
                placeholder="Enter stock code or search..."
                value={filters.stock_code}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    stock_code: e.target.value,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.include_received}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    include_received: e.target.checked,
                  })
                }
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">
                Include Received
              </span>
            </label>
            <button
              onClick={handleSearch}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium whitespace-nowrap"
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
                  <p className="text-xs text-gray-400 mt-1">
                    {results.length} stock items
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
                      Stock Code
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                      Description
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                      Order #
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                      Supplier
                    </th>
                    <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                      Outstanding Qty
                    </th>
                    <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                      Unit Cost
                    </th>
                    <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                      Total Value
                    </th>
                    <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {results.map((item) => (
                    <tr key={`${item.order_number}-${item.stock_code}`} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-blue-600">
                        {item.stock_code}
                      </td>
                      <td className="px-4 py-3 text-sm">{item.description}</td>
                      <td className="px-4 py-3 text-sm font-medium">
                        {item.order_number}
                      </td>
                      <td className="px-4 py-3 text-sm">{item.supplier_name}</td>
                      <td className="px-4 py-3 text-sm text-right">
                        {item.quantity_outstanding}
                      </td>
                      <td className="px-4 py-3 text-sm text-right">
                        R {item.unit_cost.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-medium">
                        R{' '}
                        {(
                          item.quantity_outstanding * item.unit_cost
                        ).toLocaleString('en-ZA', {
                          minimumFractionDigits: 2,
                        })}
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
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No stock items found</p>
            <p className="text-sm text-gray-400 mt-1">
              Enter a stock code and search to find outstanding items
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
