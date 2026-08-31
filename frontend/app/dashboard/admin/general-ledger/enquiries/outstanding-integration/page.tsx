'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { glIntegrationApi } from '@/lib/general-ledger';
import { IntegrationSource } from '@/lib/types/generalLedger';
import { getApiErrorMessage } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Loader2, PlayCircle } from 'lucide-react';
import Link from 'next/link';

const SOURCES: { key: IntegrationSource; label: string }[] = [
  { key: 'all', label: 'All Sources' },
  { key: 'debtors', label: 'Debtors' },
  { key: 'creditors', label: 'Creditors' },
  { key: 'stock_control', label: 'Stock Control' },
  { key: 'cash_book', label: 'Cash Book' },
];

export default function OutstandingIntegrationPage() {
  const queryClient = useQueryClient();
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [lastResult, setLastResult] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['gl-integration-outstanding'],
    queryFn: () => glIntegrationApi.outstanding(),
  });

  const transferMutation = useMutation({
    mutationFn: (source: IntegrationSource) =>
      glIntegrationApi.transfer({
        source,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['gl-integration-outstanding'] });
      setLastResult(JSON.stringify(result.results, null, 2));
    },
    onError: (err) => window.alert(getApiErrorMessage(err, 'Integration transfer failed')),
  });

  const outstanding = data?.outstanding;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/general-ledger/enquiries">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Outstanding Integration</h1>
          <p className="text-gray-600 mt-1">
            Posted Debtors/Creditors/Stock/Cash Book records not yet transferred into GL
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      ) : outstanding ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="p-6">
            <p className="text-xs text-gray-600 uppercase">Debtors</p>
            <p className="text-3xl font-bold mt-2">{outstanding.debtors}</p>
          </Card>
          <Card className="p-6">
            <p className="text-xs text-gray-600 uppercase">Creditors</p>
            <p className="text-sm mt-2 space-y-1">
              {Object.entries(outstanding.creditors).map(([model, count]) => (
                <div key={model} className="flex justify-between">
                  <span className="text-gray-500">{model}</span>
                  <span className="font-bold">{count as number}</span>
                </div>
              ))}
            </p>
          </Card>
          <Card className="p-6">
            <p className="text-xs text-gray-600 uppercase">Stock Control</p>
            <p className="text-3xl font-bold mt-2">{outstanding.stock_control}</p>
          </Card>
          <Card className="p-6">
            <p className="text-xs text-gray-600 uppercase">Cash Book</p>
            <p className="text-3xl font-bold mt-2">{outstanding.cash_book}</p>
          </Card>
        </div>
      ) : null}

      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">Run Integration Transfer</h2>
        <div className="grid grid-cols-2 gap-4 max-w-md mb-4">
          <div>
            <label className="text-sm font-medium">Date From</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Date To</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {SOURCES.map((s) => (
            <Button
              key={s.key}
              variant="outline"
              onClick={() => {
                if (window.confirm(`Transfer ${s.label} transactions into GL?`)) {
                  transferMutation.mutate(s.key);
                }
              }}
              disabled={transferMutation.isPending}
            >
              {transferMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <PlayCircle className="w-4 h-4 mr-2" />
              )}
              {s.label}
            </Button>
          ))}
        </div>
        {lastResult && (
          <pre className="mt-4 bg-gray-50 border rounded p-3 text-xs overflow-x-auto">{lastResult}</pre>
        )}
      </Card>
    </div>
  );
}
