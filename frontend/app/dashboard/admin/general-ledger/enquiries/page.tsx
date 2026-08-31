'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { History, ClipboardList, RefreshCw } from 'lucide-react';

const SECTIONS = [
  {
    href: '/dashboard/admin/general-ledger/enquiries/account-history',
    icon: History,
    title: 'Account History',
    description: 'Period-by-period balance, budget, and prior-year history for one account.',
  },
  {
    href: '/dashboard/admin/general-ledger/enquiries/batch-summary',
    icon: ClipboardList,
    title: 'Batch Summary',
    description: 'Debit/credit totals and posting status for a specific batch number.',
  },
  {
    href: '/dashboard/admin/general-ledger/enquiries/outstanding-integration',
    icon: RefreshCw,
    title: 'Outstanding Integration',
    description: 'Debtors/Creditors/Stock/Cash Book records not yet transferred into GL.',
  },
];

export default function GeneralLedgerEnquiriesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">General Ledger Enquiries</h1>
        <p className="text-gray-600 mt-1">Account history, batch status, and integration status</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {SECTIONS.map((section) => (
          <Link key={section.href} href={section.href}>
            <Card className="p-6 hover:shadow-md transition-shadow cursor-pointer h-full">
              <div className="flex items-start gap-4">
                <section.icon className="w-8 h-8 text-green-600 flex-shrink-0" />
                <div>
                  <h2 className="text-lg font-bold">{section.title}</h2>
                  <p className="text-sm text-gray-600 mt-1">{section.description}</p>
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
