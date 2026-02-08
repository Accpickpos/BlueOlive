'use client';

import { useQuery } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader } from 'lucide-react';
import { PieChart, Pie, Cell, Legend, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

export default function CreditUtilizationPage() {
  const { data: accounts, isLoading } = useQuery({
    queryKey: ['debtors-credit-utilization'],
    queryFn: () => debtorsApi.accounts.list({ page_size: 500 }),
    staleTime: 5 * 60 * 1000,
  });

  const utilData = accounts?.results
    ?.map((a) => {
      const used = a.total_balance || 0;
      const limit = a.dclimit || 0;
      const available = Math.max(0, limit - used);
      return {
        name: a.dno || 'Unknown',
        used,
        available,
        limit,
        percentage: limit ? (used / limit) * 100 : 0,
      };
    })
    .filter((x) => x.limit > 0)
    .sort((a, b) => b.percentage - a.percentage) || [];

  const summary = {
    totalLimit: utilData.reduce((sum, x) => sum + x.limit, 0),
    totalUsed: utilData.reduce((sum, x) => sum + x.used, 0),
    totalAvailable: utilData.reduce((sum, x) => sum + x.available, 0),
  };

  const summaryPercent = summary.totalLimit ? (summary.totalUsed / summary.totalLimit) * 100 : 0;

  const utilizationBuckets = [
    0,
    20,
    40,
    60,
    80,
    100,
  ];

  const bucketData = Array.from({ length: utilizationBuckets.length - 1 }).map((_, idx) => {
    const min = utilizationBuckets[idx];
    const max = utilizationBuckets[idx + 1];
    const count = utilData.filter((x) => x.percentage >= min && x.percentage < max).length;
    return {
      name: `${min}-${max}%`,
      count,
    };
  });

  const COLORS = ['#22c55e', '#84cc16', '#f59e0b', '#ef4444', '#991b1b'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Credit Utilization Report</h1>
        <p className="text-gray-600 mt-1">Outstanding balance vs credit limit analysis</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-96">
          <Loader className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <p className="text-xs text-gray-600 uppercase">Total Limit</p>
              <p className="text-2xl font-bold mt-2">
                ${summary.totalLimit.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </p>
            </Card>
            <Card className="p-4">
              <p className="text-xs text-gray-600 uppercase">Total Used</p>
              <p className="text-2xl font-bold text-blue-600 mt-2">
                ${summary.totalUsed.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </p>
            </Card>
            <Card className="p-4">
              <p className="text-xs text-gray-600 uppercase">Available</p>
              <p className="text-2xl font-bold text-green-600 mt-2">
                ${summary.totalAvailable.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </p>
            </Card>
            <Card className="p-4">
              <p className="text-xs text-gray-600 uppercase">Utilization</p>
              <p className="text-2xl font-bold text-orange-600 mt-2">{summaryPercent.toFixed(1)}%</p>
            </Card>
          </div>

          {/* Utilization Pie */}
          <Card className="p-6">
            <h2 className="text-lg font-bold mb-4">Overall Credit Utilization</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Used', value: summary.totalUsed },
                    { name: 'Available', value: summary.totalAvailable },
                  ]}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  <Cell fill="#3b82f6" />
                  <Cell fill="#10b981" />
                </Pie>
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>

          {/* Distribution */}
          <Card className="p-6">
            <h2 className="text-lg font-bold mb-4">Accounts by Utilization %</h2>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={bucketData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Top Utilizers */}
          {utilData.length > 0 && (
            <Card className="p-6">
              <h2 className="text-lg font-bold mb-4">Top 10 Credit Utilizers</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold">Account</th>
                      <th className="px-4 py-3 text-right font-semibold">Credit Limit</th>
                      <th className="px-4 py-3 text-right font-semibold">Used</th>
                      <th className="px-4 py-3 text-right font-semibold">Available</th>
                      <th className="px-4 py-3 text-right font-semibold">% Used</th>
                    </tr>
                  </thead>
                  <tbody>
                    {utilData
                      .slice(0, 10)
                      .map((row) => (
                        <tr key={row.name} className="border-b">
                          <td className="px-4 py-3 font-medium">{row.name}</td>
                          <td className="px-4 py-3 text-right">${row.limit.toLocaleString()}</td>
                          <td className="px-4 py-3 text-right font-bold text-blue-600">
                            ${row.used.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                          </td>
                          <td className="px-4 py-3 text-right">${row.available.toLocaleString('en-US', { maximumFractionDigits: 0 })}</td>
                          <td className={`px-4 py-3 text-right font-bold ${row.percentage > 80 ? 'text-red-600' : row.percentage > 60 ? 'text-orange-600' : 'text-green-600'}`}>
                            {row.percentage.toFixed(1)}%
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Export Options */}
          <div className="flex gap-2">
            <Button className="bg-blue-600 hover:bg-blue-700">Export to Excel</Button>
            <Button className="bg-green-600 hover:bg-green-700">Export to PDF</Button>
          </div>
        </div>
      )}
    </div>
  );
}
