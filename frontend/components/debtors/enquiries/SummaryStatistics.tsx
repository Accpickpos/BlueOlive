'use client';

import { Card } from '@/components/ui/card';
import type { DebtorsSummary } from '@/lib/types/debtors';

interface SummaryStatisticsProps {
  summary: DebtorsSummary;
}

export default function SummaryStatistics({ summary }: SummaryStatisticsProps) {
  const stats = [
    {
      label: 'Total Debtors',
      value: summary.total_debtors.toLocaleString(),
      subtext: summary.active_debtors + ' active',
      color: 'bg-blue-500',
    },
    {
      label: 'Total Receivable',
      value: `$${summary.total_receivable?.toLocaleString('en-US', { maximumFractionDigits: 0 })}`,
      subtext: 'across all accounts',
      color: 'bg-green-500',
    },
    {
      label: 'Avg Days Sales Outstanding',
      value: `${summary.average_dso?.toFixed(1)}`,
      subtext: 'days',
      color: 'bg-orange-500',
    },
    {
      label: 'Critical Ballances (120+)',
      value: `$${summary.critical_aging?.toLocaleString('en-US', { maximumFractionDigits: 0 })}`,
      subtext: 'over 120 days old',
      color: 'bg-red-500',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, idx) => (
        <Card key={idx} className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-gray-600 font-medium uppercase">{stat.label}</p>
              <p className="text-2xl font-bold mt-2">{stat.value}</p>
              <p className="text-xs text-gray-500 mt-1">{stat.subtext}</p>
            </div>
            <div className={`${stat.color} p-3 rounded-lg`} />
          </div>
        </Card>
      ))}
    </div>
  );
}
