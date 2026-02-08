'use client';

import { Card } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { DebtorsSummary } from '@/lib/types/debtors';

interface AgingChartProps {
  summary: DebtorsSummary;
}

export default function AgingChart({ summary }: AgingChartProps) {
  const data = [
    { name: 'Current', value: summary.aging_summary?.current || 0 },
    { name: '30 Days', value: summary.aging_summary?.days_30 || 0 },
    { name: '60 Days', value: summary.aging_summary?.days_60 || 0 },
    { name: '90 Days', value: summary.aging_summary?.days_90 || 0 },
    { name: '120+ Days', value: summary.aging_summary?.days_120_plus || 0 },
  ];

  const COLORS = ['#22c55e', '#84cc16', '#f59e0b', '#ef4444', '#991b1b'];

  return (
    <Card className="p-6">
      <h2 className="text-lg font-bold mb-4">Receivables by Age</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip
            formatter={(value: any) => `$${(value as number).toLocaleString()}`}
            labelFormatter={(label) => `Age: ${label}`}
          />
          <Bar dataKey="value" radius={[8, 8, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}
