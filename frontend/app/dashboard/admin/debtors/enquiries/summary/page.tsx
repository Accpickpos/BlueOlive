'use client';

import { useQuery } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Card } from '@/components/ui/card';
import { Loader, AlertCircle } from 'lucide-react';
import SummaryStatistics from '@/components/debtors/enquiries/SummaryStatistics';
import AgingChart from '@/components/debtors/enquiries/AgingChart';

export default function SummaryEnquiryPage() {
  const { data: summary, isLoading, error } = useQuery({
    queryKey: ['debtors-summary-enquiry'],
    queryFn: () => debtorsApi.summary.get(),
    staleTime: 5 * 60 * 1000,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Debtors Summary</h1>
        <p className="text-gray-600 mt-1">Overall receivables aging and analysis</p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-800">Failed to load summary data</div>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center h-96">
          <Loader className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : summary ? (
        <div className="space-y-6">
          {/* Key Statistics */}
          <SummaryStatistics summary={summary} />

          {/* Aging Chart */}
          <AgingChart summary={summary} />

          {/* Top Debtors */}
          {summary.top_debtors && summary.top_debtors.length > 0 && (
            <Card className="p-6">
              <h2 className="text-lg font-bold mb-4">Top Debtors by Balance</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold">Account</th>
                      <th className="px-4 py-3 text-left font-semibold">Name</th>
                      <th className="px-4 py-3 text-right font-semibold">Balance</th>
                      <th className="px-4 py-3 text-right font-semibold">Credit Limit</th>
                      <th className="px-4 py-3 text-right font-semibold">DSO</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.top_debtors.map((debtor, idx) => (
                      <tr key={idx} className="border-b">
                        <td className="px-4 py-3 font-medium">{debtor.dno}</td>
                        <td className="px-4 py-3">{debtor.dname}</td>
                        <td className="px-4 py-3 text-right font-bold text-blue-600">
                          ${debtor.total_balance?.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                        </td>
                        <td className="px-4 py-3 text-right">${debtor.dclimit?.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right">{debtor.days_sales_outstanding?.toFixed(0)} days</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      ) : null}
    </div>
  );
}
