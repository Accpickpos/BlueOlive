'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { glReportsApi } from '@/lib/general-ledger';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ArrowLeft, Download, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function TrialBalanceReportPage() {
  const [asOfPeriod, setAsOfPeriod] = useState<string>('');

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['gl-trial-balance', asOfPeriod],
    queryFn: () => glReportsApi.trialBalance(asOfPeriod ? parseInt(asOfPeriod) : undefined),
  });

  const handleExportCsv = () => {
    if (!data) return;
    const rows = [
      ['Account No.', 'Name', 'Debit', 'Credit'],
      ...data.accounts.map((row) => [row.accno, row.name, row.debit, row.credit]),
      ['', 'TOTAL', data.total_debit, data.total_credit],
    ];
    const csvContent = rows.map((row) => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trial-balance-period${data.as_of_period}.csv`;
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
          <h1 className="text-3xl font-bold">Trial Balance</h1>
          <p className="text-gray-600 mt-1">Every account's balance as of a chosen period</p>
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

          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Account No.</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead className="text-right">Debit</TableHead>
                  <TableHead className="text-right">Credit</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.accounts.map((row) => (
                  <TableRow key={row.accno}>
                    <TableCell className="font-medium">{row.accno}</TableCell>
                    <TableCell>{row.name}</TableCell>
                    <TableCell className="text-right">
                      {row.debit ? row.debit.toLocaleString('en-ZA', { minimumFractionDigits: 2 }) : ''}
                    </TableCell>
                    <TableCell className="text-right">
                      {row.credit ? row.credit.toLocaleString('en-ZA', { minimumFractionDigits: 2 }) : ''}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <div className="flex justify-end gap-8 mt-4 pt-4 border-t font-bold">
            <div>Total Debit: {data.total_debit.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</div>
            <div>Total Credit: {data.total_credit.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</div>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
