'use client';

import { useState } from 'react';
import DebitJournalForm from './transactions/DebitJournalForm';
import CreditJournalForm from './transactions/CreditJournalForm';
import InterestChargingForm from './transactions/InterestChargingForm';
import BatchReceiptPostingForm from './transactions/BatchReceiptPostingForm';
import CancelRemovePDCForm from './transactions/CancelRemovePDCForm';

type TabType = 'debit-journal' | 'credit-journal' | 'interest-charging' | 'batch-receipt' | 'cancel-pdc';

export default function TransactionManagement() {
  const [activeTab, setActiveTab] = useState<TabType>('debit-journal');

  const tabs = [
    { id: 'debit-journal', label: 'Debit Journal', icon: '📥' },
    { id: 'credit-journal', label: 'Credit Journal', icon: '📤' },
    { id: 'interest-charging', label: 'Interest Charging', icon: '💰' },
    { id: 'batch-receipt', label: 'Batch Receipt Posting', icon: '🧾' },
    { id: 'cancel-pdc', label: 'Cancel / Remove PDC', icon: '❌' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Transaction Management</h1>
        <p className="text-gray-600 mt-1">Manage debtor transactions - create journals, charge interest, post receipts, and manage PDCs</p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="flex flex-wrap border-b border-gray-200">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`px-6 py-4 font-medium text-sm flex items-center gap-2 border-b-2 transition-all ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 bg-blue-50'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <span className="text-lg">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'debit-journal' && <DebitJournalForm />}
          {activeTab === 'credit-journal' && <CreditJournalForm />}
          {activeTab === 'interest-charging' && <InterestChargingForm />}
          {activeTab === 'batch-receipt' && <BatchReceiptPostingForm />}
          {activeTab === 'cancel-pdc' && <CancelRemovePDCForm />}
        </div>
      </div>
    </div>
  );
}
