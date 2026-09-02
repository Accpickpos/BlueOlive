'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { glReportsApi } from '@/lib/general-ledger';
import { FinancialReportLine } from '@/lib/types/generalLedger';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Download, Loader2 } from 'lucide-react';
import Link from 'next/link';

const rowClass = (line: FinancialReportLine) => {
  if (line.fieldtype === 'H') return 'font-bold text-gray-500 uppercase text-xs pt-4';
  if (line.fieldtype === 'T') return 'font-bold border-t-2 border-gray-800';
  if (line.fieldtype === 'S') return 'font-semibold border-t border-gray-300';
  return '';
};

export default function BalanceSheetReportPage() {
  const [asOfPeriod, setAsOfPeriod] = useState<string>('');

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['gl-balance-sheet', asOfPeriod],
    queryFn: () => glReportsApi.balanceSheet(asOfPeriod ? parseInt(asOfPeriod) : undefined),
  });

  const handleExportCsv = () => {
    if (!data) return;
    const rows = [
      ['Line', 'Type', 'Name', 'Amount'],
      ...data.lines.map((line) => [line.line, line.fieldtype, line.name, line.amount ?? '']),
    ];
    const csvContent = rows.map((row) => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `balance-sheet-period${data.as_of_period}.csv`;
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
          <h1 className="text-3xl font-bold">Balance Sheet</h1>
          <p className="text-gray-600 mt-1">Assets, liabilities, and equity as of a chosen period</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-end gap-4">
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
          No Report Format rows are defined for the Balance Sheet yet. Set them up under
          Maintenance → Report Formats first.
        </div>
      ) : data ? (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold">
              Period {data.as_of_period} — {data.currentyr}
            </h2>
            <div className="flex items-center gap-3">
              <Badge variant={data.is_balanced ? 'default' : 'destructive'}>
                {data.is_balanced ? 'Balanced' : 'Out of Balance'}
              </Badge>
              <Button variant="outline" size="sm" onClick={handleExportCsv}>
                <Download className="w-4 h-4 mr-2" />
                Export CSV
              </Button>
            </div>
          </div>
          <div className="space-y-1">
            {data.lines.map((line) => (
              <div key={line.line} className={`flex justify-between py-1 ${rowClass(line)}`}>
                <span>{line.name}</span>
                <span>{(line.amount ?? 0).toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</span>
              </div>
            ))}
          </div>
          {!data.is_balanced && (
            <div className="mt-4 pt-4 border-t text-sm text-amber-800 bg-amber-50 rounded-lg p-3">
              Assets ({data.total_assets.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}) does not equal
              Liabilities + Equity + Net Income ({data.total_liabilities_and_equity.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}
              {' + '}
              {data.net_income.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}). Check for unbalanced batches or
              unposted transactions for this period.
            </div>
          )}
        </Card>
      ) : null}
    </div>
  );
}
