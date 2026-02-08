'use client';

import React, { Suspense } from 'react';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { GoodsReceivedForm } from '@/components/purchase-orders/transactions/GoodsReceivedForm';
import { useRouter } from 'next/navigation';

function StockReceivedContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const orderId = searchParams.get('order');

  const handleComplete = () => {
    router.push('/dashboard/purchase-orders');
  };

  const handleCancel = () => {
    router.back();
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
        <h1 className="text-2xl font-bold text-gray-900">
          Goods Received Note (GRN)
        </h1>
        <p className="text-sm text-gray-500">
          Record receipt of items from purchase order
        </p>
      </div>

      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <GoodsReceivedForm
            orderId={orderId ? parseInt(orderId) : undefined}
            onComplete={handleComplete}
            onCancel={handleCancel}
          />
        </div>
      </div>
    </div>
  );
}

export default function StockReceivedPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-gray-500">Loading...</div>
        </div>
      }
    >
      <StockReceivedContent />
    </Suspense>
  );
}
