'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader, ArrowLeft, Clock } from 'lucide-react';
import Link from 'next/link';

export default function HourlyAnalysisPage() {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const { data: rows, isLoading } = useQuery({
    queryKey: ['hourly-analysis', dateFrom, dateTo],
    queryFn: () =>
      stockControlApi.enquiries.hourlyAnalysis({
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      }),
    staleTime: 30 * 1000,
  });

  const byHour = new Map((rows || []).map((r) => [r.hour, r]));
  const maxValue = Math.max(1, ...(rows || []).map((r) => Number(r.total_value || 0)));

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/stock-control/enquiries">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Hourly Analysis</h1>
          <p className="text-gray-600 mt-1">Sales activity by hour of day</p>
        </div>
      </div>

      <Card className="p-4">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">From</label>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">To</label>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="px-3 py-2 border rounded-lg" />
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Clock className="w-5 h-5 mr-2" />
          Sales by Hour
        </h2>
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : !rows || rows.length === 0 ? (
          <p className="text-gray-500 text-center py-12">No sales in this period (transaction time wasn't recorded)</p>
        ) : (
          <div className="space-y-2">
            {Array.from({ length: 24 }, (_, hour) => hour).map((hour) => {
              const row = byHour.get(hour);
              const value = Number(row?.total_value || 0);
              return (
                <div key={hour} className="flex items-center gap-3">
                  <span className="w-14 text-sm text-gray-600 font-mono">{hour.toString().padStart(2, '0')}:00</span>
                  <div className="flex-1 h-6 bg-gray-100 rounded overflow-hidden">
                    <div
                      className="h-full bg-blue-600"
                      style={{ width: `${(value / maxValue) * 100}%` }}
                    />
                  </div>
                  <span className="w-24 text-sm text-right">R {value.toFixed(2)}</span>
                  <span className="w-20 text-xs text-gray-500 text-right">{row?.transaction_count || 0} txns</span>
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
}
