'use client';

import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { glParametersApi } from '@/lib/general-ledger';
import { getApiErrorMessage } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ArrowLeft, Loader2, AlertTriangle } from 'lucide-react';
import Link from 'next/link';

export default function GLParametersPage() {
  const queryClient = useQueryClient();
  const [retainedEarningsAccno, setRetainedEarningsAccno] = useState<string>('');
  const [hasEditedRetainedEarnings, setHasEditedRetainedEarnings] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const { data: param, isLoading } = useQuery({
    queryKey: ['gl-parameters'],
    queryFn: () => glParametersApi.get(),
  });

  // Sync the input from the fetched singleton once, without clobbering
  // whatever the user has typed since (TanStack Query v5 removed
  // useQuery's onSuccess callback, so this replaces that).
  useEffect(() => {
    if (param && !hasEditedRetainedEarnings) {
      setRetainedEarningsAccno(param.retained_earnings_accno ? String(param.retained_earnings_accno) : '');
    }
  }, [param, hasEditedRetainedEarnings]);

  const { data: status, refetch: refetchStatus } = useQuery({
    queryKey: ['gl-system-status'],
    queryFn: () => glParametersApi.systemStatus(),
  });

  const updateMutation = useMutation({
    mutationFn: () =>
      glParametersApi.update({
        retained_earnings_accno: retainedEarningsAccno ? parseInt(retainedEarningsAccno) : null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gl-parameters'] });
      setMessage({ type: 'success', text: 'Parameters updated.' });
    },
    onError: (err) => setMessage({ type: 'error', text: getApiErrorMessage(err, 'Failed to update parameters') }),
  });

  const periodEndMutation = useMutation({
    mutationFn: () => glParametersApi.periodEnd(),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['gl-parameters'] });
      refetchStatus();
      setMessage({ type: 'success', text: `Period End complete — moved from period ${result.previous_period} to ${result.curperiod}.` });
    },
    onError: (err) => setMessage({ type: 'error', text: getApiErrorMessage(err, 'Period End failed') }),
  });

  const yearEndMutation = useMutation({
    mutationFn: () => glParametersApi.yearEnd(),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['gl-parameters'] });
      refetchStatus();
      setMessage({
        type: 'success',
        text: `Year End complete — closed ${result.previous_year} (net income ${result.net_income.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}), now in ${result.currentyr}.`,
      });
    },
    onError: (err) => setMessage({ type: 'error', text: getApiErrorMessage(err, 'Year End failed') }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/general-ledger/maintenance">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">GL Parameters</h1>
          <p className="text-gray-600 mt-1">Current period/year and Period/Year End</p>
        </div>
      </div>

      {message && (
        <div
          className={`rounded p-3 text-sm border ${
            message.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}
        >
          {message.text}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-lg font-bold mb-4">Status</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-600">Current Period</dt>
              <dd className="font-medium">{status?.curperiod ?? param?.curperiod}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Current Year</dt>
              <dd className="font-medium">{status?.currentyr ?? param?.currentyr}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Start Period</dt>
              <dd className="font-medium">{param?.startper}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Next Batch Number</dt>
              <dd className="font-medium">{status?.next_batchno}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Outstanding Batches</dt>
              <dd className={`font-medium ${status && status.outstanding_batches > 0 ? 'text-amber-600' : ''}`}>
                {status?.outstanding_batches}
              </dd>
            </div>
          </dl>

          {status && status.outstanding_batches > 0 && (
            <div className="mt-4 flex items-start gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              Batches {status.outstanding_batchnos.join(', ')} must be posted before Period End or Year End can run.
            </div>
          )}
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-bold mb-4">Retained Earnings Account</h2>
          <p className="text-sm text-gray-600 mb-3">
            Income Statement accounts are closed against this account at Year End.
          </p>
          <div className="flex gap-2">
            <Input
              type="number"
              value={retainedEarningsAccno}
              onChange={(e) => {
                setHasEditedRetainedEarnings(true);
                setRetainedEarningsAccno(e.target.value);
              }}
              placeholder="e.g., 3000"
            />
            <Button onClick={() => updateMutation.mutate()} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save'}
            </Button>
          </div>
        </Card>
      </div>

      <Card className="p-6 border-l-4 border-l-red-500">
        <h2 className="text-lg font-bold mb-2">Period End / Year End</h2>
        <p className="text-sm text-gray-600 mb-4">
          These operations are irreversible. Ensure all batches are posted before running either.
        </p>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => {
              if (window.confirm('Advance to the next period? This cannot be undone.')) {
                periodEndMutation.mutate();
              }
            }}
            disabled={periodEndMutation.isPending}
          >
            {periodEndMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            Run Period End
          </Button>
          <Button
            variant="destructive"
            onClick={() => {
              if (
                window.confirm(
                  'Run Year End? This closes all Income Statement accounts to Retained Earnings, rolls balances forward, and advances the year. This cannot be undone.'
                )
              ) {
                yearEndMutation.mutate();
              }
            }}
            disabled={yearEndMutation.isPending}
          >
            {yearEndMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            Run Year End
          </Button>
        </div>
      </Card>
    </div>
  );
}
