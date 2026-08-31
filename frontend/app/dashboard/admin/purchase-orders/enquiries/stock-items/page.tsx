'use client';

import React from 'react';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { OutstandingByStock } from '@/components/purchase-orders/enquiries/OutstandingByStock';

export default function OutstandingStockItemsPage() {
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
          View stock items currently on order, and which purchase orders they're on
        </p>
      </div>

      <div className="p-6">
        <OutstandingByStock />
      </div>
    </div>
  );
}
