'use client';

import React, { useState } from 'react';
import { Search, Package, FileText, Printer, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { OrderStatusBadge } from '@/components/purchase-orders/common/OrderStatusBadge';

interface StockOutstanding {
  stock_code: string;
  stock_description: string;
  supplier_name: string;
  order_number: string;
  ordered_qty: number;
  received_qty: number;
  outstanding_qty: number;
  unit_price: number;
  line_total: number;
  delivery_date: string;
  status: string;
}

export default function OutstandingStockItemsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSupplier, setFilterSupplier] = useState('');
  const [results, setResults] = useState<StockOutstanding[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = () => {
    setLoading(true);
    // Simulated search - replace with actual API call
    setTimeout(() => {
      setResults([
        {
          stock_code: 'SKU-001',
          stock_description: 'Widget A - Standard',
          supplier_name: 'ABC Supplies',
          order_number: 'PO-001',
          ordered_qty: 100,
          received_qty: 60,
          outstanding_qty: 40,
          unit_price: 150.0,
          line_total: 6000.0,
          delivery_date: '2024-02-01',
          status: 'PARTIALLY_RECEIVED',
        },
        {
          stock_code: 'SKU-002',
          stock_description: 'Widget B - Premium',
          supplier_name: 'XYZ Trading',
          order_number: 'PO-002',
          ordered_qty: 50,
          received_qty: 0,
          outstanding_qty: 50,
          unit_price: 250.0,
          line_total: 12500.0,
          delivery_date: '2024-02-05',
          status: 'ISSUED',
        },
      ]);
      setLoading(false);
    }, 500);
  };

  const totalOutstanding = results.reduce((sum, r) => sum + r.line_total, 0);
  const totalQtyOutstanding = results.reduce(
    (sum, r) => sum + r.outstanding_qty,
    0
  );

  const suppliers = [...new Set(results.map((r) => r.supplier_name))];

  const filteredResults = results.filter((r) => {
    return (
      (r.stock_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.stock_description.toLowerCase().includes(searchTerm.toLowerCase())) &&
      (!filterSupplier || r.supplier_name === filterSupplier)
    );
  });

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
          Outstanding Stock Items
        </h1>
        <p className="text-sm text-gray-500">
          View all outstanding stock items across purchase orders
        </p>
      </div>

      <div className="p-6">
        {/* Search & Filters */}
        <div className="bg-white rounded-lg border shadow-sm p-4 mb-6">
          <div className="flex flex-col gap-4">
            <div className="flex gap-4 items-end">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Stock Code / Description
                </label>
                <input
                  type="text"
                  placeholder="Search by stock code or description"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
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

            {suppliers.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Filter by Supplier
                </label>
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => setFilterSupplier('')}
                    className={`px-3 py-1 rounded-full text-sm font-medium border ${
                      filterSupplier === ''
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'border-gray-300 text-gray-700 hover:border-gray-400'
                    }`}
                  >
                    All Suppliers
                  </button>
                  {suppliers.map((supplier) => (
                    <button
                      key={supplier}
                      onClick={() => setFilterSupplier(supplier)}
                      className={`px-3 py-1 rounded-full text-sm font-medium border ${
                        filterSupplier === supplier
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'border-gray-300 text-gray-700 hover:border-gray-400'
                      }`}
                    >
                      {supplier}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Results */}
        {filteredResults.length > 0 && (
          <>
            {/* Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-lg border shadow-sm p-4">
                <p className="text-xs text-gray-500 uppercase">
                  Total Items Outstanding
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {filteredResults.length}
                </p>
              </div>
              <div className="bg-white rounded-lg border shadow-sm p-4">
                <p className="text-xs text-gray-500 uppercase">
                  Total Qty Outstanding
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {totalQtyOutstanding}
                </p>
              </div>
              <div className="bg-white rounded-lg border shadow-sm p-4 md:col-span-2">
                <p className="text-xs text-gray-500 uppercase">
                  Total Value (excl VAT)
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  R{' '}
                  {totalOutstanding.toLocaleString('en-ZA', {
                    minimumFractionDigits: 2,
                  })}
                </p>
              </div>
            </div>

            {/* Table */}
            <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
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
                        Supplier
                      </th>
                      <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                        Ordered
                      </th>
                      <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                        Received
                      </th>
                      <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                        Outstanding
                      </th>
                      <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                        Unit Price
                      </th>
                      <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                        Line Total
                      </th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {filteredResults.map((item) => (
                      <tr key={`${item.order_number}-${item.stock_code}`} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-medium text-blue-600">
                          {item.stock_code}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {item.stock_description}
                        </td>
                        <td className="px-4 py-3 text-sm">{item.supplier_name}</td>
                        <td className="px-4 py-3 text-sm text-center">
                          {item.ordered_qty}
                        </td>
                        <td className="px-4 py-3 text-sm text-center text-green-600 font-medium">
                          {item.received_qty}
                        </td>
                        <td className="px-4 py-3 text-sm text-center font-medium text-orange-600">
                          {item.outstanding_qty}
                        </td>
                        <td className="px-4 py-3 text-sm text-right">
                          R{' '}
                          {item.unit_price.toLocaleString('en-ZA', {
                            minimumFractionDigits: 2,
                          })}
                        </td>
                        <td className="px-4 py-3 text-sm text-right font-medium">
                          R{' '}
                          {item.line_total.toLocaleString('en-ZA', {
                            minimumFractionDigits: 2,
                          })}
                        </td>
                        <td className="px-4 py-3">
                          <OrderStatusBadge status={item.status} size="sm" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {!loading && results.length === 0 && (
          <div className="bg-white rounded-lg border shadow-sm p-8 text-center">
            <Package className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">
              No stock items found
            </p>
            <p className="text-sm text-gray-400 mt-1">
              Click Search to load outstanding stock items
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
