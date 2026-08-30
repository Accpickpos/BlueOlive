'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { Scale, TrendingUp, Landmark, CalendarClock } from 'lucide-react';

const REPORTS = [
  {
    href: '/dashboard/admin/general-ledger/reports/trial-balance',
    icon: Scale,
    title: 'Trial Balance',
    description: 'Every account’s debit/credit balance as of a chosen period — must tie out.',
  },
  {
    href: '/dashboard/admin/general-ledger/reports/income-statement',
    icon: TrendingUp,
    title: 'Income Statement',
    description: 'Revenue and expense performance for the period, per the Report Format layout.',
  },
  {
    href: '/dashboard/admin/general-ledger/reports/balance-sheet',
    icon: Landmark,
    title: 'Balance Sheet',
    description: 'Assets, liabilities, and equity as of a chosen period, per the Report Format layout.',
  },
  {
    href: '/dashboard/admin/general-ledger/maintenance/parameters',
    icon: CalendarClock,
    title: 'Period / Year End',
    description: 'Advance the current period or close the financial year.',
  },
];

export default function GeneralLedgerReportsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">General Ledger Reports</h1>
        <p className="text-gray-600 mt-1">Trial Balance, Income Statement, Balance Sheet, Period/Year End</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {REPORTS.map((report) => (
          <Link key={report.href} href={report.href}>
            <Card className="p-6 hover:shadow-md transition-shadow cursor-pointer h-full">
              <div className="flex items-start gap-4">
                <report.icon className="w-8 h-8 text-orange-600 flex-shrink-0" />
                <div>
                  <h2 className="text-lg font-bold">{report.title}</h2>
                  <p className="text-sm text-gray-600 mt-1">{report.description}</p>
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
