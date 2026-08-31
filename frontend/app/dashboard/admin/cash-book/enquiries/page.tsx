'use client';

import React from 'react';
import Link from 'next/link';
import { Search, Building2, BarChart3, ListOrdered, Percent, FileClock, ClipboardList } from 'lucide-react';

export default function CashBookEnquiriesPage() {
  const enquiryOptions = [
    {
      title: 'Banking Account',
      description: 'Query transactions by banking account',
      icon: <Building2 className="w-8 h-8" />,
      href: '/dashboard/admin/cash-book/enquiries/banking-account',
      color: 'blue',
    },
    {
      title: 'Monthly Analysis',
      description: 'Analyze monthly cash book transactions',
      icon: <BarChart3 className="w-8 h-8" />,
      href: '/dashboard/admin/cash-book/enquiries/monthly-analysis',
      color: 'purple',
    },
    {
      title: 'Transaction Scroll',
      description: 'Continuous, ordered scroll of every transaction',
      icon: <ListOrdered className="w-8 h-8" />,
      href: '/dashboard/admin/cash-book/enquiries/transaction-scroll',
      color: 'indigo',
    },
    {
      title: 'Category & Tax Analysis',
      description: 'Income/expense by category, split by value and VAT',
      icon: <Percent className="w-8 h-8" />,
      href: '/dashboard/admin/cash-book/enquiries/category-tax-analysis',
      color: 'emerald',
    },
    {
      title: 'PDC Listing',
      description: 'Cheques issued but not yet presented at the bank',
      icon: <FileClock className="w-8 h-8" />,
      href: '/dashboard/admin/cash-book/enquiries/pdc-listing',
      color: 'amber',
    },
    {
      title: 'Control Summary',
      description: 'Period-end reconciling totals for the cash book',
      icon: <ClipboardList className="w-8 h-8" />,
      href: '/dashboard/admin/cash-book/enquiries/control-summary',
      color: 'rose',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center gap-2">
          <Search className="w-6 h-6 text-gray-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Cash Book Enquiries</h1>
            <p className="text-sm text-gray-500">Search and analyze cash book data</p>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl">
          {enquiryOptions.map((option) => (
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
                Search <span className="ml-1">→</span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
