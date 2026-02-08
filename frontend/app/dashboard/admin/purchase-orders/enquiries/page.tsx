'use client';

import React, { useState } from 'react';
import {
  Search,
  Calendar,
  Package,
  ArrowLeft,
} from 'lucide-react';
import Link from 'next/link';

interface EnquiryType {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  href: string;
  color: 'blue' | 'purple';
}

const ENQUIRY_TYPES: EnquiryType[] = [
  {
    id: 'stock-items',
    name: 'Stock Items Enquiry',
    description: 'Search and view stock items in existing purchase orders',
    icon: <Package className="w-6 h-6" />,
    href: '/dashboard/admin/purchase-orders/enquiries/stock-items',
    color: 'blue',
  },
  {
    id: 'delivery-date',
    name: 'Delivery Date Enquiry',
    description: 'Search orders by delivery date and track deliveries',
    icon: <Calendar className="w-6 h-6" />,
    href: '/dashboard/admin/purchase-orders/enquiries/delivery-date',
    color: 'purple',
  },
];

export default function EnquiriesPage() {
  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; border: string; text: string; button: string }> = {
      blue: {
        bg: 'bg-blue-50',
        border: 'border-blue-200',
        text: 'text-blue-700',
        button: 'bg-blue-600 hover:bg-blue-700',
      },
      purple: {
        bg: 'bg-purple-50',
        border: 'border-purple-200',
        text: 'text-purple-700',
        button: 'bg-purple-600 hover:bg-purple-700',
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
          Purchase Order Enquiries
        </h1>
        <p className="text-sm text-gray-500">
          Search and view purchase order information
        </p>
      </div>

      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-lg font-bold text-gray-900 mb-6">
            Available Enquiries
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {ENQUIRY_TYPES.map((enquiry) => {
              const colors = getColorClasses(enquiry.color);
              return (
                <Link
                  key={enquiry.id}
                  href={enquiry.href}
                  className={`group p-6 rounded-lg border-2 transition transform hover:shadow-lg hover:scale-105 ${colors.bg} border-gray-200 hover:${colors.border} cursor-pointer`}
                >
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${colors.bg} ${colors.text} group-hover:scale-110 transition`}>
                    {enquiry.icon}
                  </div>
                  <h3 className="font-bold text-gray-900 mb-2">
                    {enquiry.name}
                  </h3>
                  <p className="text-sm text-gray-600 mb-4">
                    {enquiry.description}
                  </p>
                  <button
                    className={`w-full ${colors.button} text-white px-4 py-2 rounded-lg font-medium transition`}
                  >
                    Search
                  </button>
                </Link>
              );
            })}
          </div>

          {/* Information Section */}
          <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg border p-6">
              <h3 className="font-bold text-gray-900 mb-2">Stock Items Enquiry</h3>
              <p className="text-sm text-gray-600">
                Find and view all stock items across purchase orders. Search by item code, description, or supplier.
              </p>
            </div>
            <div className="bg-white rounded-lg border p-6">
              <h3 className="font-bold text-gray-900 mb-2">Delivery Date Enquiry</h3>
              <p className="text-sm text-gray-600">
                Search orders by delivery date range. Track upcoming deliveries and manage receiving schedules.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
