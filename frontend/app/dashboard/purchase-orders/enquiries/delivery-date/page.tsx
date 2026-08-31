'use client';

import React from 'react';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { OutstandingByDelivery } from '@/components/purchase-orders/enquiries/OutstandingByDelivery';

export default function OutstandingByDeliveryPage() {
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
          Outstanding Orders by Delivery Date
        </h1>
        <p className="text-sm text-gray-500">
          View all outstanding purchase orders within a delivery date range
        </p>
      </div>

      <div className="p-6">
        <OutstandingByDelivery />
      </div>
    </div>
  );
}
