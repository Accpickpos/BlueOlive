'use client';

import React, { useState, useEffect } from 'react';
import { Truck, Check, AlertTriangle, FileText } from 'lucide-react';
import { GoodsReceivedNote, GRNAccountingLineItem } from '@/lib/types/purchaseOrders';
import { purchaseOrdersApi } from '@/lib/purchaseOrdersApi';

interface GoodsReceivedFormProps {
  orderId?: number;
  onComplete: () => void;
  onCancel: () => void;
}

export function GoodsReceivedForm({ orderId, onComplete, onCancel }: GoodsReceivedFormProps) {
  const [order, setOrder] = useState<any>(null);
  const [formData, setFormData] = useState({
    receipt_date: new Date().toISOString().split('T')[0],
    invoice_date: new Date().toISOString().split('T')[0],
    invoice_number: '',
    additional_reference: '',
  });
  const [lineItems, setLineItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (orderId) {
      fetchOrder();
    }
  }, [orderId]);

  const fetchOrder = async () => {
    try {
      const data = await purchaseOrdersApi.orders.get(orderId!);
      setOrder(data);
      setLineItems(
        (data.line_items || [])
          .filter((item: any) => Number(item.quantity_outstanding) > 0)
          .map((item: any) => ({
            id: item.id,
            stock_code: item.stock_code,
            stock_description: item.stock_description,
            quantity: Number(item.quantity),
            quantity_outstanding: Number(item.quantity_outstanding),
            current_cost: Number(item.base_price),
            quantity_received: 0,
          }))
      );
    } catch (err) {
      setError('Failed to load order');
    }
  };

  const handleQuantityChange = (index: number, quantity: number) => {
    setLineItems((prev) =>
      prev.map((item, i) => (i === index ? { ...item, quantity_received: quantity } : item))
    );
  };

  const handleCostChange = (index: number, cost: number) => {
    setLineItems((prev) =>
      prev.map((item, i) => (i === index ? { ...item, current_cost: cost } : item))
    );
  };

  const calculateTotals = () => {
    const subtotal = lineItems.reduce((sum, item) => sum + item.quantity_received * item.current_cost, 0);
    const variance = lineItems.reduce(
      (sum, item) => sum + (item.quantity_received - item.quantity) * item.current_cost,
      0
    );
    return { subtotal, variance };
  };

  const { subtotal, variance } = calculateTotals();

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const linesToReceive = lineItems.filter((item) => item.quantity_received > 0);
      if (linesToReceive.length === 0) {
        setError('Enter a received quantity for at least one line');
        return;
      }

      await purchaseOrdersApi.orders.receiveStock(orderId!, {
        receipt_date: formData.receipt_date,
        invoice_number: formData.invoice_number,
        line_items: linesToReceive.map((item) => ({
          purchase_order_line_id: item.id,
          quantity_received: item.quantity_received,
          actual_unit_cost: item.current_cost,
        })),
      });
      onComplete();
    } catch (err: any) {
      setError(err?.response?.data?.error || (err instanceof Error ? err.message : 'Failed to post GRN'));
    } finally {
      setLoading(false);
    }
  };

  if (!order) {
    return (
      <div className="p-8 text-center">
        <div className="inline-flex items-center gap-2 text-gray-500">
          <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin" />
          Loading order...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg max-w-6xl mx-auto">
      {/* Header */}
      <div className="border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
              <Truck className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Stock Received (GRN)</h2>
              <p className="text-sm text-gray-500">Order: {order.order_number}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Supplier</p>
            <p className="font-medium">{order.supplier_name}</p>
          </div>
        </div>
      </div>

      {/* Invoice Details */}
      <div className="border-b px-6 py-4 bg-gray-50">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Receipt Date</label>
            <input
              type="date"
              value={formData.receipt_date}
              onChange={(e) => setFormData({ ...formData, receipt_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Invoice Date</label>
            <input
              type="date"
              value={formData.invoice_date}
              onChange={(e) => setFormData({ ...formData, invoice_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Invoice Number</label>
            <input
              type="text"
              value={formData.invoice_number}
              onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
              placeholder="Supplier's invoice #"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Additional Reference</label>
            <input
              type="text"
              value={formData.additional_reference}
              onChange={(e) => setFormData({ ...formData, additional_reference: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
            />
          </div>
        </div>
      </div>

      {/* Line Items */}
      <div className="p-6">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <span className="text-red-600 text-sm">{error}</span>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="text-left px-3 py-2 text-xs font-medium text-gray-600">Stock Code</th>
                <th className="text-left px-3 py-2 text-xs font-medium text-gray-600">Description</th>
                <th className="text-right px-3 py-2 text-xs font-medium text-gray-600">Ordered</th>
                <th className="text-right px-3 py-2 text-xs font-medium text-gray-600">Received</th>
                <th className="text-right px-3 py-2 text-xs font-medium text-gray-600">Outstanding</th>
                <th className="text-right px-3 py-2 text-xs font-medium text-gray-600">Unit Cost</th>
                <th className="text-right px-3 py-2 text-xs font-medium text-gray-600">Total</th>
              </tr>
            </thead>
            <tbody>
              {lineItems.map((item, index) => {
                const outstanding = item.quantity_outstanding - item.quantity_received;
                return (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="px-3 py-3 text-sm font-medium">{item.stock_code}</td>
                    <td className="px-3 py-3 text-sm text-gray-600">{item.stock_description}</td>
                    <td className="px-3 py-3 text-sm text-right">{item.quantity}</td>
                    <td className="px-3 py-3 text-right">
                      <input
                        type="number"
                        value={item.quantity_received}
                        onChange={(e) => handleQuantityChange(index, parseInt(e.target.value) || 0)}
                        className="w-20 px-2 py-1 border border-gray-300 rounded text-sm text-right focus:ring-2 focus:ring-green-500"
                        min="0"
                        max={item.quantity_outstanding}
                      />
                    </td>
                    <td className="px-3 py-3 text-sm text-right">
                      <span className={outstanding > 0 ? 'text-orange-600 font-medium' : 'text-green-600'}>
                        {Math.max(0, outstanding)}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-right">
                      <input
                        type="number"
                        value={item.current_cost}
                        onChange={(e) => handleCostChange(index, parseFloat(e.target.value) || 0)}
                        className="w-24 px-2 py-1 border border-gray-300 rounded text-sm text-right focus:ring-2 focus:ring-green-500"
                        step="0.01"
                      />
                    </td>
                    <td className="px-3 py-3 text-sm text-right font-medium">
                      R {(item.quantity_received * item.current_cost).toFixed(2)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Totals */}
        <div className="mt-6 flex justify-end">
          <div className="w-72 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Subtotal:</span>
              <span className="font-medium">R {subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">VAT (14%):</span>
              <span className="font-medium">R {(subtotal * 0.14).toFixed(2)}</span>
            </div>
            <div className="flex justify-between border-t pt-2">
              <span className="font-semibold">Total:</span>
              <span className="font-bold text-lg">R {(subtotal * 1.14).toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Variance Alert */}
        {variance !== 0 && (
          <div className="mt-4 p-4 bg-orange-50 border border-orange-200 rounded-lg flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            <div>
              <p className="text-sm font-medium text-orange-800">Invoice Variance Detected</p>
              <p className="text-xs text-orange-600">
                Total difference: R {Math.abs(variance).toFixed(2)} {variance > 0 ? '(under)' : '(over)'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="border-t px-6 py-4 flex items-center justify-between bg-gray-50">
        <button onClick={onCancel} className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium">
          Cancel
        </button>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100">
            <FileText className="w-4 h-4" />
            Print GRN
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || lineItems.every((item) => item.quantity_received === 0)}
            className="flex items-center gap-2 px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Processing...' : 'Post GRN'}
            <Check className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
