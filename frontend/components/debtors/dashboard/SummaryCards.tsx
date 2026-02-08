'use client';

import { Card } from '@/components/ui/card';
import type { DebtorsSummary } from '@/lib/types/debtors';
import { Users, User, Lock, TrendingUp, AlertCircle, DollarSign } from 'lucide-react';

interface SummaryCardsProps {
  summary: DebtorsSummary;
}

export default function SummaryCards({ summary }: SummaryCardsProps) {
  const stats = [
    {
      label: 'Total Debtors',
      value: summary.total_debtors,
      icon: Users,
      color: 'bg-blue-500',
      trend: null,
    },
    {
      label: 'Active Debtors',
      value: summary.active_debtors,
      icon: User,
      color: 'bg-green-500',
      percent: ((summary.active_debtors / summary.total_debtors) * 100).toFixed(0),
    },
    {
      label: 'Blocked Debtors',
      value: summary.blocked_debtors,
      icon: Lock,
      color: 'bg-red-500',
      percent: ((summary.blocked_debtors / summary.total_debtors) * 100).toFixed(0),
    },
    {
      label: 'Total Receivable',
      value: `$${summary.total_receivable?.toLocaleString('en-US', { maximumFractionDigits: 0 })}`,
      icon: DollarSign,
      color: 'bg-purple-500',
      trend: null,
    },
    {
      label: 'Avg DSO',
      value: `${summary.average_dso?.toFixed(1)} days`,
      icon: TrendingUp,
      color: 'bg-orange-500',
      trend: null,
    },
    {
      label: 'Critical (120+)',
      value: `$${summary.critical_aging?.toLocaleString('en-US', { maximumFractionDigits: 0 })}`,
      icon: AlertCircle,
      color: 'bg-red-600',
      trend: null,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-3">
      {stats.map((stat, idx) => {
        const Icon = stat.icon;
        return (
          <Card key={idx} className="p-4 border-l-4" style={{ borderLeftColor: `var(--color-${stat.color.split('-')[1]})` }}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600 font-medium uppercase">{stat.label}</p>
                <p className="text-xl font-bold mt-1">{stat.value}</p>
                {stat.percent && <p className="text-xs text-gray-500 mt-1">{stat.percent}%</p>}
              </div>
              <div className={`${stat.color} p-2 rounded-lg`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
