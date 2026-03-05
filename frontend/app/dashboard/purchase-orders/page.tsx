'use client';

import React, { useState, useEffect } from 'react';
import {
  PlusCircle,
  FileText,
  Search,
  Download,
  Printer,
  Clock,
  Package,
  Truck,
  BarChart3,
} from 'lucide-react';

// Import components directly
import { OrderStatusBadge } from '@/components/purchase-orders/common/OrderStatusBadge';
import { OrderSummaryCard } from '@/components/purchase-orders/common/OrderSummaryCard';
import { PurchaseOrderWizard } from '@/components/purchase-orders/transactions/PurchaseOrderWizard';
import { OutstandingByDelivery } from '@/components/purchase-orders/enquiries/OutstandingByDelivery';

import purchaseOrdersApi from '@/lib/purchaseOrdersApi';
import type { PurchaseOrder } from '@/lib/types/purchaseOrders';

export default function PurchaseOrdersPage() {
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    fetchOrders();
  }, [statusFilter, currentPage]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const params: any = { page: currentPage, page_size: 20 };
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }
      if (searchTerm) {
        params.search = searchTerm;
      }

      const response = await purchaseOrdersApi.orders.list(params);
      setOrders(response.results || response);
      setTotalCount(response.count || 0);
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchOrders();
  };

  // Calculate summary statistics
  const summaryStats = {
    totalOrders: totalCount,
    pendingOrders: orders.filter((o) =>
      ['DRAFT', 'PENDING_APPROVAL', 'ISSUED'].includes(o.status)
    ).length,
    totalValue: orders.reduce((sum, o) => sum + (o.total_amount || 0), 0),
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Purchase Orders</h1>
            <p className="text-sm text-gray-500">
              Manage orders, receipts, and supplier deliveries
            </p>
          </div>
          <div className="flex gap-3">
            <a
              href="/dashboard/purchase-orders/transactions/new-order"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              New Purchase Order
            </a>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-6">
        <OrderSummaryCard
          title="Total Orders"
          value={summaryStats.totalOrders}
          subtitle="All time"
          icon={<FileText className="w-5 h-5 text-blue-600" />}
          color="info"
        />
        <OrderSummaryCard
          title="Pending Orders"
          value={summaryStats.pendingOrders}
          subtitle="Awaiting processing"
          icon={<Clock className="w-5 h-5 text-yellow-600" />}
          color="warning"
        />
        <OrderSummaryCard
          title="Total Value"
          value={summaryStats.totalValue}
          subtitle="All orders"
          icon={<BarChart3 className="w-5 h-5 text-green-600" />}
          color="success"
        />
        <OrderSummaryCard
          title="Received Today"
          value={0}
          subtitle="Completed receipts"
          icon={<Package className="w-5 h-5 text-purple-600" />}
        />
      </div>

      {/* Filters & Search */}
      <div className="px-6">
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
            <form onSubmit={handleSearch} className="flex gap-3 w-full md:w-auto">
              <div className="relative flex-1 md:w-80">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search orders..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="DRAFT">Draft</option>
                <option value="PENDING_APPROVAL">Pending Approval</option>
                <option value="APPROVED">Approved</option>
                <option value="ISSUED">Issued</option>
                <option value="PARTIALLY_RECEIVED">Partially Received</option>
                <option value="RECEIVED">Received</option>
                <option value="CLOSED">Closed</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
              <button
                type="submit"
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors"
              >
                Search
              </button>
            </form>

            <div className="flex gap-2">
              <a
                href="/dashboard/purchase-orders/enquiries/delivery-date"
                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg font-medium transition-colors"
              >
                <Search className="w-4 h-4" />
                Enquiries
              </a>
              <a
                href="/dashboard/purchase-orders/reports"
                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg font-medium transition-colors"
              >
                <Download className="w-4 h-4" />
                Reports
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Orders Table */}
      <div className="px-6 pb-6">
        <div className="bg-white rounded-lg border shadow-sm overflow-hidden mt-4">
          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-flex items-center gap-2 text-gray-500">
                <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin" />
                Loading orders...
              </div>
            </div>
          ) : orders.length === 0 ? (
            <div className="p-8 text-center">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No purchase orders found</p>
              <a
                href="/dashboard/purchase-orders/transactions/new-order"
                className="inline-flex items-center gap-2 mt-4 text-blue-600 hover:text-blue-700 font-medium"
              >
                <PlusCircle className="w-4 h-4" />
                Create your first order
              </a>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Order #
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Supplier
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Delivery Date
                  </th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {orders.map((order) => (
                  <tr key={order.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-blue-600">
                      {order.order_number}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {new Date(order.order_date).toLocaleDateString('en-ZA')}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {order.supplier_name || order.supplier_id}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {new Date(order.delivery_date).toLocaleDateString('en-ZA')}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-medium">
                      R{' '}
                      {(order.total_amount || 0).toLocaleString('en-ZA', {
                        minimumFractionDigits: 2,
                      })}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <OrderStatusBadge status={order.status} size="sm" />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                          title="View Details"
                        >
                          <FileText className="w-4 h-4" />
                        </button>
                        <button
                          className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                          title="Print"
                        >
                          <Printer className="w-4 h-4" />
                        </button>
                        {order.status === 'ISSUED' && (
                          <a
                            href={`/dashboard/purchase-orders/transactions/stock-received?order=${order.id}`}
                            className="p-1.5 text-green-600 hover:text-green-700 hover:bg-green-100 rounded"
                            title="Receive Stock"
                          >
                            <Truck className="w-4 h-4" />
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* Pagination */}
          {totalCount > 20 && (
            <div className="px-4 py-3 border-t bg-gray-50 flex items-center justify-between">
              <p className="text-sm text-gray-500">
                Showing {orders.length} of {totalCount} orders
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 border rounded hover:bg-gray-100 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage((p) => p + 1)}
                  disabled={orders.length < 20}
                  className="px-3 py-1 border rounded hover:bg-gray-100 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
