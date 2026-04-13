// app/dashboard/admin/stockfinder/orders/page.tsx
"use client";
import { useState, useEffect } from "react";
import { Package, Loader, FileText, Wrench } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";

interface StockFinderOrder {
  id: number;
  stockfinder_order_id: string;
  order_number: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  vehicle_registration: string;
  vehicle_make: string;
  vehicle_model: string;
  status: string;
  status_display: string;
  order_date: string;
  required_date: string | null;
  notes: string;
  fitment_center: string;
  subtotal: string;
  tax_amount: string;
  total_amount: string;
  local_job_card: number | null;
  local_invoice: number | null;
  lines: OrderLine[];
  created_at: string;
}

interface OrderLine {
  id: number;
  line_number: number;
  stock_code: string;
  description: string;
  quantity: string;
  unit_price: string;
  tax_amount: string;
  line_total: string;
}

export default function StockfinderOrdersPage() {
  const [loading, setLoading] = useState(false);
  const [orders, setOrders] = useState<StockFinderOrder[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<StockFinderOrder | null>(null);
  const [filter, setFilter] = useState('all');
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/stockfinder/orders/');
      setOrders(response.data.results || response.data);
    } catch (err: any) {
      setError('Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  const createJobCard = async (orderId: number) => {
    setActionLoading(orderId);
    setError(null);
    setSuccess(null);
    try {
      const response = await api.post(`/api/v1/stockfinder/orders/${orderId}/create_job_card/`);
      setSuccess(`JobCard created: ${response.data.job_card_reference}`);
      loadOrders();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create JobCard');
    } finally {
      setActionLoading(null);
    }
  };

  const createInvoice = async (orderId: number) => {
    setActionLoading(orderId);
    setError(null);
    setSuccess(null);
    try {
      const response = await api.post(`/api/v1/stockfinder/orders/${orderId}/create_invoice/`);
      setSuccess(`Invoice created: ${response.data.invoice_number}`);
      loadOrders();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create Invoice');
    } finally {
      setActionLoading(null);
    }
  };

  const filteredOrders = orders.filter(order => {
    if (filter === 'all') return true;
    if (filter === 'pending') return order.status === 'pending';
    if (filter === 'in_progress') return order.status === 'in_progress';
    if (filter === 'completed') return order.status === 'completed';
    return true;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'accepted': return 'bg-blue-100 text-blue-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Package className="h-8 w-8" />
            Stockfinder Orders
          </h1>
          <p className="text-gray-600 mt-1">
            View orders received from Stockfinder and create local records
          </p>
        </div>
        <button
          onClick={loadOrders}
          className="px-4 py-2 border rounded-lg hover:bg-gray-50"
        >
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="mb-4 flex gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1 rounded ${filter === 'all' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100'}`}
        >
          All
        </button>
        <button
          onClick={() => setFilter('pending')}
          className={`px-3 py-1 rounded ${filter === 'pending' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100'}`}
        >
          Pending
        </button>
        <button
          onClick={() => setFilter('in_progress')}
          className={`px-3 py-1 rounded ${filter === 'in_progress' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100'}`}
        >
          In Progress
        </button>
        <button
          onClick={() => setFilter('completed')}
          className={`px-3 py-1 rounded ${filter === 'completed' ? 'bg-green-100 text-green-800' : 'bg-gray-100'}`}
        >
          Completed
        </button>
      </div>

      {/* Messages */}
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
          {success}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8">
          <Loader className="h-8 w-8 animate-spin mx-auto" />
        </div>
      ) : filteredOrders.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-gray-500">
            No orders found from Stockfinder.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredOrders.map((order) => (
            <Card key={order.id} className={selectedOrder?.id === order.id ? 'border-blue-500' : ''}>
              <CardContent className="p-4">
                <div 
                  className="flex justify-between items-start cursor-pointer"
                  onClick={() => setSelectedOrder(selectedOrder?.id === order.id ? null : order)}
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{order.stockfinder_order_id}</h3>
                      <span className={`px-2 py-0.5 text-xs rounded ${getStatusColor(order.status)}`}>
                        {order.status_display}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {order.customer_name} • {order.vehicle_registration || 'No vehicle'}
                    </p>
                    <div className="text-sm text-gray-500 mt-1">
                      {new Date(order.order_date).toLocaleDateString()} • 
                      Total: R{order.total_amount}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {order.local_job_card && (
                      <span className="text-xs text-green-600 flex items-center gap-1">
                        <Wrench className="h-3 w-3" /> JobCard
                      </span>
                    )}
                    {order.local_invoice && (
                      <span className="text-xs text-blue-600 flex items-center gap-1">
                        <FileText className="h-3 w-3" /> Invoice
                      </span>
                    )}
                  </div>
                </div>

                {/* Expanded Details */}
                {selectedOrder?.id === order.id && (
                  <div className="mt-4 pt-4 border-t">
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <h4 className="font-medium text-sm">Customer Details</h4>
                        <p className="text-sm text-gray-600">{order.customer_name}</p>
                        <p className="text-sm text-gray-600">{order.customer_email}</p>
                        <p className="text-sm text-gray-600">{order.customer_phone}</p>
                      </div>
                      <div>
                        <h4 className="font-medium text-sm">Vehicle</h4>
                        <p className="text-sm text-gray-600">{order.vehicle_registration}</p>
                        <p className="text-sm text-gray-600">{order.vehicle_make} {order.vehicle_model}</p>
                      </div>
                    </div>

                    {/* Order Lines */}
                    <h4 className="font-medium text-sm mb-2">Order Lines</h4>
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-1">Stock Code</th>
                          <th className="text-left py-1">Description</th>
                          <th className="text-right py-1">Qty</th>
                          <th className="text-right py-1">Price</th>
                          <th className="text-right py-1">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {order.lines.map((line) => (
                          <tr key={line.id} className="border-b">
                            <td className="py-1">{line.stock_code}</td>
                            <td className="py-1">{line.description}</td>
                            <td className="text-right py-1">{line.quantity}</td>
                            <td className="text-right py-1">R{line.unit_price}</td>
                            <td className="text-right py-1">R{line.line_total}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>

                    {/* Actions */}
                    <div className="mt-4 flex gap-2">
                      {!order.local_job_card && (
                        <button
                          onClick={() => createJobCard(order.id)}
                          disabled={actionLoading === order.id}
                          className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                          {actionLoading === order.id ? (
                            <Loader className="h-3 w-3 animate-spin" />
                          ) : (
                            <Wrench className="h-3 w-3" />
                          )}
                          Create JobCard
                        </button>
                      )}
                      {!order.local_invoice && (
                        <button
                          onClick={() => createInvoice(order.id)}
                          disabled={actionLoading === order.id}
                          className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
                        >
                          {actionLoading === order.id ? (
                            <Loader className="h-3 w-3 animate-spin" />
                          ) : (
                            <FileText className="h-3 w-3" />
                          )}
                          Create Invoice
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
