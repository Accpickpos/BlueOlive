'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/card';
import {
  FileText,
  Users,
  TrendingUp,
  PieChart,
  CreditCard,
  BarChart3,
  Settings,
  FileCheck,
} from 'lucide-react';

const QUICK_LINKS = [
  {
    title: 'Accounts',
    description: 'Manage debtor accounts',
    href: '/dashboard/admin/debtors/maintenance',
    icon: Users,
    color: 'bg-blue-500',
  },
  {
    title: 'Transactions',
    description: 'Post journals & receipts',
    href: '/dashboard/admin/debtors/transactions',
    icon: FileText,
    color: 'bg-green-500',
  },
  {
    title: 'Age Analysis',
    description: 'View aging summary',
    href: '/dashboard/admin/debtors/enquiries/summary',
    icon: BarChart3,
    color: 'bg-purple-500',
  },
  {
    title: 'Top Accounts',
    description: 'High balance debtors',
    href: '/dashboard/admin/debtors/enquiries/top-accounts',
    icon: TrendingUp,
    color: 'bg-orange-500',
  },
  {
    title: 'PDC Management',
    description: 'Post-dated cheques',
    href: '/dashboard/admin/debtors/transactions/pdc',
    icon: CreditCard,
    color: 'bg-pink-500',
  },
  {
    title: 'Reports',
    description: 'Generate reports',
    href: '/dashboard/admin/debtors/reports',
    icon: FileCheck,
    color: 'bg-indigo-500',
  },
];

export default function QuickLinks() {
  return (
    <div className="space-y-3">
      <h2 className="text-lg font-bold">Quick Access</h2>
      {QUICK_LINKS.map((link) => {
        const Icon = link.icon;
        return (
          <Link key={link.href} href={link.href}>
            <Card className="p-3 cursor-pointer hover:shadow-md transition-shadow">
              <div className="flex items-start gap-3">
                <div className={`${link.color} p-2 rounded-lg flex-shrink-0`}>
                  <Icon className="w-4 h-4 text-white" />
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-sm">{link.title}</p>
                  <p className="text-xs text-gray-600">{link.description}</p>
                </div>
              </div>
            </Card>
          </Link>
        );
      })}
    </div>
  );
}
