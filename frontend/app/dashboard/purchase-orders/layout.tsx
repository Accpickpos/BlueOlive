'use client';

import React from 'react';
import { 
  Package, 
  TrendingUp, 
  Search, 
  BarChart3, 
  Settings,
  FileText,
  Truck,
  Calendar
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function PurchaseOrdersLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path || pathname.startsWith(path);

  return (
    <div className="flex gap-6">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-white border-r sticky top-20 h-[calc(100vh-80px)] overflow-y-auto">
        <nav className="p-4 space-y-1">
          {/* Main Dashboard */}
          <Link
            href="/dashboard/purchase-orders"
            className={`flex items-center gap-3 px-4 py-2.5 rounded-lg font-medium transition-colors ${
              pathname === '/dashboard/purchase-orders'
                ? 'bg-blue-50 text-blue-700'
                : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Package className="w-5 h-5" />
            Dashboard
          </Link>

          {/* Transactions Section */}
          <div className="pt-4">
            <h3 className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Transactions
            </h3>
            <div className="space-y-1">
              <Link
                href="/dashboard/purchase-orders/transactions/new-order"
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg font-medium transition-colors ${
                  isActive('/dashboard/purchase-orders/transactions/new-order')
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <FileText className="w-5 h-5" />
                New Order
              </Link>
              <Link
                href="/dashboard/purchase-orders/transactions/stock-received"
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg font-medium transition-colors ${
                  isActive('/dashboard/purchase-orders/transactions/stock-received')
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Truck className="w-5 h-5" />
                Stock Received
              </Link>
              <Link
                href="/dashboard/purchase-orders/transactions/cancel-order"
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg font-medium transition-colors ${
                  isActive('/dashboard/purchase-orders/transactions/cancel-order')
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <FileText className="w-5 h-5" />
                Cancel Order
              </Link>
            </div>
          </div>

          {/* Enquiries Section */}
          <div className="pt-4">
            <h3 className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Enquiries
            </h3>
            <div className="space-y-1">
              <Link
                href="/dashboard/purchase-orders/enquiries/delivery-date"
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg font-medium transition-colors ${
                  isActive('/dashboard/purchase-orders/enquiries/delivery-date')
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Calendar className="w-5 h-5" />
                By Delivery Date
              </Link>
              <Link
                href="/dashboard/purchase-orders/enquiries/stock-items"
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg font-medium transition-colors ${
                  isActive('/dashboard/purchase-orders/enquiries/stock-items')
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Search className="w-5 h-5" />
                By Stock Items
              </Link>
            </div>
          </div>

          {/* Reports Section */}
          <div className="pt-4">
            <h3 className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Reports
            </h3>
            <Link
              href="/dashboard/purchase-orders/reports"
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg font-medium transition-colors ${
                isActive('/dashboard/purchase-orders/reports')
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <BarChart3 className="w-5 h-5" />
              Reports
            </Link>
          </div>

          {/* Utilities Section */}
          <div className="pt-4">
            <h3 className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Utilities
            </h3>
            <Link
              href="/dashboard/purchase-orders/utilities"
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg font-medium transition-colors ${
                isActive('/dashboard/purchase-orders/utilities')
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Settings className="w-5 h-5" />
              Utilities
            </Link>
          </div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
