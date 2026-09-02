'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { glReportsApi } from '@/lib/general-ledger';
import { FinancialReportLine, IncomeStatementMode } from '@/lib/types/generalLedger';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { ArrowLeft, Download, Loader2 } from 'lucide-react';
import Link from 'next/link';

const rowClass = (line: FinancialReportLine) => {
  if (line.fieldtype === 'H') return 'font-bold text-gray-500 uppercase text-xs pt-4';
  if (line.fieldtype === 'T') return 'font-bold border-t-2 border-gray-800';
  if (line.fieldtype === 'S') return 'font-semibold border-t border-gray-300';
  return '';
};

// Mirrors settings.OPTIONAL modes in backend reports.py INCOME_STATEMENT_MODES.
const MODE_OPTIONS: { value: IncomeStatementMode; label: string }[] = [
  { value: 'current', label: 'Current Period' },
  { value: 'current_ytd', label: 'Current Period + Year to Date' },
  { value: 'current_last_year', label: 'Current Period + Last Year' },
  { value: 'current_budget', label: 'Current Period + Budget' },
  { value: 'budget_12', label: 'Budgeted Values — 12 Months' },
  { value: 'variance', label: 'Budget Variance' },
  { value: 'actual_12', label: 'Actual Values — 12 Months' },
];

// Column keys to show, in order, for each non-"current" mode - everything
// else on a line is metadata (line/fieldtype/name/printdet).
const MODE_COLUMNS: Record<IncomeStatementMode, { key: string; label: string }[]> = {
  current: [{ key: 'amount', label: 'Amount' }],
  current_ytd: [
    { key: 'current', label: 'Current' },
    { key: 'ytd', label: 'Year to Date' },
  ],
  current_last_year: [
    { key: 'current', label: 'Current' },
    { key: 'last_year', label: 'Last Year' },
    { key: 'ytd', label: 'YTD' },
    { key: 'last_year_ytd', label: 'Last Year YTD' },
  ],
  current_budget: [
    { key: 'current', label: 'Current' },
    { key: 'budget', label: 'Budget' },
    { key: 'ytd', label: 'YTD' },
    { key: 'ytd_budget', label: 'YTD Budget' },
  ],
  budget_12: Array.from({ length: 12 }, (_, i) => ({ key: `month${i + 1}`, label: `M${i + 1}` })),
  variance: [
    { key: 'current_variance', label: 'Current Variance' },
    { key: 'ytd_variance', label: 'YTD Variance' },
  ],
  actual_12: Array.from({ length: 12 }, (_, i) => ({ key: `month${i + 1}`, label: `M${i + 1}` })),
};

const fmt = (value: number | string | undefined) =>
  typeof value === 'number' ? value.toLocaleString('en-ZA', { minimumFractionDigits: 2 }) : '';

export default function IncomeStatementReportPage() {
  const [asOfPeriod, setAsOfPeriod] = useState<string>('');
  const [mode, setMode] = useState<IncomeStatementMode>('current');

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['gl-income-statement', asOfPeriod, mode],
    queryFn: () => glReportsApi.incomeStatement(asOfPeriod ? parseInt(asOfPeriod) : undefined, mode),
  });

  const columns = MODE_COLUMNS[mode];

  const handleExportCsv = () => {
    if (!data) return;
    const rows = [
      ['Line', 'Type', 'Name', ...columns.map((c) => c.label)],
      ...data.lines.map((line) => [line.line, line.fieldtype, line.name, ...columns.map((c) => line[c.key] ?? '')]),
    ];
    const csvContent = rows.map((row) => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `income-statement-${mode}-period${data.as_of_period}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/general-ledger/reports">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Income Statement</h1>
          <p className="text-gray-600 mt-1">Revenue and expense performance for the period</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-end gap-4 flex-wrap">
          <div>
            <label className="text-sm font-medium">As of Period (1-13)</label>
            <Input
              type="number"
              min={1}
              max={13}
              placeholder="Current period"
              value={asOfPeriod}
              onChange={(e) => setAsOfPeriod(e.target.value)}
              className="w-40"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Layout</label>
            <Select value={mode} onValueChange={(v) => setMode(v as IncomeStatementMode)}>
              <SelectTrigger className="w-64">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MODE_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={() => refetch()} disabled={isFetching}>
            {isFetching ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            Generate
          </Button>
        </div>
      </Card>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      ) : data && !data.is_seeded ? (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-amber-800 text-sm">
          No Report Format rows are defined for the Income Statement yet. Set them up under
          Maintenance → Report Formats first.
        </div>
      ) : data ? (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold">
              Period {data.as_of_period} — {data.currentyr}
            </h2>
            <Button variant="outline" size="sm" onClick={handleExportCsv}>
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
          </div>
          <div className="overflow-x-auto">
            <div className="min-w-fit space-y-1">
              <div className="flex gap-6 py-1 text-xs font-medium text-gray-500 uppercase">
                <span className="flex-1">Account</span>
                {columns.map((col) => (
                  <span key={col.key} className="w-32 text-right">{col.label}</span>
                ))}
              </div>
              {data.lines.map((line) => (
                <div key={line.line} className={`flex gap-6 py-1 ${rowClass(line)}`}>
                  <span className="flex-1">{line.name}</span>
                  {columns.map((col) => (
                    <span key={col.key} className="w-32 text-right">{fmt(line[col.key])}</span>
                  ))}
                </div>
              ))}
            </div>
          </div>
          {data.net_result !== null && (
            <div className="flex justify-between mt-4 pt-4 border-t-2 border-gray-800 font-bold text-lg">
              <span>Net Result</span>
              <span>{data.net_result.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</span>
            </div>
          )}
        </Card>
      ) : null}
    </div>
  );
}
