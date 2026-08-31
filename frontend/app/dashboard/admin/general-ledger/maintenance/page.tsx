'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { BookOpen, FileSpreadsheet, Settings, Sliders } from 'lucide-react';

const SECTIONS = [
  {
    href: '/dashboard/admin/general-ledger/maintenance/accounts',
    icon: BookOpen,
    title: 'Chart of Accounts',
    description: 'Create and manage GL master accounts (income statement and balance sheet).',
  },
  {
    href: '/dashboard/admin/general-ledger/maintenance/report-formats',
    icon: FileSpreadsheet,
    title: 'Report Formats',
    description: 'Define the line layout Income Statement and Balance Sheet reports are built from.',
  },
  {
    href: '/dashboard/admin/general-ledger/maintenance/parameters',
    icon: Sliders,
    title: 'Parameters',
    description: 'Current period/year, retained earnings account, and Period/Year End.',
  },
  {
    href: '/dashboard/admin/general-ledger/maintenance/integration-settings',
    icon: Settings,
    title: 'Integration Settings',
    description: 'Control-account mapping used to transfer Debtors/Creditors/Stock/Cash Book into GL.',
  },
];

export default function GeneralLedgerMaintenancePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">General Ledger Maintenance</h1>
        <p className="text-gray-600 mt-1">Chart of accounts, report formats, parameters, and integration setup</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {SECTIONS.map((section) => (
          <Link key={section.href} href={section.href}>
            <Card className="p-6 hover:shadow-md transition-shadow cursor-pointer h-full">
              <div className="flex items-start gap-4">
                <section.icon className="w-8 h-8 text-blue-600 flex-shrink-0" />
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
