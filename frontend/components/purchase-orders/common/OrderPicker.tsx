'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Search, FileText } from 'lucide-react';
import purchaseOrdersApi from '@/lib/purchaseOrdersApi';
import { OrderStatusBadge } from './OrderStatusBadge';
import type { PurchaseOrder } from '@/lib/types/purchaseOrders';

interface OrderPickerProps {
  onSelect: (order: PurchaseOrder) => void;
}

/**
 * Lists outstanding (status O/P) purchase orders so Cancel Order and Stock
 * Received can be reached without a pre-supplied ?order= query param — both
 * previously required navigating there manually with the order number.
 */
export function OrderPicker({ onSelect }: OrderPickerProps) {
  const [search, setSearch] = useState('');
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    purchaseOrdersApi.orders
      .outstanding()
      .then((data) => {
        if (!cancelled) setOrders(data);
      })
      .catch(() => {
        if (!cancelled) setError('Failed to load outstanding orders');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    if (!search) return orders;
    const term = search.toLowerCase();
    return orders.filter(
      (o) =>
        String(o.order_number).includes(term) ||
        (o.supplier_name || '').toLowerCase().includes(term)
    );
  }, [orders, search]);

  return (
    <div className="bg-white rounded-lg shadow-lg">
      <div className="border-b px-6 py-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by order number or supplier..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {error && <div className="px-6 py-4 text-sm text-red-600">{error}</div>}

      {loading ? (
        <div className="p-8 text-center text-gray-500">Loading outstanding orders...</div>
      ) : filtered.length === 0 ? (
        <div className="p-8 text-center">
          <FileText className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No outstanding orders found</p>
        </div>
      ) : (
        <div className="max-h-96 overflow-y-auto divide-y">
          {filtered.map((order) => (
            <button
              key={order.order_number}
              onClick={() => onSelect(order)}
              className="w-full flex items-center justify-between px-6 py-3 text-left hover:bg-gray-50"
            >
              <div>
                <p className="font-medium text-blue-600">PO {order.order_number}</p>
                <p className="text-sm text-gray-500">{order.supplier_name}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  R {(Number(order.outstanding_value_inclusive) || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2 })}
                </p>
                <OrderStatusBadge status={order.status} size="sm" />
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
