'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowRightLeft, Plus, FileText } from 'lucide-react';

export default function CashBookTransactionsPage() {
  const transactionOptions = [
    {
      title: 'Reconciliation',
      description: 'Reconcile bank transactions with ledger',
      icon: <ArrowRightLeft className="w-8 h-8" />,
      href: '/dashboard/admin/cash-book/transactions/reconciliation',
      color: 'blue',
    },
    {
      title: 'Other Income',
      description: 'Record additional income transactions',
      icon: <Plus className="w-8 h-8" />,
      href: '/dashboard/admin/cash-book/transactions/other-income',
      color: 'green',
    },
    {
      title: 'Other Expenses',
      description: 'Record additional expense transactions',
      icon: <FileText className="w-8 h-8" />,
      href: '/dashboard/admin/cash-book/transactions/other-expenses',
      color: 'orange',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">Cash Book Transactions</h1>
        <p className="text-sm text-gray-500">Manage cash transactions and reconciliations</p>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl">
          {transactionOptions.map((option) => (
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
                Open <span className="ml-1">→</span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
