'use client';

import { useState } from 'react';
import { settingsReportsApi, TaxControlReport } from '@/lib/settings/reports';
import { getApiErrorMessage } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Loader2, Printer, Info } from 'lucide-react';
import Link from 'next/link';

function formatCurrency(value: string | number) {
  return new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' }).format(Number(value));
}

const now = new Date();
const firstOfMonth = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10);
const today = now.toISOString().slice(0, 10);

export default function TaxControlReportPage() {
  const [startDate, setStartDate] = useState(firstOfMonth);
  const [endDate, setEndDate] = useState(today);
  const [report, setReport] = useState<TaxControlReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    setLoading(true);
    setError(null);
    try {
      const data = await settingsReportsApi.taxControlReport(startDate, endDate);
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
          <h1 className="text-3xl font-bold">Tax Control / VAT-201</h1>
          <p className="text-gray-600 mt-1">VAT reconciled across Debtors, Creditors, Cash Book and POS</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">Start Date</label>
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="border rounded p-2" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">End Date</label>
            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="border rounded p-2" />
          </div>
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
        <>
          <div className="rounded p-3 text-xs border bg-amber-50 border-amber-200 text-amber-800 flex items-start gap-2">
            <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
            {report.assumptions}
          </div>

          <Card className="p-6">
            <h2 className="text-lg font-bold mb-4">Category Breakdown</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-2">Category</th>
                  <th className="py-2 text-right">Amount</th>
                </tr>
              </thead>
              <tbody>
                {report.categories.map((c) => (
                  <tr key={c.label} className="border-b">
                    <td className="py-2">{c.label}</td>
                    <td className="py-2 text-right">{formatCurrency(c.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          <Card className="p-6">
            <h2 className="text-lg font-bold mb-4">Totals</h2>
            <dl className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <dt className="text-gray-600">Output VAT</dt>
                <dd className="font-bold text-lg">{formatCurrency(report.totals.output_vat)}</dd>
              </div>
              <div>
                <dt className="text-gray-600">Input VAT</dt>
                <dd className="font-bold text-lg">{formatCurrency(report.totals.input_vat)}</dd>
              </div>
              <div>
                <dt className="text-gray-600">Net VAT Payable</dt>
                <dd className="font-bold text-lg">{formatCurrency(report.totals.net_vat_payable)}</dd>
              </div>
            </dl>
          </Card>

          <Card className="p-6">
            <h2 className="text-lg font-bold mb-2">Reconcile Against Each Module's Own Report</h2>
            <p className="text-sm text-gray-600 mb-4">
              Compare these totals against each module's own Transaction Report before submitting VAT-201.
            </p>
            <dl className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <dt className="text-gray-600">Debtors — Output VAT</dt>
                <dd className="font-medium">{formatCurrency(report.reconciliation.debtors_module_output_vat)}</dd>
              </div>
              <div>
                <dt className="text-gray-600">Creditors — Input VAT</dt>
                <dd className="font-medium">{formatCurrency(report.reconciliation.creditors_module_input_vat)}</dd>
              </div>
              <div>
                <dt className="text-gray-600">Cash Book — Input VAT</dt>
                <dd className="font-medium">{formatCurrency(report.reconciliation.cash_book_module_input_vat)}</dd>
              </div>
              <div>
                <dt className="text-gray-600">Cash Book — Output VAT</dt>
                <dd className="font-medium">{formatCurrency(report.reconciliation.cash_book_module_output_vat)}</dd>
              </div>
            </dl>
          </Card>
        </>
      )}
    </div>
  );
}
