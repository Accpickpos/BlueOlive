'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { glReportsApi } from '@/lib/general-ledger';
import { FinancialReportLine } from '@/lib/types/generalLedger';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ArrowLeft, Loader2 } from 'lucide-react';
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
          <h2 className="text-lg font-bold mb-4">
            Period {data.as_of_period} — {data.currentyr}
          </h2>
          <div className="space-y-1">
            {data.lines.map((line) => (
              <div key={line.line} className={`flex justify-between py-1 ${rowClass(line)}`}>
                <span>{line.name}</span>
                <span>{line.amount.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</span>
              </div>
            ))}
          </div>
        </Card>
      ) : null}
    </div>
  );
}
