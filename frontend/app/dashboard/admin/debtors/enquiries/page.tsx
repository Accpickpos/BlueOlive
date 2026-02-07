'use client';

import { useState } from 'react';
import IndividualAccountEnquiry from '@/components/debtors/enquiries/IndividualAccountEnquiry';
import DebtorsSummaryEnquiry from '@/components/debtors/enquiries/DebtorsSummaryEnquiry';
import TopAccountsEnquiry from '@/components/debtors/enquiries/TopAccountsEnquiry';
import TransactionsEnquiry from '@/components/debtors/enquiries/TransactionsEnquiry';
import SalesDepartmentsEnquiry from '@/components/debtors/enquiries/SalesDepartmentsEnquiry';
import SalesmanEnquiry from '@/components/debtors/enquiries/SalesmanEnquiry';
import PostDatedChequeListingEnquiry from '@/components/debtors/enquiries/PostDatedChequeListingEnquiry';
import AccountSalesHistoryEnquiry from '@/components/debtors/enquiries/AccountSalesHistoryEnquiry';

type EnquiryType = 
  | 'individual' 
  | 'summary' 
  | 'topaccounts' 
  | 'transactions' 
  | 'departments' 
  | 'salesman' 
  | 'pdc' 
  | 'saleshistory';

const menuItems = [
  {
    id: 'individual',
    title: 'Individual Account',
    icon: '👤',
    description: 'Balance Brought Forward & Open Item Debtors',
  },
  {
    id: 'summary',
    title: 'Total Debtors Summary',
    icon: '📊',
    description: 'Age Analysis & Control Enquiry',
  },
  {
    id: 'topaccounts',
    title: 'Top Accounts',
    icon: '⭐',
    description: 'Account Performance by Sales Area/User',
  },
  {
    id: 'transactions',
    title: 'Transactions',
    icon: '📝',
    description: 'Invoices, Credits, Receipts & More',
  },
  {
    id: 'departments',
    title: 'Sales Departments',
    icon: '🏢',
    description: 'Month-by-Month Department Performance',
  },
  {
    id: 'salesman',
    title: 'Salesman',
    icon: '👨‍💼',
    description: 'Month-by-Month Salesman Performance',
  },
  {
    id: 'pdc',
    title: 'Post Dated Cheques',
    icon: '💳',
    description: 'PDC Listing by Account or Date',
  },
  {
    id: 'saleshistory',
    title: 'Account Sales History',
    icon: '📈',
    description: 'Sales Transactions for Selected Debtor',
  },
];

export default function DebtorsEnquiriesPage() {
  const [activeEnquiry, setActiveEnquiry] = useState<EnquiryType>('individual');

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Debtors' Enquiry Menu</h1>
        <p className="text-gray-600 mt-1">Select an enquiry option to view detailed debtor information, transactions, and reports</p>
      </div>

      {/* Menu Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {menuItems.map(item => (
          <button
            key={item.id}
            onClick={() => setActiveEnquiry(item.id as EnquiryType)}
            className={`p-4 rounded-lg border-2 transition-all text-left ${
              activeEnquiry === item.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 bg-white hover:border-blue-300 hover:shadow-md'
            }`}
          >
            <div className="text-2xl mb-2">{item.icon}</div>
            <h3 className="font-semibold text-gray-900 text-sm">{item.title}</h3>
            <p className="text-xs text-gray-600 mt-1">{item.description}</p>
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        {activeEnquiry === 'individual' && <IndividualAccountEnquiry />}
        {activeEnquiry === 'summary' && <DebtorsSummaryEnquiry />}
        {activeEnquiry === 'topaccounts' && <TopAccountsEnquiry />}
        {activeEnquiry === 'transactions' && <TransactionsEnquiry />}
        {activeEnquiry === 'departments' && <SalesDepartmentsEnquiry />}
        {activeEnquiry === 'salesman' && <SalesmanEnquiry />}
        {activeEnquiry === 'pdc' && <PostDatedChequeListingEnquiry />}
        {activeEnquiry === 'saleshistory' && <AccountSalesHistoryEnquiry />}
      </div>
    </div>
  );
}
