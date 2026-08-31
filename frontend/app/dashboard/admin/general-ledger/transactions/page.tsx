'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { Layers, Repeat } from 'lucide-react';

const SECTIONS = [
  {
    href: '/dashboard/admin/general-ledger/transactions/batches',
    icon: Layers,
    title: 'Journal Batches',
    description: 'Capture journal entry lines, check they balance, then post them to the ledger.',
  },
  {
    href: '/dashboard/admin/general-ledger/transactions/standing-journals',
    icon: Repeat,
    title: 'Standing Journals',
    description: 'Recurring journals — define once, post the ones due for the current period.',
  },
];

export default function GeneralLedgerTransactionsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">General Ledger Transactions</h1>
        <p className="text-gray-600 mt-1">Batch journal capture and standing journals</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {SECTIONS.map((section) => (
          <Link key={section.href} href={section.href}>
            <Card className="p-6 hover:shadow-md transition-shadow cursor-pointer h-full">
              <div className="flex items-start gap-4">
                <section.icon className="w-8 h-8 text-purple-600 flex-shrink-0" />
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
