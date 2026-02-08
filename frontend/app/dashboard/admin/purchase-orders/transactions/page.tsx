'use client';

import React, { useState } from 'react';
import {
  PlusCircle,
  Package,
  Truck,
  X,
  ArrowLeft,
} from 'lucide-react';
import Link from 'next/link';

interface TransactionType {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  href: string;
  color: 'blue' | 'green' | 'orange' | 'red';
}

const TRANSACTION_TYPES: TransactionType[] = [
  {
    id: 'new-order',
    name: 'New Purchase Order',
    description: 'Create a new purchase order for suppliers',
    icon: <PlusCircle className="w-6 h-6" />,
    href: '/dashboard/admin/purchase-orders/transactions/new-order',
    color: 'blue',
  },
  {
    id: 'stock-received',
    name: 'Goods Received Note (GRN)',
    description: 'Record receipt of items from suppliers',
    icon: <Truck className="w-6 h-6" />,
    href: '/dashboard/admin/purchase-orders/transactions/stock-received',
    color: 'green',
  },
  {
    id: 'cancel-order',
    name: 'Cancel Order',
    description: 'Cancel an existing purchase order',
    icon: <X className="w-6 h-6" />,
    href: '/dashboard/admin/purchase-orders/transactions/cancel-order',
    color: 'red',
  },
];

export default function TransactionsPage() {
  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; border: string; text: string; button: string }> = {
      blue: {
        bg: 'bg-blue-50',
        border: 'border-blue-200',
        text: 'text-blue-700',
        button: 'bg-blue-600 hover:bg-blue-700',
      },
      green: {
        bg: 'bg-green-50',
        border: 'border-green-200',
        text: 'text-green-700',
        button: 'bg-green-600 hover:bg-green-700',
      },
      orange: {
        bg: 'bg-orange-50',
        border: 'border-orange-200',
        text: 'text-orange-700',
        button: 'bg-orange-600 hover:bg-orange-700',
      },
      red: {
        bg: 'bg-red-50',
        border: 'border-red-200',
        text: 'text-red-700',
        button: 'bg-red-600 hover:bg-red-700',
      },
    };
    return colors[color] || colors.blue;
  };

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
          Purchase Order Transactions
        </h1>
        <p className="text-sm text-gray-500">
          Manage purchase orders, receipts, and related transactions
        </p>
      </div>

      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-lg font-bold text-gray-900 mb-6">
            Available Transactions
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {TRANSACTION_TYPES.map((transaction) => {
              const colors = getColorClasses(transaction.color);
              return (
                <Link
                  key={transaction.id}
                  href={transaction.href}
                  className={`group p-6 rounded-lg border-2 transition transform hover:shadow-lg hover:scale-105 ${colors.bg} border-gray-200 hover:${colors.border} cursor-pointer`}
                >
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${colors.bg} ${colors.text} group-hover:scale-110 transition`}>
                    {transaction.icon}
                  </div>
                  <h3 className="font-bold text-gray-900 mb-2">
                    {transaction.name}
                  </h3>
                  <p className="text-sm text-gray-600 mb-4">
                    {transaction.description}
                  </p>
                  <button
                    className={`w-full ${colors.button} text-white px-4 py-2 rounded-lg font-medium transition`}
                  >
                    Access
                  </button>
                </Link>
              );
            })}
          </div>

          {/* Information Section */}
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg border p-6">
              <h3 className="font-bold text-gray-900 mb-2">New Purchase Order</h3>
              <p className="text-sm text-gray-600">
                Create purchase orders for your suppliers. Define items, quantities, and delivery dates.
              </p>
            </div>
            <div className="bg-white rounded-lg border p-6">
              <h3 className="font-bold text-gray-900 mb-2">Goods Received</h3>
              <p className="text-sm text-gray-600">
                Record goods received from suppliers. Match items with orders and update stock levels.
              </p>
            </div>
            <div className="bg-white rounded-lg border p-6">
              <h3 className="font-bold text-gray-900 mb-2">Cancel Order</h3>
              <p className="text-sm text-gray-600">
                Cancel pending or issued orders. Keep audit trail of cancellations for compliance.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
