'use client';

import React from 'react';
import Link from 'next/link';
import { Settings, Tag, DollarSign } from 'lucide-react';

export default function CashBookMaintenancePage() {
  const maintenanceOptions = [
    {
      title: 'Income Categories',
      description: 'Manage income category definitions',
      icon: <DollarSign className="w-8 h-8" />,
      href: '/dashboard/admin/cash-book/maintenance/income-categories',
      color: 'green',
    },
    {
      title: 'Expense Categories',
      description: 'Manage expense category definitions',
      icon: <Tag className="w-8 h-8" />,
      href: '/dashboard/admin/cash-book/maintenance/expense-categories',
      color: 'red',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center gap-2">
          <Settings className="w-6 h-6 text-gray-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Cash Book Maintenance</h1>
            <p className="text-sm text-gray-500">Manage system settings and configurations</p>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
          {maintenanceOptions.map((option) => (
            <Link
              key={option.href}
              href={option.href}
              className="bg-white rounded-lg border shadow-sm hover:shadow-md transition-shadow p-6 cursor-pointer group"
            >
              <div className={`w-14 h-14 rounded-lg bg-${option.color}-50 flex items-center justify-center text-${option.color}-600 mb-4 group-hover:bg-${option.color}-100 transition-colors`}>
                {option.icon}
              </div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">{option.title}</h2>
              <p className="text-sm text-gray-600">{option.description}</p>
              <div className="mt-4 flex items-center text-blue-600 font-medium text-sm group-hover:gap-2 transition-all">
                View <span className="ml-1">→</span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
