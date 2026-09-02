'use client';

import { Card } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import type { DebtorsSummary } from '@/lib/types/debtors';

interface AgeAnalysisChartProps {
  summary: DebtorsSummary;
}

export default function AgeAnalysisChart({ summary }: AgeAnalysisChartProps) {
  const totalReceivable = summary.total_receivable || 0;
  const pct = (amount: number) => (totalReceivable > 0 ? (amount / totalReceivable) * 100 : 0);

  const data = [
    {
      name: 'Current',
      amount: summary.aging_summary?.current || 0,
      percentage: pct(summary.aging_summary?.current || 0),
    },
    {
      name: '0-30 Days',
      amount: summary.aging_summary?.days_30 || 0,
      percentage: pct(summary.aging_summary?.days_30 || 0),
    },
    {
      name: '30-60 Days',
      amount: summary.aging_summary?.days_60 || 0,
      percentage: pct(summary.aging_summary?.days_60 || 0),
    },
    {
      name: '60-90 Days',
      amount: summary.aging_summary?.days_90 || 0,
      percentage: pct(summary.aging_summary?.days_90 || 0),
    },
    {
      name: '120+ Days',
      amount: summary.aging_summary?.days_120_plus || 0,
      percentage: pct(summary.aging_summary?.days_120_plus || 0),
    },
  ];

  const COLORS = ['#22c55e', '#84cc16', '#f59e0b', '#ef4444', '#dc2626'];

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h2 className="text-xl font-bold">Aging Analysis</h2>
        <p className="text-sm text-gray-600 mt-1">Receivables breakdown by age</p>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip
            formatter={(value: any) => {
              if (typeof value === 'number') {
                return `$${value.toLocaleString()}`;
              }
              return value;
            }}
          />
          <Bar dataKey="amount" fill="#3b82f6" radius={[8, 8, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-6 grid grid-cols-5 gap-2 text-xs">
        {data.map((item, idx) => (
          <div key={idx} className="text-center">
            <div className="w-3 h-3 mx-auto mb-1 rounded" style={{ backgroundColor: COLORS[idx] }} />
            <div className="font-semibold">${(item.amount / 1000).toFixed(1)}K</div>
            <div className="text-gray-600">{item.percentage.toFixed(0)}%</div>
          </div>
        ))}
      </div>
    </Card>
  );
}
