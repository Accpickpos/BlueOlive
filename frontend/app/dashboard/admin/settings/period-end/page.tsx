'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { periodEndApi, isAsyncTaskResult, DayEndReport } from '@/lib/settings/periodEnd';
import { getApiErrorMessage } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Loader2, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';
import Link from 'next/link';

export default function PeriodEndPage() {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [expandedReportId, setExpandedReportId] = useState<number | null>(null);

  const { data: status, refetch: refetchStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['settings-period-end-status'],
    queryFn: () => periodEndApi.status(),
  });

  const { data: reports, refetch: refetchReports } = useQuery({
    queryKey: ['settings-day-end-reports'],
    queryFn: () => periodEndApi.listDayEndReports(),
  });

  function handleResult(result: Awaited<ReturnType<typeof periodEndApi.runDayEnd>>, label: string) {
    if (isAsyncTaskResult(result)) {
      setMessage({ type: 'success', text: `${label} started in the background (task ${result.task_id}).` });
      return;
    }
    refetchStatus();
    refetchReports();
    queryClient.invalidateQueries({ queryKey: ['settings-day-end-reports'] });
    setMessage({
      type: result.success ? 'success' : 'error',
      text: result.success ? `${label} complete — ${result.message}` : `${label} failed — ${result.message || result.errors.join(', ')}`,
    });
  }

  const dayEndMutation = useMutation({
    mutationFn: () => periodEndApi.runDayEnd(),
    onSuccess: (result) => handleResult(result, 'Day End'),
    onError: (err) => setMessage({ type: 'error', text: getApiErrorMessage(err, 'Day End failed') }),
  });

  const monthEndMutation = useMutation({
    mutationFn: () => periodEndApi.runMonthEnd(),
    onSuccess: (result) => handleResult(result, 'Month End'),
    onError: (err) => setMessage({ type: 'error', text: getApiErrorMessage(err, 'Month End failed') }),
  });

  const yearEndMutation = useMutation({
    mutationFn: () => periodEndApi.runYearEnd(),
    onSuccess: (result) => handleResult(result, 'Year End'),
    onError: (err) => setMessage({ type: 'error', text: getApiErrorMessage(err, 'Year End failed') }),
  });

  if (statusLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/settings">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Day End / Month End / Year End</h1>
          <p className="text-gray-600 mt-1">Run period-end processing and reprint past Day End reports</p>
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

      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">Status</h2>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-gray-600">Current Period / Year</dt>
            <dd className="font-medium">
              {status?.current_period.period} / {status?.current_period.year}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">Last Day End</dt>
            <dd className="font-medium">{status?.last_day_end_date ?? 'Never run'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">Last Month End</dt>
            <dd className="font-medium">{status?.last_month_end_date ?? 'Never run'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">Last Year End</dt>
            <dd className="font-medium">{status?.last_year_end_date ?? 'Never run'}</dd>
          </div>
        </dl>

        {status?.scheduling && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-gray-600">
            <div className="border rounded p-2">
              <div className="font-semibold text-gray-800">Auto Day End</div>
              {status.scheduling.day_end.enabled
                ? `Enabled — ${status.scheduling.day_end.time ?? ''} ${status.scheduling.day_end.days_of_week ?? ''}`
                : 'Disabled'}
            </div>
            <div className="border rounded p-2">
              <div className="font-semibold text-gray-800">Auto Month End</div>
              {status.scheduling.month_end.enabled
                ? `Enabled — day ${status.scheduling.month_end.day ?? ''} ${status.scheduling.month_end.time ?? ''}`
                : 'Disabled'}
            </div>
            <div className="border rounded p-2">
              <div className="font-semibold text-gray-800">Auto Year End</div>
              {status.scheduling.year_end.enabled
                ? `Enabled — month ${status.scheduling.year_end.month ?? ''} day ${status.scheduling.year_end.day ?? ''}`
                : 'Disabled'}
            </div>
          </div>
        )}
      </Card>

      <Card className="p-6 border-l-4 border-l-amber-500">
        <h2 className="text-lg font-bold mb-2">Run Period End</h2>
        <p className="text-sm text-gray-600 mb-4 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-600" />
          These operations post ageing, statistics, and financial period changes. Confirm before running.
        </p>
        <div className="flex flex-wrap gap-3">
          <Button
            variant="outline"
            onClick={() => {
              if (window.confirm('Run Day End for yesterday? This applies due Future Pricing and generates sales/cashbook/stock summaries.')) {
                dayEndMutation.mutate();
              }
            }}
            disabled={dayEndMutation.isPending}
          >
            {dayEndMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            Run Day End
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              if (window.confirm('Run Month End? This ages debtor balances, generates department/sales-area monthly stats, and advances the accounting period.')) {
                monthEndMutation.mutate();
              }
            }}
            disabled={monthEndMutation.isPending}
          >
            {monthEndMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            Run Month End
          </Button>
          <Button
            variant="destructive"
            onClick={() => {
              if (window.confirm('Run Year End? This closes the financial year, generates YTD summaries, and advances the financial year. This cannot be undone.')) {
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

      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">Day End Report History</h2>
        {!reports || reports.length === 0 ? (
          <p className="text-sm text-gray-500">No Day End reports recorded yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2">Date</th>
                <th className="py-2">Shop</th>
                <th className="py-2">Status</th>
                <th className="py-2">Message</th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody>
              {reports.map((r: DayEndReport) => (
                <ReportRow
                  key={r.id}
                  report={r}
                  expanded={expandedReportId === r.id}
                  onToggle={() => setExpandedReportId(expandedReportId === r.id ? null : r.id)}
                />
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}

function ReportRow({
  report,
  expanded,
  onToggle,
}: {
  report: DayEndReport;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <tr className="border-b hover:bg-gray-50 cursor-pointer" onClick={onToggle}>
        <td className="py-2">{report.process_date}</td>
        <td className="py-2">{report.shop_id ?? 'All shops'}</td>
        <td className="py-2">
          <span className={report.success ? 'text-green-700' : 'text-red-700'}>
            {report.success ? 'Success' : 'Failed'}
          </span>
        </td>
        <td className="py-2 text-gray-600">{report.message}</td>
        <td className="py-2 text-right">{expanded ? <ChevronUp className="w-4 h-4 inline" /> : <ChevronDown className="w-4 h-4 inline" />}</td>
      </tr>
      {expanded && (
        <tr className="bg-gray-50">
          <td colSpan={5} className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <div className="font-semibold mb-1">Details</div>
                <pre className="bg-white border rounded p-2 overflow-x-auto">{JSON.stringify(report.details, null, 2)}</pre>
              </div>
              {report.errors?.length > 0 && (
                <div>
                  <div className="font-semibold mb-1 text-red-700">Errors</div>
                  <ul className="bg-white border rounded p-2 list-disc list-inside text-red-700">
                    {report.errors.map((e, i) => (
                      <li key={i}>{e}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
