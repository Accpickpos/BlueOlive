'use client';

import React from 'react';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { PurchaseOrderWizard } from '@/components/purchase-orders/transactions/PurchaseOrderWizard';
import { useRouter } from 'next/navigation';

export default function NewPurchaseOrderPage() {
  const router = useRouter();

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
        <h1 className="text-2xl font-bold text-gray-900">Create New Purchase Order</h1>
        <p className="text-sm text-gray-500">
          Follow the steps below to create a new purchase order
        </p>
      </div>

      <div className="p-6">
        <div className="max-w-4xl mx-auto">
          <PurchaseOrderWizard
            onComplete={handleComplete}
            onCancel={handleCancel}
          />
        </div>
      </div>
    </div>
  );
}
