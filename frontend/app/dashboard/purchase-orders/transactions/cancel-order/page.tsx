'use client';

import React, { Suspense, useState } from 'react';
import { ArrowLeft, AlertTriangle } from 'lucide-react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import purchaseOrdersApi from '@/lib/purchaseOrdersApi';
import { getApiErrorMessage } from '@/lib/api';
import { OrderPicker } from '@/components/purchase-orders/common/OrderPicker';
import type { PurchaseOrder } from '@/lib/types/purchaseOrders';

function CancelOrderContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const orderParam = searchParams.get('order');
  const [selectedOrder, setSelectedOrder] = useState<PurchaseOrder | null>(null);
  const orderId = orderParam || (selectedOrder ? String(selectedOrder.order_number) : null);
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCancel = async () => {
    if (!orderId) {
      setError('Order number is required');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await purchaseOrdersApi.orders.cancel(orderId, reason);
      router.push('/dashboard/purchase-orders');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to cancel order'));
    } finally {
      setLoading(false);
    }
  };

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
        <h1 className="text-2xl font-bold text-gray-900">Cancel Purchase Order</h1>
        <p className="text-sm text-gray-500">
          {orderId ? 'Cancel this purchase order' : 'Select an outstanding order to cancel'}
        </p>
      </div>

      <div className="p-6">
        <div className="max-w-2xl mx-auto">
          {!orderId ? (
            <OrderPicker onSelect={setSelectedOrder} />
          ) : (
          <div className="bg-white rounded-lg shadow-lg">
            <div className="border-b px-6 py-3 bg-gray-50 flex items-center justify-between">
              <span className="text-sm text-gray-600">
                Order <span className="font-semibold text-gray-900">PO {orderId}</span>
                {selectedOrder && <> — {selectedOrder.supplier_name}</>}
              </span>
              {!orderParam && (
                <button
                  onClick={() => setSelectedOrder(null)}
                  className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                >
                  Change order
                </button>
              )}
            </div>
            {/* Warning Box */}
            <div className="border-b px-6 py-4 bg-red-50">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-red-900">
                    This action cannot be undone
                  </h3>
                  <p className="text-sm text-red-700 mt-1">
                    Cancelling a fully-received order is not possible. Outstanding stock
                    on order will be reversed. Please provide a reason for the cancellation.
                  </p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded flex items-center gap-3">
                  <span className="text-red-600">{error}</span>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reason for Cancellation
                </label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Please provide a reason for cancelling this order..."
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">
                  What happens next?
                </h4>
                <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                  <li>Order status will be set to Cancelled</li>
                  <li>Outstanding quantity on order will be reversed on all stock items</li>
                  <li>No further stock can be received against this order</li>
                  <li>Fully-received orders cannot be cancelled</li>
                </ul>
              </div>
            </div>

            {/* Actions */}
            <div className="border-t px-6 py-4 bg-gray-50 flex items-center justify-between">
              <Link
                href="/dashboard/purchase-orders"
                className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
              >
                Go Back
              </Link>
              <button
                onClick={handleCancel}
                disabled={loading || !orderId}
                className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Cancelling...' : 'Cancel Order'}
              </button>
            </div>
          </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CancelOrderPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-gray-500">Loading...</div>
        </div>
      }
    >
      <CancelOrderContent />
    </Suspense>
  );
}
