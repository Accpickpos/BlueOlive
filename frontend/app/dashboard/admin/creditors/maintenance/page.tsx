'use client';

import { useState } from 'react';
import CreditorsMaintenance from '@/components/creditors/CreditorsMaintenance';
import ExpenseCategoryMaintenance from '@/components/creditors/ExpenseCategoryMaintenance';
import OutstandingBalanceMaintenance from '@/components/creditors/OutstandingBalanceMaintenance';

export default function CreditorMaintenancePage() {
  const [activeTab, setActiveTab] = useState<'suppliers' | 'categories' | 'balances'>('suppliers');

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Creditors Maintenance</h1>
        <p className="text-gray-600">Manage suppliers, expense categories, and outstanding balances</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-8">
          <button
            onClick={() => setActiveTab('suppliers')}
            className={`pb-4 px-2 font-medium border-b-2 transition-colors ${
              activeTab === 'suppliers'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Suppliers/Creditors
          </button>
          <button
            onClick={() => setActiveTab('categories')}
            className={`pb-4 px-2 font-medium border-b-2 transition-colors ${
              activeTab === 'categories'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Expense Categories
          </button>
          <button
            onClick={() => setActiveTab('balances')}
            className={`pb-4 px-2 font-medium border-b-2 transition-colors ${
              activeTab === 'balances'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Outstanding Balances
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'suppliers' && <CreditorsMaintenance />}
        {activeTab === 'categories' && <ExpenseCategoryMaintenance />}
        {activeTab === 'balances' && <OutstandingBalanceMaintenance />}
      </div>
    </div>
  );
}