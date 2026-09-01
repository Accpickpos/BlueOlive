'use client';

import React from 'react';

interface OrderStatusBadgeProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
}

export function OrderStatusBadge({ status, size = 'md' }: OrderStatusBadgeProps) {
  // Real backend status model (PurchaseOrder.STATUS_CHOICES): O/P/F/C.
  const statusConfig: Record<string, { label: string; color: string }> = {
    O: { label: 'Outstanding', color: 'bg-indigo-100 text-indigo-800' },
    P: { label: 'Partially Received', color: 'bg-orange-100 text-orange-800' },
    F: { label: 'Fully Received', color: 'bg-green-100 text-green-800' },
    C: { label: 'Cancelled', color: 'bg-red-100 text-red-800' },
  };

  const config = statusConfig[status] || { label: status, color: 'bg-gray-100 text-gray-800' };

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5',
  };

  return (
    <span className={`inline-flex items-center rounded-full font-medium ${config.color} ${sizeClasses[size]}`}>
      {config.label}
    </span>
  );
}
