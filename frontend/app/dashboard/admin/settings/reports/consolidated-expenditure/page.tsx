'use client';

import { useState } from 'react';
import { settingsReportsApi, ConsolidatedExpenditureReport } from '@/lib/settings/reports';
import { getApiErrorMessage } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Loader2, Printer } from 'lucide-react';
import Link from 'next/link';

function formatCurrency(value: string | number) {
  return new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' }).format(Number(value));
}

const now = new Date();
const defaultPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;

export default function ConsolidatedExpenditurePage() {
  const [period, setPeriod] = useState(defaultPeriod);
  const [ytd, setYtd] = useState(false);
  const [report, setReport] = useState<ConsolidatedExpenditureReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    setLoading(true);
    setError(null);
    try {
      const data = await settingsReportsApi.consolidatedExpenditure(period, ytd);
      setReport(data);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to generate report'));
    } finally {
      setLoading(false);
    }
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
          <h1 className="text-3xl font-bold">Consolidated Expenditure</h1>
          <p className="text-gray-600 mt-1">Creditors Expense + Cash Book Expense, combined by category</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">Period</label>
            <input
              type="month"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="border rounded p-2"
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={ytd} onChange={(e) => setYtd(e.target.checked)} />
            Year-to-Date
          </label>
          <Button onClick={generate} disabled={loading}>
            {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            Generate Report
          </Button>
          {report && (
            <Button variant="outline" onClick={() => window.print()}>
              <Printer className="w-4 h-4 mr-2" />
              Print
            </Button>
          )}
        </div>
      </Card>

      {error && (
        <div className="rounded p-3 text-sm border bg-red-50 border-red-200 text-red-800">{error}</div>
      )}

      {report && (
        <Card className="p-6">
          <h2 className="text-lg font-bold mb-1">
            {report.ytd ? `Year-to-Date through ${report.end_date}` : `${report.start_date} to ${report.end_date}`}
          </h2>
          {report.rows.length === 0 ? (
            <p className="text-sm text-gray-500 mt-4">No expenditure recorded for this period.</p>
          ) : (
            <table className="w-full text-sm mt-4">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-2">Category</th>
                  <th className="py-2 text-right">Creditors</th>
                  <th className="py-2 text-right">Cash Book</th>
                  <th className="py-2 text-right">Total</th>
                </tr>
              </thead>
              <tbody>
                {report.rows.map((row) => (
                  <tr key={row.category_id} className="border-b">
                    <td className="py-2">{row.category_name}</td>
                    <td className="py-2 text-right">{formatCurrency(row.creditor_amount)}</td>
                    <td className="py-2 text-right">{formatCurrency(row.cash_book_amount)}</td>
                    <td className="py-2 text-right font-medium">{formatCurrency(row.total)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="font-bold border-t-2">
                  <td className="py-2">Grand Total</td>
                  <td></td>
                  <td></td>
                  <td className="py-2 text-right">{formatCurrency(report.grand_total)}</td>
                </tr>
              </tfoot>
            </table>
          )}
        </Card>
      )}
    </div>
  );
}
